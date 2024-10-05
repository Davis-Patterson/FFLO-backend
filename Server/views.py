from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from django.shortcuts import get_list_or_404
from .models import Category, Book, BookRental, Image
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

class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookDetailSerializer
    lookup_field = 'id'
    permission_classes = []

class FreeRentalView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        book_id = kwargs.get('book_id')
        
        # Check if the user is a member
        if not user.member:
            return Response({"detail": "User is not a member"}, status=status.HTTP_403_FORBIDDEN)

        # Check if the user has free rentals available
        if user.free_books <= 0:
            return Response({"detail": "No free rentals available this week"}, status=status.HTTP_400_BAD_REQUEST)

        # Find the book
        book = Book.objects.get(id=book_id)
        if book.available <= 0:
            return Response({"detail": f"No copies available for book {book.title}"}, status=status.HTTP_400_BAD_REQUEST)

        # Create rental
        rental = BookRental.objects.create(book=book, user=user)
        book.available -= 1
        book.save()

        # Deduct from user's free books count
        user.free_books -= 1
        user.save()

        return Response({"detail": f"Book '{book.title}' rented successfully"}, status=status.HTTP_200_OK)

class PaidRentalView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        book_id = kwargs.get('book_id')

        # Find the book
        book = Book.objects.get(id=book_id)
        if book.available <= 0:
            return Response({"detail": f"No copies available for book {book.title}"}, status=status.HTTP_400_BAD_REQUEST)

        # Create rental
        rental = BookRental.objects.create(book=book, user=user)
        book.available -= 1
        book.save()

        return Response({"detail": f"Book '{book.title}' rented successfully"}, status=status.HTTP_200_OK)

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
                image_instance = Image(book=book)
                image_instance.save(image_file=image_file)

class DeleteBookView(generics.DestroyAPIView):
    queryset = Book.objects.all()
    permission_classes = [IsAuthenticated, IsStaffPermission]
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        book = self.get_object()
        book.delete()
        return Response({"detail": "Book deleted successfully"}, status=status.HTTP_200_OK)
