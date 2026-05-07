# photos/views.py (заменить весь файл)
from rest_framework import viewsets, permissions, status, filters, serializers
from rest_framework.response import Response
from .models import RetroPhoto
from .serializers import RetroPhotoSerializer
from moderation.models import ModerationStatus, ModerationLog
from accounts.views import IsAdminUser


class RetroPhotoViewSet(viewsets.ModelViewSet):
    serializer_class = RetroPhotoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['description', 'year']
    ordering_fields = ['year', 'created_at']

    def get_queryset(self):
        qs = RetroPhoto.objects.select_related('location', 'owner', 'status')
        # Фильтр по location_id (GET-параметр ?location=ID)
        location_id = self.request.query_params.get('location')
        if location_id:
            qs = qs.filter(location_id=location_id)
        # Публичный доступ – только опубликованные
        try:
            published = ModerationStatus.objects.get(name="Опубликовано")
            qs = qs.filter(status=published)
        except ModerationStatus.DoesNotExist:
            qs = qs.none()
        return qs

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise serializers.ValidationError("Требуется авторизация")
        try:
            pending_status = ModerationStatus.objects.get(name="На проверке")
        except ModerationStatus.DoesNotExist:
            pending_status = ModerationStatus.objects.create(name="На проверке")
        photo = serializer.save(
            owner=self.request.user,
            status=pending_status
        )
        ModerationLog.objects.create(
            photo=photo,
            moderator=None,   # теперь допустимо благодаря null=True
            comment="Фото загружено и ожидает проверки."
        )

class AdminRetroPhotoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = RetroPhoto.objects.all()
    serializer_class = RetroPhotoSerializer

    def perform_create(self, serializer):
        # Автоматически назначаем текущего пользователя владельцем
        serializer.save(owner=self.request.user)