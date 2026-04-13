from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .serializers import EmailAuthSerializer

from google.oauth2 import id_token
from google.auth.transport import requests

from rest_framework.views import APIView

class RefreshTokenView(APIView):
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")

        if not refresh_token:
            return Response({"error": "No refresh token"}, status=400)

        try:
            token = RefreshToken(refresh_token)
            new_access = str(token.access_token)

            response = Response({"message": "Token refreshed"})
            response.set_cookie(
                key="access",
                value=new_access,
                httponly=True,
                secure=False,
                samesite="Lax",
            )
            return response

        except Exception:
            return Response({"error": "Invalid refresh token"}, status=400)

class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "Logged out"})

        response.delete_cookie("access")
        response.delete_cookie("refresh")

        return response

CLIENT_ID = "1065094393006-4b9tr4v35nf2l52ohi158evfmgbkge80.apps.googleusercontent.com"


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [] 

    def post(self, request):
        token = request.data.get("token")

        if not token:
            return Response({"error": "Token missing"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), CLIENT_ID
            )

            email = idinfo.get("email")
            name = idinfo.get("name", "")

            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    "email": email,
                    "first_name": name
                }
            )

            refresh = RefreshToken.for_user(user)

            response = Response({
                "message": "Signup successful" if created else "Login successful",
                "data": {
                    "user_id": user.id,
                    "name": user.first_name,
                    "email": user.email,
                    "username": user.username,
                }
            }, status=status.HTTP_200_OK)
            response.set_cookie(
                key="access",
                value=str(refresh.access_token),
                httponly=True,
                secure=False,  # ⚠️ True in production (HTTPS)
                samesite="Lax",
                max_age=60 * 60,  # 1 hour
            )

            response.set_cookie(
                key="refresh",
                value=str(refresh),
                httponly=True,
                secure=False,  # ⚠️ True in production
                samesite="Lax",
                max_age=7 * 24 * 60 * 60,  # 7 days
            )
            return response        

        except ValueError:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )


class EmailAuthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = EmailAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        base_username = email.split("@")[0]
        username = base_username

        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1


        try:
            user = User.objects.get(email=email)

            # 🔐 Login flow
            if not user.check_password(password):
                return Response(
                    {"error": "Invalid password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            is_new_user = False

        except User.DoesNotExist:
            # 🆕 Signup flow
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            is_new_user = True

        refresh = RefreshToken.for_user(user)

        return Response({
            "message": "Signup successful" if is_new_user else "Login successful",
            "data": {
                "user_id": user.id,
                "email": user.email,
                "username": user.username,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }
        }, status=status.HTTP_200_OK)

