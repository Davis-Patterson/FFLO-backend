from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, BookCategoryUpdateView, BookListView, BookDetailView, FreeRentalView, PaidRentalView, ReturnBookView, BookCreateView, DeleteBookView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)

urlpatterns = [
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:id>/', BookDetailView.as_view(), name='book-detail'),
    path('books/<int:book_id>/free-rent/', FreeRentalView.as_view(), name='free-rent-book'),
    path('books/<int:book_id>/paid-rent/', PaidRentalView.as_view(), name='paid-rent-book'),
    path('books/<int:book_id>/return/', ReturnBookView.as_view(), name='return-book'),
    path('books/create/', BookCreateView.as_view(), name='create-book'),
    path('books/<int:id>/delete/', DeleteBookView.as_view(), name='delete-book'),
    path('books/<int:pk>/categories/', BookCategoryUpdateView.as_view(), name='update-book-categories'),
]
