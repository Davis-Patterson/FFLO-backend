import os
import uuid
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django.db import models
from utils import convert_to_webp
from storages.backends.s3boto3 import S3Boto3Storage

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
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    joined_date = models.DateTimeField(auto_now_add=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    archived = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    objects = CustomUserManager()

    def __str__(self):
        return self.email


    def reset_free_books(self):
        self.free_books = 0
        self.save()


class UserImage(models.Model):
    user = models.OneToOneField(CustomUser, related_name="image", on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        image_file = kwargs.pop('image_file', None)
        if image_file:
            # Remove the old image URL if it exists
            if self.image_url:
                self.delete_old_image()

            # Save the image file temporarily
            temp_image_path = f"/tmp/{image_file.name}"
            try:
                with open(temp_image_path, 'wb') as temp_image:
                    temp_image.write(image_file.read())

                # Convert the image to .webp
                webp_image_path = f"{temp_image_path}.webp"
                convert_to_webp(temp_image_path, webp_image_path)

                # Create an S3Boto3Storage instance
                s3_storage = S3Boto3Storage()

                # Strip the original file extension and add a unique suffix
                filename_without_extension = os.path.splitext(image_file.name)[0]
                unique_suffix = str(uuid.uuid4())

                # Prepend the 'users/' folder path
                s3_filename = f"users/{filename_without_extension}_{unique_suffix}.webp"

                # Upload to S3 and get the URL
                with open(webp_image_path, 'rb') as webp_file:
                    saved_path = s3_storage.save(s3_filename, webp_file)

                # Set the new image URL in the model
                self.image_url = f'{settings.MEDIA_URL}{s3_filename}'

            except Exception as e:
                print(f"Error while uploading image to S3: {str(e)}")

            finally:
                # Clean up the temporary files
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                if os.path.exists(webp_image_path):
                    os.remove(webp_image_path)

        super(UserImage, self).save(*args, **kwargs)

    def delete_old_image(self):
        # Optionally, implement S3 deletion logic if you want to remove the file from S3 as well.
        self.image_url = None


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    monthly_books = models.IntegerField(default=0)
    transaction_history = models.ManyToManyField('Payments.Payment', related_name='membership_history', blank=True)
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
