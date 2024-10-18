from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from .models import Category, Book, BookHold, BookRental, BookImage
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
    permission_classes = [IsAuthenticated, IsStaffPermission]


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
    serializer_class = BookSerializer
    permission_classes = []

    def get_queryset(self):
        queryset = Book.objects.all()
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        return queryset


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


class HoldBookView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def post(self, request, *args, **kwargs):
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({"error": "No book ID provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        if book.available <= 0:
            return Response({"error": f"No available copies for {book.title}"}, status=status.HTTP_400_BAD_REQUEST)

        active_holds = book.holds.filter(hold_date__isnull=False)
        if active_holds.exists():
            return Response({"error": f"Book '{book.title}' is already on hold"}, status=status.HTTP_400_BAD_REQUEST)

        BookHold.objects.create(
            book=book,
            staff_member=request.user,
            hold_date=timezone.now()
        )

        book.available -= 1
        book.save()

        return Response({"detail": f"Book '{book.title}' has been placed on hold by {request.user.email}."}, status=status.HTTP_200_OK)


class RentBookView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({"error": "No book ID provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Find the book
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check if the book is available
        if book.available <= 0:
            return Response({"error": f"No available copies for {book.title}"}, status=status.HTTP_400_BAD_REQUEST)

        # Check user's membership
        active_membership = request.user.memberships.filter(active=True).first()
        if not active_membership:
            return Response({"error": "User does not have an active membership"}, status=status.HTTP_403_FORBIDDEN)

        # Check if user has already rented 4 books this month
        if active_membership.monthly_books >= 4:
            return Response({"error": "You have reached your limit of 4 books for this month"}, status=status.HTTP_403_FORBIDDEN)

        # Ensure the user hasn't already rented a book that hasn't been returned
        active_rentals = BookRental.objects.filter(user=request.user, return_date__isnull=True)
        if active_rentals.exists():
            return Response({"error": "You already have an active rental"}, status=status.HTTP_403_FORBIDDEN)

        # All checks passed, create the book rental
        BookRental.objects.create(
            book=book,
            user=request.user,
            rental_date=timezone.now(),
            due_date=timezone.now() + timezone.timedelta(days=7)  # Set the due date to 7 days after rental
        )

        # Update book availability and membership count
        book.available -= 1
        book.save()

        active_membership.monthly_books += 1
        active_membership.save()

        return Response({"detail": f"Book '{book.title}' rented successfully."}, status=status.HTTP_200_OK)


class RemoveHoldView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def post(self, request, *args, **kwargs):
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({"error": "No book ID provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Find the book
        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        # Find the active hold for this book
        hold = book.holds.filter(hold_date__isnull=False).first()

        if not hold:
            return Response({"error": f"No active hold found for {book.title}"}, status=status.HTTP_400_BAD_REQUEST)

        # Remove the hold
        hold.delete()

        # Update the book's availability
        book.available += 1
        book.save()

        return Response({"detail": f"Hold on book '{book.title}' removed successfully."}, status=status.HTTP_200_OK)


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
