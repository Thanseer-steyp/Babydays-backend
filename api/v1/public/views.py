from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from public.models import Product,ProductCategory
from .serializers import ProductSerializer,ProductCategorySerializer
from django.shortcuts import get_object_or_404


class CategoryView(APIView):

    def get(self, request):
        categories = ProductCategory.objects.all()

        serializer = ProductCategorySerializer(
            categories,
            many=True,
            context={"request": request}
        )

        return Response(serializer.data)


class ProductView(APIView):

    def get(self, request):
        q = request.query_params.get("q")
        category_slug = request.query_params.get("category")

        products = Product.objects.filter(is_available=True)

        if category_slug:
            products = products.filter(
                product_category__slug=category_slug
            )

        if q:
            products = products.filter(
                Q(title__icontains=q) |
                Q(material_type__icontains=q) |
                Q(pattern_design__icontains=q)
            )

        serializer = ProductSerializer(
            products,
            many=True,
            context={"request": request}
        )
        return Response(serializer.data)


class ProductDetailView(APIView):

    def get(self, request, slug):
        product = get_object_or_404(
            Product,
            slug=slug,
            is_available=True
        )

        serializer = ProductSerializer(
            product,
            context={"request": request}
        )

        return Response(serializer.data)
