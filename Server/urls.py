from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookmarkViewSet, CategoryViewSet, BookListView, BookInfoView, BookDetailView, HoldBookView, RentBookView, RemoveHoldView, ReturnBookView, BookCreateView, DeleteBookView, BookCategoryUpdateView, BookUpdateView, ToggleArchiveView, ArchivedBookListView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')

urlpatterns = [
    path('', include(router.urls)),
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
    path('books/<int:id>/update/', BookUpdateView.as_view(), name='update-book'),
    path('books/<int:id>/archive/', ToggleArchiveView.as_view(), name='toggle-archive'),
    path('books/archived/', ArchivedBookListView.as_view(), name='archived-books'),
]
