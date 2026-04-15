from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from user.models import Cart,Wishlist,Address,Order,ProductRating
from public.models import Product,ProductVariant
from user.models import CheckoutSession, CheckoutItem 
from .serializers import (CartSerializer,WishlistSerializer,AddressSerializer,OrderSerializer,
ProductRatingSerializer,CheckoutSessionSerializer,CheckoutItemSerializer)
import razorpay
from django.shortcuts import get_object_or_404
from razorpay.errors import SignatureVerificationError
from utils.email import send_admin_order_email
from django.db.models import Sum
from django.db import transaction

class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        CheckoutSession.objects.filter(
            user=request.user,
            status="active"
        ).delete()

        session = CheckoutSession.objects.create(
            user=request.user,
            status="active"
        )

        return Response({
            "success": True,
            "message": "Checkout session created",
        })


class AddToCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        variant_id = request.data.get("variant_id")
        qty = int(request.data.get("qty", 1))

        session, _ = CheckoutSession.objects.get_or_create(
            user=user,
            status="active"
        )

        variant = get_object_or_404(ProductVariant, id=variant_id)

        item, created = CheckoutItem.objects.get_or_create(
            session=session,
            variant=variant,
            defaults={"qty": qty}
        )

        if not created:
            item.qty += qty
            item.save()

        return Response({
            "success": True,
            "message": "Item added to checkout session"
        })


class CheckoutSessionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        session = get_object_or_404(
            CheckoutSession,
            user=request.user,
            status="active"
        )

        serializer = CheckoutSessionSerializer(
            session,
            context={"request": request}
        )

        return Response(serializer.data)


class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        addr = data.get("address", {})


        session = get_object_or_404(
            CheckoutSession,
            user=request.user,
            status="active"
        )

        items = session.items.select_related("variant__product")
        addr = data.get("address", {})

        if not items.exists():
            return Response({"detail": "No items to checkout"}, status=400)


        grand_total = 0

        for item in items:
            variant = item.variant
            product = variant.product
            qty = item.qty

            if variant.stock_qty < qty:
                return Response(
                    {"detail": f"Only {variant.stock_qty} left for {product.title}"},
                    status=400
                )

            price = float(variant.price)
            delivery = float(product.delivery_charge or 0)

            item_total = (price * qty) + (delivery * qty)

            grand_total += item_total

        # COD
        if data.get("payment_method") == "cod":
            orders = []

            for item in items:
                variant = item.variant
                product = variant.product
                qty = item.qty

                price = float(variant.price)
                mrp = float(variant.mrp)
                delivery = float(product.delivery_charge or 0)

                order = Order.objects.create(
                    user=request.user,
                    product_name=product.title,
                    product_slug=product.slug,
                    variant=variant,
                    size=variant.size,
                    qty=qty,
                    price=price * qty,
                    mrp=mrp * qty,
                    discount=(mrp - price) * qty,
                    delivery_charge=delivery * qty,
                    total=(price * qty) + (delivery * qty),
                    payment_method="cod",
                    payment_status="initiated",

                    # ✅ FROM SESSION (SAFE)
                    name=addr.get("name", ""),
                    phone=addr.get("phone", ""),
                    alt_phone=addr.get("alt_phone", ""),
                    pincode=addr.get("pincode", ""),
                    state=addr.get("state", ""),
                    city=addr.get("city", ""),
                    location=addr.get("location", ""),
                    address_line=addr.get("address_line", ""),
                    landmark=addr.get("landmark", ""),
                )
                orders.append(order)
                variant.stock_qty -= qty
                variant.save()

            session.status = "completed"
            session.save()
            session.items.all().delete()

            Cart.objects.filter(user=request.user).delete()
            send_admin_order_email(orders)

            return Response({
                "success": True,
                "order_count": len(orders),
                "grand_total": grand_total,
            }, status=200)

        # PREPAID
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        razorpay_order = client.order.create({
            "amount": int(grand_total * 100),
            "currency": "INR",
            "payment_capture": 1,
        })

        session.total_amount = grand_total
        session.razorpay_order_id = razorpay_order["id"]
        session.save()

        return Response({
            "success": True,
            "razorpay_order_id": razorpay_order["id"],
            "amount": razorpay_order["amount"],
            "razorpay_key": settings.RAZORPAY_KEY_ID,
        })


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        addr = data.get("address", {})

        try:
            client = razorpay.Client(
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
            )

            client.utility.verify_payment_signature({
                "razorpay_order_id": data["razorpay_order_id"],
                "razorpay_payment_id": data["razorpay_payment_id"],
                "razorpay_signature": data["razorpay_signature"],
            })

            # ✅ GET SESSION FIRST
            session = get_object_or_404(
                CheckoutSession,
                razorpay_order_id=data["razorpay_order_id"],
                user=request.user,
                status="active"
            )

            payment = client.payment.fetch(data["razorpay_payment_id"])

            # ✅ VERIFY AMOUNT (CRITICAL)
            if payment["amount"] != int(session.total_amount * 100):
                return Response({"error": "Amount mismatch"}, status=400)

            payment_channel = payment.get("method")

            orders = []
            items = session.items.select_related("variant__product")

            with transaction.atomic():
                for item in items:
                    variant = item.variant
                    product = variant.product
                    qty = item.qty

                    if variant.stock_qty < qty:
                        raise ValueError(f"Stock exhausted for {product.title}")

                    price = float(variant.price)
                    mrp = float(variant.mrp)
                    delivery = float(product.delivery_charge or 0)
                    variant.stock_qty -= qty
                    variant.save()

                    order = Order.objects.create(
                        user=request.user,
                        product_name=product.title,
                        product_slug=product.slug,
                        variant=variant,
                        size=variant.size,
                        qty=qty,
                        price=price * qty,
                        mrp=mrp * qty,
                        discount=(mrp - price) * qty,
                        delivery_charge=delivery * qty,
                        total=(price * qty) + (delivery * qty),
                        payment_method="prepaid",
                        payment_status="paid",
                        razorpay_order_id=data["razorpay_order_id"],
                        razorpay_payment_id=data["razorpay_payment_id"],
                        razorpay_signature=data["razorpay_signature"],
                        payment_channel=payment_channel,

                        # ✅ SAFE ADDRESS FROM SESSION
                        name=addr.get("name", ""),
                        phone=addr.get("phone", ""),
                        alt_phone=addr.get("alt_phone", ""),
                        pincode=addr.get("pincode", ""),
                        state=addr.get("state", ""),
                        city=addr.get("city", ""),
                        location=addr.get("location", ""),
                        address_line=addr.get("address_line", ""),
                        landmark=addr.get("landmark", ""),
                    )
                    orders.append(order)

                # ✅ mark session used
                session.status = "completed"
                session.save()
                session.items.all().delete()

            Cart.objects.filter(user=request.user).delete()
            send_admin_order_email(orders)

            return Response({"success": True,"message": "Payment successful","channel": payment_channel})

        except SignatureVerificationError:
            return Response(
                {"success": False, "message": "Payment verification failed"},
                status=400
            )

        except Exception as e:
            return Response({"error": str(e)}, status=400)

class AddressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        address = Address.objects.filter(user=request.user).first()
        if not address:
            return Response({}, status=status.HTTP_200_OK)

        serializer = AddressSerializer(address)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=201)

    def put(self, request):
        address = Address.objects.filter(user=request.user).first()
        if not address:
            return Response({"detail": "Address not found"}, status=404)

        serializer = AddressSerializer(
            address, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
        })


class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        size = request.data.get("size")

        if not size:
            return Response(
                {"detail": "Size is required"},
                status=400
            )

        product = get_object_or_404(
            Product,
            slug=slug,
            is_available=True
        )

        variant = ProductVariant.objects.filter(
            product=product,
            size=size,
            is_active=True
        ).first()

        if not variant:
            return Response(
                {"detail": "Invalid or unavailable size"},
                status=400
            )

        if variant.stock_qty < 1:
            return Response(
                {"detail": "Out of stock"},
                status=400
            )

        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            variant=variant,
            defaults={"product": product}
        )

        if not created:
            if cart_item.quantity >= variant.stock_qty:
                return Response(
                    {"detail": "Stock limit reached"},
                    status=400
                )
            cart_item.quantity += 1
            cart_item.save()

        return Response(
            {"message": "Added to cart"},
            status=200
        )




class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, slug):
        size = request.data.get("size")
        if not size:
            return Response({"detail": "Size required"}, status=400)

        product = Product.objects.filter(slug=slug).first()


        if not product:
            return Response({"detail": "Product not found"}, status=404)

        variant = ProductVariant.objects.get(product=product, size=size)
        Cart.objects.filter(user=request.user, variant=variant).delete()

        return Response({"message": "Removed from cart"}, status=200)


class CartListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True, context={"request": request})
        return Response(serializer.data, status=200)



class UpdateCartQtyView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, slug):
        action = request.data.get("action")
        size = request.data.get("size")

        product = get_object_or_404(Product, slug=slug)
        variant = get_object_or_404(ProductVariant, product=product, size=size)

        cart_item = get_object_or_404(
            Cart,
            user=request.user,
            variant=variant
        )

        if action == "increase":
            if cart_item.quantity >= variant.stock_qty:
                return Response(
                    {"detail": "Stock limit reached"},
                    status=400
                )
            cart_item.quantity += 1

        elif action == "decrease" and cart_item.quantity > 1:
            cart_item.quantity -= 1

        cart_item.save()

        return Response({
            "qty": cart_item.quantity,
            "available_stock": variant.stock_qty
        })



class AddToWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slug):
        
        product = Product.objects.filter(slug=slug).first()


        if not product:
            return Response({"message": "Product not found"}, status=400)

        # Create wishlist entry
        Wishlist.objects.get_or_create(user=request.user, product=product)
        return Response({"message": "Added to wishlist"}, status=200)


class RemoveFromWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, slug):
        # Look for product manually
        product = Product.objects.filter(slug=slug).first()


        if not product:
            return Response({"message": "Product not found"}, status=400)

        # Remove from wishlist
        Wishlist.objects.filter(user=request.user, product=product).delete()
        return Response({"message": "Removed from wishlist"}, status=200)
    


class WishlistListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        products = Product.objects.filter(
            wishlist__user=request.user
        )
        serializer = WishlistSerializer(
            products, many=True, context={"request": request}
        )
        return Response(serializer.data)
    


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderSerializer(orders, many=True, context={"request": request})
        return Response(serializer.data)



class CreateRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):
        rating = request.data.get("rating")
        review = request.data.get("review", "")

        if not rating or not (1 <= int(rating) <= 5):
            return Response({"detail": "Invalid rating"}, status=400)

        try:
            order = Order.objects.get(
                id=order_id,
                user=request.user,
                delivery_status="delivered"
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not delivered"},
                status=403
            )

        product = Product.objects.get(slug=order.product_slug)


        ProductRating.objects.create(
            product=product,
            user=request.user,
            order=order,
            rating=rating,
            review=review
        )

        return Response({"success": True}, status=201)

