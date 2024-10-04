from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Book, BookRental
from Accounts.models import CustomUser
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone

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
