from rest_framework import serializers
from .models import Bookmark, Category, Book, BookRating, BookImage, BookRental, Review
from Accounts.models import CustomUser
from Common.serializers import UserImageSerializer
from django.db.models import Avg


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
        fields = ['user', 'rental_date', 'return_date', 'is_active', 'reserved', 'late']

    def get_late(self, obj):
        return obj.late


class RentalHistorySerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = BookRental
        fields = ['rental_date', 'return_date', 'is_active', 'user', 'reserved']

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


class BookmarkSerializer(serializers.ModelSerializer):
    user_id = serializers.SerializerMethodField()
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Bookmark
        fields = ['id', 'book', 'user_id', 'user_email', 'created_at']
        read_only_fields = ['user_email', 'created_at']

    def get_user_email(self, obj):
        return obj.user.email

    def get_user_id(self, obj):
        return obj.user.id


class CategorySerializer(serializers.ModelSerializer):
    quantity = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color', 'icon', 'flair', 'sort_order', 'quantity']
        read_only_fields = ['sort_order', 'quantity']

    def get_quantity(self, obj):
        return obj.books.count()

    def validate_name(self, value):
        if len(value) > 15:
            raise serializers.ValidationError("Name must be 15 characters or fewer.")
        return value

    def validate_description(self, value):
        if len(value) > 50:
            raise serializers.ValidationError("Description must be 50 characters or fewer.")
        return value

    def validate_flair(self, value):
        if value is not None and len(value) > 10:
            raise serializers.ValidationError("Flair must be 10 characters or fewer.")
        return value

    def validate_color(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError("Color must be an integer.")
        return value

    def validate_icon(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError("Icon must be an integer.")
        return value


class BookRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookRating
        fields = ['id', 'book', 'user', 'rating']
        read_only_fields = ['user', 'book']

    def validate_rating(self, value):
        if not isinstance(value, int) or not 1 <= value <= 5:
            raise serializers.ValidationError("Rating must be an integer between 1 and 5.")
        return value


class BookSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    images = BookImageSerializer(many=True, required=False)
    created_date = serializers.ReadOnlyField()
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    flair = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), many=True)
    archived = serializers.BooleanField(default=False)
    on_hold = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    ratings = BookRatingSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'description', 'language', 'images', 'inventory', 'available', 'created_date', 'flair', 'categories', 'archived', 'on_hold', 'rating', 'ratings']

    def get_on_hold(self, obj):
        return obj.holds.filter(hold_date__isnull=False).exists()

    def get_rating(self, obj):
        average = obj.ratings.aggregate(average=Avg('rating'))['average']
        return average if average is not None else None

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        categories_data = validated_data.pop('categories', [])

        book = Book.objects.create(**validated_data)
        book.categories.set(categories_data)

        for image_data in images_data:
            image_file = image_data.pop('image_file')
            BookImage.objects.create(book=book, image_file=image_file)

        return book


class BookDetailSerializer(BookSerializer):
    checked_out = serializers.SerializerMethodField()
    rental_history = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = BookSerializer.Meta.fields + ['checked_out', 'rental_history']

    def get_checked_out(self, obj):
        active_rentals = obj.rentals.filter(return_date__isnull=True)
        return CurrentRentalSerializer(active_rentals, many=True).data

    def get_rental_history(self, obj):
        rental_history = obj.rentals.all().order_by('-rental_date')
        return RentalHistorySerializer(rental_history, many=True).data


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'name', 'message', 'created_at']
        read_only_fields = ['created_at']
