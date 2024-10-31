from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Bookmark, Category, Book, BookHold, BookRental, BookImage
from Accounts.models import CustomUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, NotFound
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .serializers import BookmarkSerializer, CategorySerializer, BookSerializer, BookDetailSerializer

class IsStaffPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff

class BookmarkViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer  # Using BookSerializer to get full book details
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Get the list of book IDs that are bookmarked by the user
        bookmarked_book_ids = Bookmark.objects.filter(user=self.request.user).values_list('book', flat=True)
        # Return Book objects that match these IDs
        return Book.objects.filter(id__in=bookmarked_book_ids)

    def create(self, request, *args, **kwargs):
        book_id = request.data.get('book_id')

        if not book_id:
            return Response({"error": "Book ID is required to bookmark a book."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)

        if Bookmark.objects.filter(user=request.user, book=book).exists():
            return Response({"error": "Book is already bookmarked."}, status=status.HTTP_400_BAD_REQUEST)

        Bookmark.objects.create(user=request.user, book=book)

        # Serialize all bookmarked books
        bookmarks = self.get_queryset()
        serializer = BookSerializer(bookmarks, many=True)
        return Response({
            "detail": "Book bookmarked successfully.",
            "bookmarks": serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['delete'], url_path='remove/(?P<book_id>[^/.]+)')
    def remove(self, request, book_id=None):
        if not book_id:
            return Response({"error": "Book ID is required to remove a bookmark."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
            bookmark = Bookmark.objects.get(user=request.user, book=book)
        except Book.DoesNotExist:
            return Response({"error": "Book not found."}, status=status.HTTP_404_NOT_FOUND)
        except Bookmark.DoesNotExist:
            return Response({"error": "Bookmark not found for this book."}, status=status.HTTP_404_NOT_FOUND)

        bookmark.delete()

        # Serialize all remaining bookmarked books
        bookmarks = self.get_queryset()
        serializer = BookSerializer(bookmarks, many=True)
        return Response({
            "detail": "Bookmark removed successfully.",
            "bookmarks": serializer.data
        }, status=status.HTTP_200_OK)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        if self.action in ['create', 'destroy', 'update']:
            return [IsStaffPermission()]
        return [IsStaffPermission()]

    def create(self, request, *args, **kwargs):
        last_category = Category.objects.order_by('-sort_order').first()
        next_sort_order = last_category.sort_order + 1 if last_category else 1

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(sort_order=next_sort_order)

        categories = Category.objects.all().order_by('sort_order')
        all_categories_serializer = self.get_serializer(categories, many=True)

        return Response({
            'message': 'Category created successfully',
            'categories': all_categories_serializer.data
        }, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if 'flair' in request.data and request.data['flair'] == '':
            request.data['flair'] = None

        response = super().update(request, *args, **kwargs)
        categories = Category.objects.all().order_by('sort_order')
        serializer = self.get_serializer(categories, many=True)
        return Response({
            'message': 'Category updated successfully',
            'categories': serializer.data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], permission_classes=[IsStaffPermission])
    def reorder(self, request):
        order_data = request.data.get('order', [])
        
        if not isinstance(order_data, list) or not all(isinstance(id, int) for id in order_data):
            return Response({"error": "Invalid order data format."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            for sort_order, category_id in enumerate(order_data, start=1):
                category = Category.objects.get(id=category_id)
                category.sort_order = sort_order
                category.save()
        except Category.DoesNotExist:
            return Response({"error": "One or more category IDs are invalid."}, status=status.HTTP_400_BAD_REQUEST)

        ordered_categories = Category.objects.all().order_by('sort_order')
        serializer = self.get_serializer(ordered_categories, many=True)
        return Response({
            "message": "Categories reordered successfully.",
            "categories": serializer.data
        }, status=status.HTTP_200_OK)


class BookCategoryUpdateView(generics.UpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def update(self, request, *args, **kwargs):
        book = self.get_object()
        categories_data = request.data.get('categories', [])
        categories = Category.objects.filter(id__in=categories_data)
        book.categories.set(categories)
        book.save()
        return Response({"detail": "Book categories updated successfully"})

    def destroy(self, request, *args, **kwargs):
        category = self.get_object()
        category.delete()
        return Response({"message": "Category deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


class BookListView(generics.ListAPIView):
    serializer_class = BookSerializer
    permission_classes = []

    def get_queryset(self):
        queryset = Book.objects.filter(archived=False)
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        return queryset


class BookInfoView(generics.RetrieveAPIView):
    queryset = Book.objects.filter(archived=False)
    serializer_class = BookSerializer
    lookup_field = 'id'
    permission_classes = []


class BookDetailView(generics.RetrieveAPIView):
    queryset = Book.objects.filter(archived=False)
    serializer_class = BookDetailSerializer
    lookup_field = 'id'
    permission_classes = [IsStaffPermission]


class HoldBookView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def post(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id')  # Get book ID from the URL
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
            user=request.user,
            hold_date=timezone.now()
        )

        book.available -= 1
        book.save()

        return Response({"detail": f"Book '{book.title}' has been placed on hold by {request.user.email}."}, status=status.HTTP_200_OK)


class RentBookView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id') 
        if not book_id:
            return Response({"error": "No book ID provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        if book.available <= 0:
            return Response({"error": f"No available copies for {book.title}"}, status=status.HTTP_400_BAD_REQUEST)

        active_membership = request.user.memberships.filter(active=True).first()
        if not active_membership:
            return Response({"error": "User does not have an active membership"}, status=status.HTTP_403_FORBIDDEN)

        if active_membership.monthly_books >= 4:
            return Response({"error": "You have reached your limit of 4 books for this month"}, status=status.HTTP_403_FORBIDDEN)

        active_rentals = BookRental.objects.filter(user=request.user, return_date__isnull=True)
        if active_rentals.exists():
            return Response({"error": "You already have an active rental"}, status=status.HTTP_403_FORBIDDEN)

        BookRental.objects.create(
            book=book,
            user=request.user,
            rental_date=timezone.now(),
            due_date=timezone.now() + timezone.timedelta(days=7)
        )

        book.available -= 1
        book.save()

        active_membership.monthly_books += 1
        active_membership.save()

        return Response({"detail": f"Book '{book.title}' rented successfully."}, status=status.HTTP_200_OK)


class RemoveHoldView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def post(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id')
        if not book_id:
            return Response({"error": "No book ID provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            return Response({"error": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        hold = book.holds.filter(hold_date__isnull=False).first()

        if not hold:
            return Response({"error": f"No active hold found for {book.title}"}, status=status.HTTP_400_BAD_REQUEST)

        hold.delete()

        book.available += 1
        book.save()

        return Response({"detail": f"Hold on book '{book.title}' removed successfully."}, status=status.HTTP_200_OK)


class ReturnBookView(generics.GenericAPIView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id')
        email = request.data.get('email')

        if not email:
            return Response({"detail": "Email address is required to return a book"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"detail": "No user found with this email address"}, status=status.HTTP_400_BAD_REQUEST)

        rental = BookRental.objects.filter(book_id=book_id, user=user, return_date__isnull=True).first()

        if not rental:
            return Response({"detail": "No active rental found for this book with the provided email"}, status=status.HTTP_400_BAD_REQUEST)

        rental.return_date = timezone.now()
        rental.save()

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
        
        try:
            book = serializer.save()
        except ValidationError as e:
            raise ValidationError({"detail": "A book with this title already exists."})
        
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


class BookUpdateView(generics.UpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsStaffPermission]
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        book = self.get_object()
        data = request.data

        title = data.get('title')
        author = data.get('author')

        if not title:
            return Response({"detail": "Title cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)
        if not author:
            return Response({"detail": "Author cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

        book.title = title
        book.author = author
        book.description = data.get('description', book.description)
        book.flair = data.get('flair', book.flair)
        book.inventory = data.get('inventory', book.inventory)
        book.available = data.get('available', book.available)
        
        categories_data = data.get('categories', [])
        if isinstance(categories_data, str):
            categories_data = categories_data.split(',')

        try:
            category_ids = [int(category_id.strip()) for category_id in categories_data]
        except ValueError:
            return Response({"detail": "Invalid category ID format."}, status=status.HTTP_400_BAD_REQUEST)

        if category_ids:
            categories = Category.objects.filter(id__in=category_ids)
            if categories.exists():
                book.categories.add(*categories)

        categories_to_remove = data.get('categories_to_remove', [])
        if isinstance(categories_to_remove, str):
            categories_to_remove = categories_to_remove.split(',')

        try:
            categories_to_remove = [int(category_id.strip()) for category_id in categories_to_remove]
        except ValueError:
            return Response({"detail": "Invalid category ID format."}, status=status.HTTP_400_BAD_REQUEST)

        if categories_to_remove:
            categories_to_remove_objects = Category.objects.filter(id__in=categories_to_remove)
            book.categories.remove(*categories_to_remove_objects)

        book.save()

        images_to_add = request.FILES.getlist('images')
        for image_file in images_to_add:
            image_instance = BookImage(book=book)
            image_instance.save(image_file=image_file)

        images_to_remove = data.get('images_to_remove', [])

        if isinstance(images_to_remove, str):
            images_to_remove = images_to_remove.split(',')
        
        try:
            images_to_remove = [int(image_id) for image_id in images_to_remove]
        except ValueError:
            return Response({"detail": "Invalid image ID format."}, status=status.HTTP_400_BAD_REQUEST)

        # Delete the images
        for image_id in images_to_remove:
            try:
                image = BookImage.objects.get(id=image_id, book=book)
                image.delete()
            except BookImage.DoesNotExist:
                return Response({"detail": f"Image with id {image_id} not found for this book."}, status=status.HTTP_404_NOT_FOUND)

        book.refresh_from_db()

        serializer = BookSerializer(book)
        return Response({
            "detail": f"Book '{book.title}' updated successfully.",
            "book": serializer.data
        }, status=status.HTTP_200_OK)


class ToggleArchiveView(APIView):
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def post(self, request, id):
        try:
            book = Book.objects.get(id=id)
        except Book.DoesNotExist:
            raise NotFound("Book not found")

        # Toggle the archived status
        book.archived = not book.archived
        book.save()

        status_text = "archived" if book.archived else "unarchived"
        return Response({
            "detail": f"Book '{book.title}' has been {status_text}.",
            "archived": book.archived
        }, status=status.HTTP_200_OK)


class ArchivedBookListView(generics.ListAPIView):
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated, IsStaffPermission]

    def get_queryset(self):
        return Book.objects.filter(archived=True)
