from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Location, LocationType
from rest_framework_gis.fields import GeometryField

class LocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationType
        fields = ['id', 'name', 'icon_marker']


class LocationSerializer(GeoFeatureModelSerializer):
    location_type_name = serializers.ReadOnlyField(source='location_type.name', allow_null=True)
    location_type = serializers.PrimaryKeyRelatedField(
        queryset=LocationType.objects.all(),
        required=False,
        allow_null=True
    )
    oldest_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Location
        geo_field = "coordinates"
        auto_bbox = True
        fields = ['id', 'name', 'location_type', 'location_type_name', 'oldest_photo_url', 'is_approved']

    def get_oldest_photo_url(self, obj):
        # Ищем самую старую ОПУБЛИКОВАННУЮ фотографию для этой локации
        oldest = obj.photos.filter(status__name='Опубликовано').order_by('year').first()
        if oldest and oldest.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(oldest.image.url)
            return oldest.image.url
        return None


class AdminLocationSerializer(serializers.ModelSerializer):
    coordinates = GeometryField()

    class Meta:
        model = Location
        fields = ['id', 'name', 'coordinates', 'location_type', 'created_at']
        read_only_fields = ['created_at']