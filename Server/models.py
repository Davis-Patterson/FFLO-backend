import os
import uuid
from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from Accounts.models import CustomUser
from Payments.models import Payment
from django.utils import timezone
from utils import convert_to_webp

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

    def __str__(self):
        return self.title

    def is_on_hold(self):
        return bool(self.on_hold_by)


class BookImage(models.Model):
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
                
                # **Prepend the 'books/' folder path**
                s3_filename = f"books/{filename_without_extension}_{unique_suffix}.webp"
                
                # Upload to S3 and get the URL
                with open(webp_image_path, 'rb') as webp_file:
                    saved_path = s3_storage.save(s3_filename, webp_file)

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

        super(BookImage, self).save(*args, **kwargs)


class BookRental(models.Model):
    book = models.ForeignKey(Book, related_name="rentals", on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name="rented_books", on_delete=models.CASCADE)
    rental_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(blank=True, null=True)
    return_date = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.rental_date + timezone.timedelta(days=7)
        super(BookRental, self).save(*args, **kwargs)

    def is_returned(self):
        return self.return_date is not None


class BookHold(models.Model):
    book = models.ForeignKey(Book, related_name="holds", on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    hold_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.book.title} held by {self.user.first_name} on {self.hold_date} (email: {self.user.email})"
