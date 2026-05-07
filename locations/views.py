# locations/views.py
from rest_framework import viewsets, filters, generics, permissions
from .models import Location, LocationType
from .serializers import LocationSerializer, LocationTypeSerializer, AdminLocationSerializer
from accounts.views import IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D

class LocationViewSet(viewsets.ModelViewSet):
    """
    API для получения списка локаций и создания новых.
    Создавать могут только авторизованные пользователи (IsAuthenticatedOrReadOnly).
    """
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

class AdminLocationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = Location.objects.all()
    serializer_class = AdminLocationSerializer

class AdminLocationTypeViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = LocationType.objects.all()
    serializer_class = LocationTypeSerializer

class AdminLocationTypeListView(generics.ListAPIView):
    """Список типов локаций для админки (для выпадающих списков)."""
    permission_classes = [IsAdminUser]
    queryset = LocationType.objects.all()
    serializer_class = LocationTypeSerializer

class CheckLocationView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    def get(self, request):
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        if not lat or not lng:
            return Response({'error': 'lat/lng required'}, status=400)
        point = Point(float(lng), float(lat), srid=4326)
        nearby = Location.objects.filter(coordinates__distance_lte=(point, D(m=50)))
        # Убираем дубликаты по имени
        unique_names = []
        seen = set()
        for loc in nearby:
            if loc.name not in seen:
                seen.add(loc.name)
                unique_names.append({'id': loc.id, 'name': loc.name})
        return Response({'nearby': unique_names})