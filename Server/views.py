from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from django.shortcuts import get_list_or_404
from .models import Category, Book, BookRental, Image
from Accounts.models import Transaction
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

class CheckoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        cart_items = request.data.get('cart_items', [])
        if not cart_items:
            return Response({"detail": "No items in the cart"}, status=status.HTTP_400_BAD_REQUEST)

        book_ids = [item['book_id'] for item in cart_items if item['type'] == 'rental']
        total_amount = 0
        rental_details = {}

        # If there are rentals in the cart, calculate rental prices
        if book_ids:
            rental_details = rental_request(user, book_ids)
            if "error" in rental_details:
                return Response({"detail": rental_details["error"]}, status=status.HTTP_400_BAD_REQUEST)
            total_amount += rental_details["total_rental_amount"]

        # Add other types of cart items here (e.g., merchandise)

        # Send total_amount to Stripe for payment processing (integration handled later)
        # For now, we assume the payment request is created successfully and return the total amount
        return Response({
            "total_amount": total_amount,
            "rental_details": rental_details,
            "stripe_payment_intent": None  # Placeholder for Stripe payment intent
        }, status=status.HTTP_200_OK)

class CheckoutFinalizationView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        payment_successful = request.data.get('payment_successful', False)
        stripe_payment_id = request.data.get('stripe_payment_id', None)
        cart_items = request.data.get('cart_items', [])

        if not payment_successful or not stripe_payment_id:
            return Response({"detail": "Payment failed or incomplete"}, status=status.HTTP_400_BAD_REQUEST)

        book_ids = [item['book_id'] for item in cart_items if item['type'] == 'rental']
        rentals = []

        # Finalize rentals if present
        if book_ids:
            rental_details = rental_request(user, book_ids)
            if "error" in rental_details:
                return Response({"detail": rental_details["error"]}, status=status.HTTP_400_BAD_REQUEST)

            for book_id in book_ids:
                book = Book.objects.get(id=book_id)
                free_rental = rental_details['free_books_used'] > 0
                rental = BookRental.objects.create(book=book, user=user, free=free_rental)
                rentals.append(rental)
                book.available -= 1
                book.save()

            # Update membership free books if used
            active_membership = user.memberships.filter(active=True).first()
            if active_membership:
                active_membership.free_books_used += rental_details['free_books_used']
                active_membership.save()

        # Record the transaction
        transaction = Transaction.objects.create(
            user=user,
            amount=sum([item['price'] for item in cart_items]),
            stripe_payment_id=stripe_payment_id
        )

        return Response({
            "detail": "Checkout finalized successfully",
            "rental_ids": [rental.id for rental in rentals],
            "transaction_id": transaction.id
        }, status=status.HTTP_200_OK)

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
