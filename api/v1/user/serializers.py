from django.utils.text import slugify
from rest_framework import serializers
from user.models import (Cart,Address,Order,ProductRating,CheckoutSession,
CheckoutItem,Wishlist)
from public.models import Product
from django.db.models import Sum

from rest_framework import serializers

class CheckoutItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField(source="variant.id")
    title = serializers.CharField(source="variant.product.title")
    price = serializers.DecimalField(source="variant.price", max_digits=10, decimal_places=2)
    mrp = serializers.DecimalField(source="variant.mrp", max_digits=10, decimal_places=2)
    delivery_charge = serializers.DecimalField(source="variant.product.delivery_charge", max_digits=10, decimal_places=2)
    qty = serializers.IntegerField()
    size = serializers.CharField(source="variant.size")
    stock = serializers.IntegerField(source="variant.stock_qty")
    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        request = self.context.get("request")

        if obj.variant.image:
            return request.build_absolute_uri(obj.variant.image.url)

        return None


class CheckoutSessionSerializer(serializers.ModelSerializer):
    items = serializers.SerializerMethodField()

    class Meta:
        model = CheckoutSession
        fields = ["id", "items"]  # ✅ id included

    def get_items(self, obj):
        items = obj.items.select_related("variant__product")
        return CheckoutItemSerializer(
            items,
            many=True,
            context=self.context
        ).data



class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["user"]


class CartSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="product.title", read_only=True)
    size = serializers.CharField(source="variant.size", read_only=True)
    price = serializers.DecimalField(source="variant.price", max_digits=10, decimal_places=2, read_only=True)
    image1 = serializers.ImageField(source="product.image1", read_only=True)
    slug = serializers.CharField(source="product.slug", read_only=True)
    stock = serializers.IntegerField(source="variant.stock_qty", read_only=True)
    mrp = serializers.DecimalField(source="product.mrp",max_digits=10,decimal_places=2)
    delivery_charge = serializers.DecimalField(source="product.delivery_charge",max_digits=10,decimal_places=2)

    class Meta:
        model = Cart
        fields = [
            "id",
            "product_id",
            "title",
            "price",
            "mrp",
            "delivery_charge",
            "image1",
            "slug",
            "quantity",
            "size",
            'stock'
        ]





class WishlistSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "price",
            "image1",
            "slug",
        ]

    




class ProductRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRating
        fields = ["id", "rating", "review", "created_at"]




class OrderSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    product_image = serializers.SerializerMethodField()
    product_category = serializers.SerializerMethodField()
    is_reviewed = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = "__all__"
        read_only_fields = [
            "user",
            "razorpay_order_id",
            "razorpay_payment_id",
            "razorpay_signature",
        ]
    def get_product_image(self, obj):
        try:
            Product.objects.get(slug=obj.product_slug)
            if product.image1:
                request = self.context.get("request")
                return request.build_absolute_uri(product.image1.url) if request else product.image1.url
            return None
        except Product.DoesNotExist:
            return None

    def get_product_category(self, obj):
        product = Product.objects.filter(slug=obj.product_slug).first()
        return product.product_category if product else None

    def get_is_reviewed(self, obj):
        return ProductRating.objects.filter(order=obj).exists()

    def get_rating(self, obj):
        rating = ProductRating.objects.filter(order=obj).first()
        return rating.rating if rating else None

    def get_review(self, obj):
        rating = ProductRating.objects.filter(order=obj).first()
        return rating.review if rating else None



