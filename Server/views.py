from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Book, BookRental, Image
from Accounts.models import CustomUser
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .serializers import BookSerializer

class RentBookView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id')
        book = Book.objects.get(id=book_id)
        user = request.user

        # Check inventory
        if book.available_inventory <= 0:
            return Response({"detail": "No copies available"}, status=status.HTTP_400_BAD_REQUEST)

        # Handle membership and free books
        if user.is_member and user.free_books_rented_this_week < 2:
            user.free_books_rented_this_week += 1
            user.save()

        # Create rental
        rental = BookRental.objects.create(book=book, student=user)
        book.available_inventory -= 1
        book.save()

        return Response({"detail": "Book rented successfully"}, status=status.HTTP_200_OK)

class ReturnBookView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id')
        book = Book.objects.get(id=book_id)
        user = request.user

        # Find the active rental for this user and book
        rental = BookRental.objects.filter(book=book, student=user, return_date__isnull=True).first()
        if not rental:
            return Response({"detail": "No active rental found"}, status=status.HTTP_400_BAD_REQUEST)

        # Mark the book as returned
        rental.return_date = timezone.now()
        rental.save()
        book.available_inventory += 1
        book.save()

        return Response({"detail": "Book returned successfully"}, status=status.HTTP_200_OK)

class BookCreateView(generics.CreateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        images_files = self.request.FILES.getlist('images')
        book = serializer.save()

        # Save each image file if provided
        if images_files:
            for image_file in images_files:
                Image.objects.create(book=book, image_file=image_file)
