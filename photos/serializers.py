# photos/serializers.py
from django.utils import timezone
from rest_framework import serializers
from .models import RetroPhoto

class RetroPhotoSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)

    class Meta:
        model = RetroPhoto
        fields = [
            'id', 'image', 'year', 'azimuth', 'description',
            'location', 'location_name', 'owner', 'owner_username',
            'status', 'status_name', 'created_at'
        ]
        read_only_fields = ['owner', 'status', 'created_at', 'location_name', 'owner_username', 'status_name']

    def validate_year(self, value):
        current_year = timezone.now().year
        if value < 1800 or value > current_year:
            raise serializers.ValidationError(f'Year must be between 1800 and {current_year}.')
        return value

    def validate_azimuth(self, value):
        if value is not None and not 0 <= value <= 360:
            raise serializers.ValidationError('Azimuth must be between 0 and 360 degrees.')
        return value

    def validate_image(self, value):
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('Image size must not exceed 10 MB.')

        content_type = getattr(value, 'content_type', '')
        allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
        if content_type and content_type not in allowed_types:
            raise serializers.ValidationError('Only JPEG, PNG, and WebP images are allowed.')

        return value
