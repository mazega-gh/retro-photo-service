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
    serializer_class = LocationSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Публично видны только одобренные локации
        return Location.objects.filter(is_approved=True)

    def perform_create(self, serializer):
        # Созданная пользователем локация становится неодобренной
        serializer.save(is_approved=False)

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
    
class ModerationLocationsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not (request.user.is_moderator or request.user.is_admin):
            return Response({'error': 'Access denied'}, status=403)
        pending_locations = Location.objects.filter(is_approved=False)
        serializer = AdminLocationSerializer(pending_locations, many=True, context={'request': request})
        return Response({
            'results': serializer.data,
            'stats': {
                'total': Location.objects.count(),
                'pending': pending_locations.count(),
                'approved': Location.objects.filter(is_approved=True).count(),
            },
        })


class ApproveLocationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not (request.user.is_moderator or request.user.is_admin):
            return Response({'error': 'Access denied'}, status=403)
        try:
            location = Location.objects.get(pk=pk, is_approved=False)
        except Location.DoesNotExist:
            return Response({'error': 'Location not found'}, status=404)
        location.is_approved = True
        location.save(update_fields=['is_approved'])
        return Response({'status': 'approved'})

class RejectLocationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        if not (request.user.is_moderator or request.user.is_admin):
            return Response({'error': 'Access denied'}, status=403)
        try:
            location = Location.objects.get(pk=pk, is_approved=False)
        except Location.DoesNotExist:
            return Response({'error': 'Location not found'}, status=404)
        location.delete()
        return Response({'status': 'rejected'})
