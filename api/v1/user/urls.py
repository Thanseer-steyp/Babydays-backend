from django.urls import path
from .views import ( CartListView, AddToCartView, RemoveFromCartView,UpdateCartQtyView,
WishlistListView,AddToWishlistView,RemoveFromWishlistView,MeView,AddressView,
CreateOrderView,VerifyPaymentView,OrderListView,CreateRatingView,CreateCheckoutSessionView,
AddToCheckoutSessionView,CheckoutSessionDetailView)
    

urlpatterns = [
    path("address/", AddressView.as_view(),name="user-address"),
    path("me/", MeView.as_view(), name="user-data"),
    path("cart/", CartListView.as_view(), name="cart-list"),
    path("cart/add/<slug:slug>/", AddToCartView.as_view(), name="add-to-cart"),
    path("cart/remove/<slug:slug>/", RemoveFromCartView.as_view(), name="remove-from-cart"),
    path("cart/update/<slug:slug>/", UpdateCartQtyView.as_view(), name="update-cart-qty"),  
    path("wishlist/", WishlistListView.as_view(), name="wishlist-list"),
    path("wishlist/add/<slug:slug>/", AddToWishlistView.as_view(), name="add-to-wishlist"),
    path("wishlist/remove/<slug:slug>/", RemoveFromWishlistView.as_view(), name="remove-from-wishlist"),
    path('create-order/', CreateOrderView.as_view(), name='create-order'),
    path('verify-payment/', VerifyPaymentView.as_view(), name='verify-payment'),
    path("orders/", OrderListView.as_view(), name="user-orders"),
    path("orders/<int:order_id>/rate/",CreateRatingView.as_view(),name="rate-order"),
    path("checkout/session/create/", CreateCheckoutSessionView.as_view()),
    path("checkout/session/add/", AddToCheckoutSessionView.as_view()),
    path("checkout/session/", CheckoutSessionDetailView.as_view()),

]
