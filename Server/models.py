from django.db import models
from Accounts.models import CustomUser
from django.utils import timezone

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    image = models.ImageField(upload_to='book_images/', blank=True, null=True)
    inventory = models.PositiveIntegerField(default=1)
    available_inventory = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.title

class BookRental(models.Model):
    book = models.ForeignKey(Book, related_name="rentals", on_delete=models.CASCADE)
    student = models.ForeignKey(CustomUser, related_name="rented_books", on_delete=models.CASCADE)
    rental_date = models.DateTimeField(default=timezone.now)
    return_date = models.DateTimeField(blank=True, null=True)

    def is_returned(self):
        return self.return_date is not None
