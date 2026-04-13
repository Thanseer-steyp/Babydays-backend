from django.urls import path
from .views import ProductView,ProductDetailView,CategoryView


urlpatterns = [
    path('products/', ProductView.as_view(), name='product-operations'),
    path('products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail-operations'),
    path('categories/', CategoryView.as_view(), name='category-list'),
]
