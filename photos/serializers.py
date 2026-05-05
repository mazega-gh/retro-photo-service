# photos/serializers.py
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