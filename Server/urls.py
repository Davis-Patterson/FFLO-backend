from django.urls import path
from .views import RentBookView, ReturnBookView

urlpatterns = [
    path('books/<int:book_id>/rent/', RentBookView.as_view(), name='rent-book'),
    path('books/<int:book_id>/return/', ReturnBookView.as_view(), name='return-book'),
]
