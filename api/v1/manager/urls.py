from django.urls import path
from .views import (
    ManageProductView,
    ManageProductDetailView,
    PrepaidPaidOrderView,
    AllOrdersView,
    PendingShipmentOrdersView,
    IntransitOrdersView,
    DeliveredOrdersView,
    UpdateDeliveryStatusView,
    LowStockProductsView,
    OutOfStockProductsView,
    AvailableProductsView,
    UnAvailableProductsView
)

urlpatterns = [
    path('products/', ManageProductView.as_view(), name='admin-product-list-create'),
    path('products/<slug:slug>/', ManageProductDetailView.as_view(), name='admin-product-detail'),
    path("products/filter/out-of-stock/", OutOfStockProductsView.as_view(), name='admin-stockout-products'),
    path("products/filter/low-stock/", LowStockProductsView.as_view(), name='admin-lowstock-products'),
    path("products/filter/available/", AvailableProductsView.as_view(), name='admin-available-products'),
    path("products/filter/unavailable/", UnAvailableProductsView.as_view(), name='admin-unavailable-products'),
    path("all-orders/",AllOrdersView.as_view(),name="manager-all-orders"),
    path("orders/prepaid/paid/",PrepaidPaidOrderView.as_view(),name="prepaid-paid-orders"),
    path("orders/pending-shipments/",PendingShipmentOrdersView.as_view(),name="pending-shipment-orders"),
    path("orders/intransit/",IntransitOrdersView.as_view(),name="intransit-orders"),
    path("orders/delivered/",DeliveredOrdersView.as_view(),name="delivered-orders"),
    path("orders/<int:order_id>/update-delivery/",UpdateDeliveryStatusView.as_view()),

]
