from django.urls import path
from .views import BookListView, BookInfoView, BookDetailView, ReturnBookView, BookCreateView, DeleteBookView, BookCategoryUpdateView

urlpatterns = [
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:id>/', BookInfoView.as_view(), name='book-detail'),
    path('books/<int:id>/full/', BookDetailView.as_view(), name='book-detail'),
    path('books/<int:book_id>/return/', ReturnBookView.as_view(), name='return-book'),
    path('books/create/', BookCreateView.as_view(), name='create-book'),
    path('books/<int:id>/delete/', DeleteBookView.as_view(), name='delete-book'),
    path('books/<int:pk>/categories/', BookCategoryUpdateView.as_view(), name='update-book-categories'),
]
