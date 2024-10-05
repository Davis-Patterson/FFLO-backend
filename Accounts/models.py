from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    reset_code = models.CharField(max_length=6, blank=True, null=True)
    archived = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def reset_free_books(self):
        self.free_books = 0
        self.save()

class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    free_books_used = models.IntegerField(default=0)
    transaction_history = models.ManyToManyField('Transaction', related_name='membership_history', blank=True)
    recurrence = models.DateField(null=True, blank=True)
    membership_price = models.DecimalField(max_digits=6, decimal_places=2, default=35.00)  # Membership price field

    def __str__(self):
        return f"Membership for {self.user.email} (Active: {self.active})"

    def set_next_recurrence(self):
        """Sets the next payment date to one month after the current recurrence or start_date."""
        if not self.recurrence:
            self.recurrence = self.start_date + timedelta(days=30)
        else:
            self.recurrence = self.recurrence + timedelta(days=30)
        self.save()

class Transaction(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="transactions")  # Changed to CustomUser
    transaction_date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    item = models.CharField(max_length=255)
    stripe_payment_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Transaction of {self.amount} for {self.item} by {self.user.email}"
