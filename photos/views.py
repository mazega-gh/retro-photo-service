from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.views import IsAdminUser
from moderation.models import ModerationLog, ModerationStatus

from .models import RetroPhoto
from .serializers import RetroPhotoSerializer
from .smart_matching import find_best_comparison_pair

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly


PENDING_STATUS = 'На проверке'
PUBLISHED_STATUS = 'Опубликовано'


def get_or_create_status(name):
    status, _ = ModerationStatus.objects.get_or_create(name=name)
    return status


class RetroPhotoViewSet(viewsets.ModelViewSet):
    serializer_class = RetroPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'year']
    ordering_fields = ['year', 'created_at']

    def get_queryset(self):
        qs = RetroPhoto.objects.select_related('location', 'owner', 'status')
        location_id = self.request.query_params.get('location')
        if location_id:
            qs = qs.filter(location_id=location_id)

        published = get_or_create_status(PUBLISHED_STATUS)
        return qs.filter(status=published)

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise serializers.ValidationError('Authorization is required.')

        pending_status = get_or_create_status(PENDING_STATUS)
        photo = serializer.save(owner=self.request.user, status=pending_status)
        ModerationLog.objects.create(
            photo=photo,
            moderator=None,
            action='uploaded',
            comment='Photo uploaded and waiting for moderation.',
        )

    @action(detail=False, methods=['get'], url_path='smart-compare')
    def smart_compare(self, request):
        location_id = request.query_params.get('location')
        if not location_id:
            return Response(
                {'detail': 'Location query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        photos = list(
            self.get_queryset()
            .filter(location_id=location_id)
            .order_by('year', 'id')
        )
        if len(photos) < 2:
            return Response(
                {'detail': 'At least two published photos are required for comparison.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        match = find_best_comparison_pair(photos)
        if not match:
            return Response(
                {'detail': 'Could not build a comparison pair.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer_context = self.get_serializer_context()
        return Response({
            'old_photo': RetroPhotoSerializer(match.old_photo, context=serializer_context).data,
            'new_photo': RetroPhotoSerializer(match.new_photo, context=serializer_context).data,
            'score': match.score,
            'quality_label': match.quality_label,
            'metrics': {
                'visual_similarity': match.visual_similarity,
                'temporal_score': match.temporal_score,
                'azimuth_score': match.azimuth_score,
                'candidates_analyzed': match.candidates_analyzed,
            },
            'algorithm': {
                'name': 'Intelligent historical photo matching',
                'features': [
                    'perceptual hashes',
                    'luminance grid',
                    'edge structure',
                    'color histogram',
                    'aspect ratio',
                    'shooting year',
                    'azimuth',
                ],
            },
        })


class AdminRetroPhotoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = RetroPhoto.objects.select_related('location', 'owner', 'status')
    serializer_class = RetroPhotoSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ShootingPointsView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        published_status = get_or_create_status(PUBLISHED_STATUS)
        photos = RetroPhoto.objects.filter(status=published_status).select_related('location')
        
        result = []
        for photo in photos:
            # Определяем координаты точки съёмки
            if photo.shooting_point:
                lat = photo.shooting_point.y
                lon = photo.shooting_point.x
            else:
                lat = photo.location.coordinates.y
                lon = photo.location.coordinates.x
            
            # Определяем азимут (сначала shooting_azimuth, потом azimuth)
            azimuth_value = photo.shooting_azimuth if photo.shooting_azimuth is not None else photo.azimuth
            
            result.append({
                'id': photo.id,
                'image': photo.image.url,
                'year': photo.year,
                'azimuth': photo.azimuth,
                'shooting_azimuth': azimuth_value,  # ← ДОБАВЬТЕ ЭТУ СТРОКУ
                'description': photo.description,
                'location_name': photo.location.name,
                'shooting_lat': lat,
                'shooting_lon': lon,
                'location_id': photo.location.id,
                'owner_username': photo.owner.username,
            })
        
        return Response(result)