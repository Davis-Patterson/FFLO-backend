import os
from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from Accounts.models import CustomUser
from django.utils import timezone
from .utils import convert_to_webp

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    inventory = models.PositiveIntegerField(default=1)
    available_inventory = models.PositiveIntegerField(default=1)
    flair = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.title

class Image(models.Model):
    book = models.ForeignKey(Book, related_name="images", on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, null=True)  # URL for the .webp image

    def save(self, *args, **kwargs):
        image_file = kwargs.pop('image_file', None)
        if image_file:
            # Save the image file temporarily
            temp_image_path = f"/tmp/{image_file.name}"
            with open(temp_image_path, 'wb') as temp_image:
                temp_image.write(image_file.read())

            # Convert the image to .webp
            webp_image_path = f"{temp_image_path}.webp"
            convert_to_webp(temp_image_path, webp_image_path)  # Call the conversion function

            # Upload to S3 and get the URL
            with open(webp_image_path, 'rb') as webp_file:
                webp_image_url = default_storage.save(f"book_images/{os.path.basename(webp_image_path)}", webp_file)

            self.image_url = f"{settings.MEDIA_URL}{webp_image_url}"

            # Clean up the temporary files
            os.remove(temp_image_path)
            os.remove(webp_image_path)

        super(Image, self).save(*args, **kwargs)

class BookRental(models.Model):
    book = models.ForeignKey(Book, related_name="rentals", on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, related_name="rented_books", on_delete=models.CASCADE)
    rental_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(blank=True, null=True)

    def is_returned(self):
        return self.return_date is not None
