from rest_framework import serializers
from .models import Book, Image

class ImageSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Image
        fields = ['image_url', 'image_file']
        read_only_fields = ['image_url']

class BookSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField()
    images = ImageSerializer(many=True, required=False)
    created_date = serializers.ReadOnlyField()
    flair = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    archived = serializers.BooleanField(default=False)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'images', 'inventory', 'available', 'created_date', 'flair', 'archived']

    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        book = Book.objects.create(**validated_data)

        # Handle image uploads
        for image_data in images_data:
            image_file = image_data.pop('image_file')
            Image.objects.create(book=book, image_file=image_file)

        return book
