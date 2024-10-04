from django.urls import path
from .views import RentBookView, ReturnBookView, BookCreateView, DeleteBookView

urlpatterns = [
    path('books/<int:book_id>/rent/', RentBookView.as_view(), name='rent-book'),
    path('books/<int:book_id>/return/', ReturnBookView.as_view(), name='return-book'),
    path('books/create/', BookCreateView.as_view(), name='create-book'),
    path('books/<int:id>/delete/', DeleteBookView.as_view(), name='delete-book'),
]
