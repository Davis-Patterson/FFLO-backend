from rest_framework import serializers
from .models import Category, Book, BookImage, BookRental
from Accounts.models import CustomUser
from Payments.serializers import PaymentSerializer

class BookImageSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = BookImage
        fields = ['image_url', 'image_file']
        read_only_fields = ['image_url']

class UserRentalSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name']

class CurrentRentalSerializer(serializers.ModelSerializer):
    user = UserRentalSerializer(read_only=True)
    payment = PaymentSerializer(read_only=True)
    free = serializers.BooleanField()

    class Meta:
        model = BookRental
        fields = ['user', 'rental_date', 'return_date', 'free', 'payment']

class CategorySerializer(serializers.ModelSerializer):
    books = serializers.StringRelatedField(many=True)
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'books', 'quantity']

    def get_quantity(self, obj):
        return obj.books.count()

class BookSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    images = BookImageSerializer(many=True, required=False)
    created_date = serializers.ReadOnlyField()
    flair = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True)
    archived = serializers.BooleanField(default=False)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'images', 'inventory', 'available', 'created_date', 'flair', 'categories', 'archived']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        categories_data = validated_data.pop('categories', [])

        book = Book.objects.create(**validated_data)
        book.categories.set(categories_data)

        # Handle image uploads
        for image_data in images_data:
            image_file = image_data.pop('image_file')
            BookImage.objects.create(book=book, image_file=image_file)

        return book

class BookDetailSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    images = BookImageSerializer(many=True, required=False)
    created_date = serializers.ReadOnlyField()
    flair = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    categories = serializers.StringRelatedField(many=True)
    archived = serializers.BooleanField(default=False)
    current_rentals = serializers.SerializerMethodField()
    rental_history = CurrentRentalSerializer(many=True, read_only=True, source='rentals')

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'images', 'inventory', 'available', 'created_date', 'flair', 'archived', 'categories', 'current_rentals', 'rental_history']

    def get_current_rentals(self, obj):
        # Get all active rentals (those with no return date)
        current_rentals = obj.rentals.filter(return_date__isnull=True)
        return CurrentRentalSerializer(current_rentals, many=True).data
