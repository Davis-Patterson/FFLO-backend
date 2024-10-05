import os
import uuid
from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from Accounts.models import CustomUser, Transaction
from django.utils import timezone
from .utils import convert_to_webp

print(default_storage.__class__.__name__)

class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    inventory = models.PositiveIntegerField(default=1)
    available = models.PositiveIntegerField(default=1)
    created_date = models.DateTimeField(auto_now_add=True)
    flair = models.CharField(max_length=10, blank=True, null=True)
    archived = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, related_name='books', blank=True)
    rental_price = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)

    def __str__(self):
        return self.title

class Image(models.Model):
    book = models.ForeignKey(Book, related_name="images", on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, null=True)

    def save(self, *args, **kwargs):
        image_file = kwargs.pop('image_file', None)
        if image_file:
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
                filename_without_extension = os.path.splitext(image_file.name)[0]  # Remove extension
                unique_suffix = str(uuid.uuid4())  # Generate a unique suffix
                s3_filename = f"{filename_without_extension}_{unique_suffix}.webp"
                
                # Ensure we're not duplicating the 'books' path
                webp_image_url = f"{s3_filename}"

                # Upload to S3 and get the URL
                with open(webp_image_path, 'rb') as webp_file:
                    saved_path = s3_storage.save(webp_image_url, webp_file)

                # Set the image URL in the model
                self.image_url = f'{settings.MEDIA_URL}{s3_filename}'

            except Exception as e:
                print(f"Error while uploading image to S3: {str(e)}")

            finally:
                # Clean up the temporary files
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                if os.path.exists(webp_image_path):
                    os.remove(webp_image_path)

        super(Image, self).save(*args, **kwargs)

class BookRental(models.Model):
    book = models.ForeignKey(Book, related_name="rentals", on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name="rented_books", on_delete=models.CASCADE)
    rental_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(blank=True, null=True)
    free = models.BooleanField(default=False)
    transaction = models.ForeignKey('Accounts.Transaction', related_name="rentals", on_delete=models.SET_NULL, null=True, blank=True)

    def is_returned(self):
        return self.return_date is not None
