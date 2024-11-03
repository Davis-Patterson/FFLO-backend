from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookmarkViewSet, CategoryViewSet, BookListView, BookInfoView, BookDetailView, HoldBookView, BookReservationView, BookRentalActivateView, RemoveHoldView, ReturnBookView, BookCreateView, DeleteBookView, BookCategoryUpdateView, BookUpdateView, ToggleArchiveView, ArchivedBookListView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')

urlpatterns = [
    path('', include(router.urls)),
    path('books/', BookListView.as_view(), name='book-list'),
    path('books/<int:id>/', BookInfoView.as_view(), name='book-detail'),
    path('books/<int:id>/full/', BookDetailView.as_view(), name='book-detail'),
    path('books/<int:book_id>/hold/', HoldBookView.as_view(), name='hold-book'),
    path('books/<int:book_id>/reserve/', BookReservationView.as_view(), name='book-reservation'),
    path('rentals/<int:rental_id>/activate/', BookRentalActivateView.as_view(), name='book-activate'),
    path('books/<int:book_id>/remove-hold/', RemoveHoldView.as_view(), name='remove-hold'),
    path('books/<int:book_id>/return/', ReturnBookView.as_view(), name='return-book'),
    path('books/create/', BookCreateView.as_view(), name='create-book'),
    path('books/<int:id>/delete/', DeleteBookView.as_view(), name='delete-book'),
    path('books/<int:pk>/categories/', BookCategoryUpdateView.as_view(), name='update-book-categories'),
    path('books/<int:id>/update/', BookUpdateView.as_view(), name='update-book'),
    path('books/<int:id>/archive/', ToggleArchiveView.as_view(), name='toggle-archive'),
    path('books/archived/', ArchivedBookListView.as_view(), name='archived-books'),
    path('bookmarks/remove/<int:book_id>/', BookmarkViewSet.as_view({'delete': 'remove'}), name='bookmark-remove'),
]
