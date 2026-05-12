from rest_framework import filters, permissions, serializers, viewsets

from accounts.views import IsAdminUser
from moderation.models import ModerationLog, ModerationStatus

from .models import RetroPhoto
from .serializers import RetroPhotoSerializer


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


class AdminRetroPhotoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = RetroPhoto.objects.select_related('location', 'owner', 'status')
    serializer_class = RetroPhotoSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
