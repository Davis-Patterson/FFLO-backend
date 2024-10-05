from django.urls import path
from .views import CheckoutView, CheckoutFinalizationView, BookListView, BookDetailView, ReturnBookView, BookCreateView, DeleteBookView, BookCategoryUpdateView

urlpatterns = [
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('checkout/finalize/', CheckoutFinalizationView.as_view(), name='checkout-finalize'),
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:id>/', BookDetailView.as_view(), name='book-detail'),
    path('books/<int:book_id>/return/', ReturnBookView.as_view(), name='return-book'),
    path('books/create/', BookCreateView.as_view(), name='create-book'),
    path('books/<int:id>/delete/', DeleteBookView.as_view(), name='delete-book'),
    path('books/<int:pk>/categories/', BookCategoryUpdateView.as_view(), name='update-book-categories'),
]
