from django.db import models
from django.contrib.auth.models import User
from public.models import Product,ProductVariant
from django.conf import settings


class CheckoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    total_amount = models.FloatField(default=0)
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("expired", "Expired"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    def __str__(self):
        return f"Session {self.id} - {self.user.username} - {self.status}"

class CheckoutItem(models.Model):
    session = models.ForeignKey(CheckoutSession, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("session", "variant")

    def __str__(self):
        return f"{self.variant.product.title} ({self.variant.size}) x {self.qty}"

    
class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="addresses")

    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    alt_phone = models.CharField(max_length=15, blank=True, null=True)

    pincode = models.CharField(max_length=6)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    address_line = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=100, blank=True, null=True)

    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.city}"


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'variant')

    def __str__(self):
        return f"{self.user.username} - {self.product.title} ({self.variant.size})"



class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product")

    def __str__(self):
        return f"{self.user} - {self.product}"
    

class Order(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ("initiated", "Initiated"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("prepaid", "Prepaid"),
        ("cod", "Cash on Delivery"),
    ]

    PAYMENT_CHANNEL_CHOICES = [
        ("upi", "UPI"),
        ("card", "Card"),
        ("netbanking", "NetBanking"),
        ("wallet", "Wallet"),
    ]
    DELIVERY_STATUS_CHOICES = [
        ("ordered", "Ordered"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    product_slug = models.SlugField()
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True)
    size = models.CharField(max_length=50, blank=True)
    qty = models.PositiveIntegerField(default=1)
    mrp = models.FloatField()
    price = models.FloatField()
    discount = models.FloatField(default=0)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="prepaid"
    )
    payment_channel = models.CharField(
        max_length=20, choices=PAYMENT_CHANNEL_CHOICES, blank=True
    )
    delivery_charge = models.FloatField(default=0)
    total = models.FloatField()
    razorpay_order_id = models.CharField(max_length=255, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default="initiated"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    name = models.CharField(max_length=100)          # delivery name
    phone = models.CharField(max_length=15)         # phone number
    alt_phone = models.CharField(max_length=15, blank=True, null=True)
    pincode = models.CharField(max_length=6)
    state = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    location = models.CharField(max_length=100)
    address_line = models.TextField(blank=True, null=True)
    landmark = models.CharField(max_length=100, blank=True, null=True)


    delivery_status = models.CharField(
        max_length=20, choices=DELIVERY_STATUS_CHOICES, default="ordered"
    )
    delivery_partner = models.CharField(max_length=100, blank=True, null=True)
    tracking_code = models.CharField(max_length=100, blank=True, null=True)
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user} - {self.product_name} - {self.payment_method} ({self.payment_status})"



class ProductRating(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="reviews"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.OneToOneField(Order, on_delete=models.CASCADE)

    rating = models.PositiveSmallIntegerField()  # 1–5
    review = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "product", "order")

    def __str__(self):
        return f"{self.product.title} - {self.rating}⭐"
