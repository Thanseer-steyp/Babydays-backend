from django.urls import path
from api.v1.register.views import EmailAuthView,GoogleLoginView,RefreshTokenView,LogoutView
from rest_framework_simplejwt.views import TokenObtainPairView,TokenRefreshView


urlpatterns = [
    path('auth/', EmailAuthView.as_view(), name='email-auth'),
    path("google-login/", GoogleLoginView.as_view()),
    path("refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]
