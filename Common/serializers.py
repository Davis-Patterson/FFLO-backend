from Accounts.models import UserImage
from rest_framework import serializers

class UserImageSerializer(serializers.ModelSerializer):
    image_file = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = UserImage
        fields = ['image_url', 'image_small', 'image_file']
        read_only_fields = ['image_url', 'image_small']