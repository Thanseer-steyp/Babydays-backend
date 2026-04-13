from rest_framework import serializers
from django.contrib.auth.models import User

class EmailAuthSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)
