# locations/serializers.py
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import Location, LocationType


class LocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationType
        fields = ['id', 'name', 'icon_marker']


class LocationSerializer(GeoFeatureModelSerializer):
    """
    Сериализатор для локаций в формате GeoJSON.
    Наследуется от GeoFeatureModelSerializer, чтобы автоматически формировать структуру:
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": { "type": "Point", "coordinates": [lon, lat] },
          "properties": { "id": 1, "name": "...", ... }
        }
      ]
    }
    """
    location_type_name = serializers.CharField(source='location_type.name', read_only=True)

    class Meta:
        model = Location
        geo_field = "coordinates"  # Указываем поле с геометрией
        auto_bbox = True           # Автоматически добавлять bounding box (опционально)
        fields = ['id', 'name', 'location_type', 'location_type_name']