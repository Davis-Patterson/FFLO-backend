from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from .models import Category, Book, BookRental, BookImage
from Accounts.models import CustomUser
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .serializers import CategorySerializer, BookSerializer, BookDetailSerializer

class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class BookCategoryUpdateView(generics.UpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def update(self, request, *args, **kwargs):
        book = self.get_object()
        categories_data = request.data.get('categories', [])
        categories = Category.objects.filter(id__in=categories_data)
        book.categories.set(categories)  # Update the book's categories
        book.save()
        return Response({"detail": "Book categories updated successfully"})


class BookListView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = []


class BookInfoView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    lookup_field = 'id'
    permission_classes = []


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookDetailSerializer
    lookup_field = 'id'
    permission_classes = [IsStaffPermission]

def rental_request(user, book_ids):
    books = Book.objects.filter(id__in=book_ids)
    active_membership = user.memberships.filter(active=True).first()
    free_books_remaining = 2 - active_membership.free_books_used if active_membership else 0

    total_rental_amount = 0
    free_books_used = 0
    book_availability = []

    for book in books:
        if book.available <= 0:
            return {"error": f"No copies available for book {book.title}"}

        is_free = free_books_remaining > 0

        if is_free:
            free_books_used += 1
            free_books_remaining -= 1
        else:
            total_rental_amount += book.rental_price

        book_availability.append({
            "book_id": book.id,
            "title": book.title,
            "free": is_free,
            "price": 0.00 if is_free else book.rental_price,
            "available_copies": book.available
        })

    return {
        "book_availability": book_availability,
        "total_rental_amount": total_rental_amount,
        "free_books_used": free_books_used
    }


class ReturnBookView(generics.GenericAPIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id')
        email = request.data.get('email')

        # Validate email input
        if not email:
            return Response({"detail": "Email address is required to return a book"}, status=status.HTTP_400_BAD_REQUEST)

        # Find the user by email
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"detail": "No user found with this email address"}, status=status.HTTP_400_BAD_REQUEST)

        # Find the active rental for this book and user
        rental = BookRental.objects.filter(book_id=book_id, user=user, return_date__isnull=True).first()

        # If no active rental is found for the book and user, return an error
        if not rental:
            return Response({"detail": "No active rental found for this book with the provided email"}, status=status.HTTP_400_BAD_REQUEST)

        # Mark the book as returned
        rental.return_date = timezone.now()
        rental.save()

        # Update the book's availability
        book = rental.book
        book.available += 1
        book.save()

        return Response({"detail": f"Book '{book.title}' returned successfully."}, status=status.HTTP_200_OK)


class BookCreateView(generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def perform_create(self, serializer):
        images_files = self.request.FILES.getlist('images')

        book = serializer.save()

        # Handle image uploads
        if images_files:
            for image_file in images_files:
                image_instance = BookImage(book=book)
                image_instance.save(image_file=image_file)


class DeleteBookView(generics.DestroyAPIView):
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated, IsStaffPermission]
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        book = self.get_object()
        book.delete()
        return Response({"detail": "Book deleted successfully"}, status=status.HTTP_200_OK)
