# photos/serializers.py
from django.utils import timezone
from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import RetroPhoto


class RetroPhotoSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    status_name = serializers.CharField(source='status.name', read_only=True)

    # Поля для чтения (откуда взята точка)
    shooting_lat = serializers.SerializerMethodField(read_only=True)
    shooting_lon = serializers.SerializerMethodField(read_only=True)
    shooting_azimuth = serializers.SerializerMethodField(read_only=True)  # ← ДОБАВЛЕНО

    # Поля для записи (то что присылает пользователь)
    shooting_lat_write = serializers.FloatField(write_only=True, required=False, allow_null=True)
    shooting_lon_write = serializers.FloatField(write_only=True, required=False, allow_null=True)
    shooting_azimuth_write = serializers.FloatField(write_only=True, required=False, allow_null=True)  # ← ДОБАВЛЕНО

    class Meta:
        model = RetroPhoto
        fields = [
            'id', 'image', 'year', 'azimuth', 'description',
            'location', 'location_name', 'owner', 'owner_username',
            'status', 'status_name', 'created_at',
            'shooting_lat', 'shooting_lon', 'shooting_azimuth',
            'shooting_lat_write', 'shooting_lon_write', 'shooting_azimuth_write'
        ]
        read_only_fields = ['owner', 'status', 'created_at', 'location_name', 'owner_username', 'status_name']

    def get_shooting_lat(self, obj):
        if obj.shooting_point:
            return obj.shooting_point.y
        if obj.location and obj.location.coordinates:
            return obj.location.coordinates.y
        return None

    def get_shooting_lon(self, obj):
        if obj.shooting_point:
            return obj.shooting_point.x
        if obj.location and obj.location.coordinates:
            return obj.location.coordinates.x
        return None

    def get_shooting_azimuth(self, obj):
        if obj.shooting_azimuth is not None:
            return obj.shooting_azimuth
        return obj.azimuth

    def create(self, validated_data):
        shooting_lat = validated_data.pop('shooting_lat_write', None)
        shooting_lon = validated_data.pop('shooting_lon_write', None)
        shooting_azimuth = validated_data.pop('shooting_azimuth_write', None)
        
        photo = super().create(validated_data)
        
        if shooting_lat is not None and shooting_lon is not None:
            photo.shooting_point = Point(shooting_lon, shooting_lat, srid=4326)
            if shooting_azimuth is not None:
                photo.shooting_azimuth = shooting_azimuth
            photo.save(update_fields=['shooting_point', 'shooting_azimuth'])
        
        return photo

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