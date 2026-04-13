from django.contrib import admin
from .models import (Cart,Wishlist,Address,Order,ProductRating,
CheckoutSession,CheckoutItem)


admin.site.register(Cart)
admin.site.register(Wishlist)
admin.site.register(Address)
admin.site.register(Order)
admin.site.register(ProductRating)
admin.site.register(CheckoutSession)
admin.site.register(CheckoutItem)




