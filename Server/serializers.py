from rest_framework import serializers
from .models import Category, Book, BookImage, BookRental
from Accounts.models import CustomUser
from Common.serializers import UserImageSerializer

class BookImageSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(write_only=True, required=False)
    id = serializers.ReadOnlyField()

    class Meta:
        model = BookImage
        fields = ['id', 'image_url', 'image_small', 'image_file']
        read_only_fields = ['id', 'image_url', 'image_small']


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
    books = serializers.StringRelatedField(many=True, read_only=True)
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'books', 'quantity']

    def get_quantity(self, obj):
        return obj.books.count()


class BookSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    images = BookImageSerializer(many=True, required=False)
    created_date = serializers.ReadOnlyField()
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    flair = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True)
    archived = serializers.BooleanField(default=False)
    on_hold = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'images', 'inventory', 'available', 'created_date', 'flair', 'categories', 'archived', 'on_hold']

    def get_on_hold(self, obj):
        return obj.holds.filter(hold_date__isnull=False).exists()

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        categories_data = validated_data.pop('categories', [])

        book = Book.objects.create(**validated_data)
        book.categories.set(categories_data)

        for image_data in images_data:
            image_file = image_data.pop('image_file')
            BookImage.objects.create(book=book, image_file=image_file)

        return book


class RentalHistorySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = BookRental
        fields = ['rental_date', 'return_date', 'is_active', 'user']

    def get_user(self, obj):
        user_image = None
        if hasattr(obj.user, 'image') and obj.user.image:
            user_image = UserImageSerializer(obj.user.image).data
        
        return {
            "email": obj.user.email,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name if obj.user.last_name else "",
            "phone": obj.user.phone if obj.user.phone else None,
            "image": user_image
        }

    def get_is_active(self, obj):
        return obj.return_date is None


class BookDetailSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    images = BookImageSerializer(many=True, required=False)
    created_date = serializers.ReadOnlyField()
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    flair = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    categories = serializers.StringRelatedField(many=True)
    archived = serializers.BooleanField(default=False)
    current_status = serializers.SerializerMethodField()
    rental_history = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'images', 'inventory', 'available', 'created_date', 'flair', 'archived', 'categories', 'current_status', 'rental_history']

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
            held_by_image = UserImageSerializer(hold.user.image).data if hold.user.image else None

            status_list.append({
                "status": "on_hold",
                "hold_date": hold.hold_date,
                "held_by": {
                    "email": hold.user.email,
                    "first_name": hold.user.first_name,
                    "last_name": hold.user.last_name,
                    "image": held_by_image
                }
            })

        return status_list if status_list else None

    def get_rental_history(self, obj):
        rentals = obj.rentals.all().order_by('-rental_date')
        return RentalHistorySerializer(rentals, many=True).data

