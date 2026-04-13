from django.db import models
from django.utils import timezone
import random


class EmailOTP(models.Model):
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    count = models.IntegerField(default=0)   # how many OTPs generated
    validated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)  # first record creation
    last_sent = models.DateTimeField(default=timezone.now)  # track last OTP send time

    # store pending signup data until OTP is verified
    username = models.CharField(max_length=150, null=True, blank=True)
    name = models.CharField(max_length=150, null=True, blank=True)
    password = models.CharField(max_length=128, null=True, blank=True)

    def generate_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.count += 1
        self.validated = False
        self.last_sent = timezone.now()
        self.save()
        return self.otp