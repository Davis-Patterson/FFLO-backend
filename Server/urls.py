from django.urls import path
from .views import BookListView, BookInfoView, BookDetailView, HoldBookView, RentBookView, RemoveHoldView, ReturnBookView, BookCreateView, DeleteBookView, BookCategoryUpdateView

urlpatterns = [
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:id>/', BookInfoView.as_view(), name='book-detail'),
    path('books/<int:id>/full/', BookDetailView.as_view(), name='book-detail'),
    path('books/<int:book_id>/hold/', HoldBookView.as_view(), name='hold-book'),
    path('books/<int:book_id>/rent/', RentBookView.as_view(), name='rent-book'),
    path('books/<int:book_id>/remove-hold/', RemoveHoldView.as_view(), name='remove-hold'),
    path('books/<int:book_id>/return/', ReturnBookView.as_view(), name='return-book'),
    path('books/create/', BookCreateView.as_view(), name='create-book'),
    path('books/<int:id>/delete/', DeleteBookView.as_view(), name='delete-book'),
    path('books/<int:pk>/categories/', BookCategoryUpdateView.as_view(), name='update-book-categories'),
]
