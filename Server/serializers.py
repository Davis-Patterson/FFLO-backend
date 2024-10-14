from rest_framework import serializers
from .models import Category, Book, BookImage, BookRental
from Accounts.models import CustomUser

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

    class Meta:
        model = BookRental
        fields = ['user', 'rental_date', 'return_date']


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
    on_hold = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'images', 'inventory', 'available', 'created_date', 'flair', 'categories', 'archived', 'on_hold']

    def get_on_hold(self, obj):
        return obj.holds.filter(hold_date__isnull=False).exists()

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
    current_status = serializers.SerializerMethodField()
    rental_history = CurrentRentalSerializer(many=True, read_only=True, source='rentals')

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'images', 'inventory', 'available', 'created_date', 'flair', 'archived', 'categories', 'current_status', 'rental_history']

    def get_current_status(self, obj):
        rentals = obj.rentals.filter(return_date__isnull=True)
        holds = obj.holds.filter(hold_date__isnull=False)

        status_list = []

        for rental in rentals:
            status_list.append({
                "status": "rented",
                "rental_date": rental.rental_date,
                "due_date": rental.due_date,
                "rented_by": {
                    "email": rental.user.email,
                    "first_name": rental.user.first_name,
                    "last_name": rental.user.last_name
                }
            })

        for hold in holds:
            status_list.append({
                "status": "on_hold",
                "hold_date": hold.hold_date,
                "held_by": {
                    "email": hold.staff_member.email,
                    "first_name": hold.staff_member.first_name,
                    "last_name": hold.staff_member.last_name
                }
            })

        return status_list if status_list else None
