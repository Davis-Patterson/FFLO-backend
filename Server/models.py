import os
import uuid
import re
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage
from storages.backends.s3boto3 import S3Boto3Storage
from Accounts.models import CustomUser
from Payments.models import Payment
from django.utils import timezone
from Common.utils import convert_to_webp, create_small_image
from django.db.models import Avg

class Category(models.Model):
    name = models.CharField(max_length=15, unique=True)
    description = models.CharField(max_length=50)
    color = models.IntegerField()
    icon = models.IntegerField()
    flair = models.CharField(max_length=10, blank=True, null=True)
    sort_order = models.IntegerField()

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255, unique=True)
    author = models.CharField(max_length=255)
    description = models.CharField(max_length=1200, blank=True, null=True)
    language = models.CharField(max_length=20, default="Français")
    rating = models.FloatField(null=True, blank=True)
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

    def get_rating(self):
        average = self.ratings.aggregate(average=Avg('rating'))['average']
        return average

    def update_available(self):
        if not self.pk:
          return
        reserved_count = BookRental.objects.filter(book=self, reserved=True).count()
        active_count = BookRental.objects.filter(book=self, is_active=True).count()
        hold_count = BookHold.objects.filter(book=self).count()

        self.available = max(self.inventory - (reserved_count + active_count + hold_count), 0)

    def save(self, *args, **kwargs):
        self.update_available()
        super(Book, self).save(*args, **kwargs)


class BookRating(models.Model):
    book = models.ForeignKey(Book, related_name="ratings", on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="book_ratings", on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)], blank=True, null=True)

    class Meta:
        unique_together = ('book', 'user')
    
    def __str__(self):
        return f"Rating of {self.rating} for {self.book.title} by {self.user.username}"


class Bookmark(models.Model):
    book = models.ForeignKey(Book, related_name="bookmarks", on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name="bookmarks", on_delete=models.CASCADE, limit_choices_to={'is_staff': False})
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('book', 'user')
        verbose_name = 'Bookmark'
        verbose_name_plural = 'Bookmarks'

    def __str__(self):
        return f"{self.user.username} bookmarked {self.book.title}"


class BookImage(models.Model):
    book = models.ForeignKey(Book, related_name="images", on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, null=True)
    image_small = models.URLField(blank=True, null=True)

    def clean_filename(self, filename):
        filename = filename.lower()
        filename = filename.replace(' ', '_')
        filename = re.sub(r'[^a-z0-9_\-\.]', '', filename)
        filename = filename.strip('.')
        name, ext = os.path.splitext(filename)
        if len(name) > 100:
            name = name[:100]

        return f"{name}{ext}"

    def save(self, *args, **kwargs):
        image_file = kwargs.pop('image_file', None)
        if image_file:
            clean_filename = self.clean_filename(image_file.name)
            temp_image_path = f"/tmp/{clean_filename}"
            temp_small_image_path = f"/tmp/{clean_filename}_small.webp"

            try:
                with open(temp_image_path, 'wb') as temp_image:
                    temp_image.write(image_file.read())

                webp_image_path = f"{temp_image_path}.webp"
                convert_to_webp(temp_image_path, webp_image_path)

                create_small_image(temp_image_path, temp_small_image_path)

                s3_storage = S3Boto3Storage()

                filename_without_extension = os.path.splitext(clean_filename)[0]
                unique_suffix = str(uuid.uuid4())

                s3_filename = f"books/{filename_without_extension}_{unique_suffix}.webp"
                s3_small_filename = f"books/{filename_without_extension}_small_{unique_suffix}.webp"
                
                with open(webp_image_path, 'rb') as webp_file:
                    saved_path = s3_storage.save(s3_filename, webp_file)
                    self.image_url = f'{settings.MEDIA_URL}{s3_filename}'

                with open(temp_small_image_path, 'rb') as small_webp_file:
                    small_saved_path = s3_storage.save(s3_small_filename, small_webp_file)
                    self.image_small = f'{settings.MEDIA_URL}{s3_small_filename}'

            except Exception as e:
                print(f"Error while uploading image to S3: {str(e)}")

            finally:
                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)
                if os.path.exists(webp_image_path):
                    os.remove(webp_image_path)
                if os.path.exists(temp_small_image_path):
                    os.remove(temp_small_image_path)

        super(BookImage, self).save(*args, **kwargs)


class BookRental(models.Model):
    book = models.ForeignKey(Book, related_name="rentals", on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, related_name="rented_books", on_delete=models.CASCADE)
    rental_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(blank=True, null=True)
    return_date = models.DateTimeField(blank=True, null=True)
    reserved = models.BooleanField(default=True)
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = self.rental_date + timezone.timedelta(days=7)
        super(BookRental, self).save(*args, **kwargs)

    @property
    def late(self):
        if self.return_date:
            return False
        if self.due_date and timezone.now().date() > self.due_date.date():
            return True
        return False


class BookHold(models.Model):
    book = models.ForeignKey(Book, related_name="holds", on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    hold_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.book.title} held by {self.user.first_name} on {self.hold_date} (email: {self.user.email})"


class Review(models.Model):
    name = models.CharField(max_length=50)
    message = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.name}"
