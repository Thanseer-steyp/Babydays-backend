from rest_framework import serializers
from user.models import Order
from public.models import Product

class OrderListSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username", read_only=True)
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = "__all__"

    def get_product_image(self, obj):
        try:
            product = Product.objects.get(title=obj.product_name)
            if product.image1:
                request = self.context.get("request")
                return (
                    request.build_absolute_uri(product.image1.url)
                    if request else product.image1.url
                )
            return None
        except Product.DoesNotExist:
            return None
        

