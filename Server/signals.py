from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg
from .models import BookRating

@receiver(post_save, sender=BookRating)
@receiver(post_delete, sender=BookRating)
def update_book_rating(sender, instance, **kwargs):
    book = instance.book
    avg_rating = book.ratings.aggregate(average=Avg('rating'))['average']
    book.rating = avg_rating if avg_rating is not None else None
    book.save()