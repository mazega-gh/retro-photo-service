from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from .models import ModerationStatus, ModerationLog
from photos.models import RetroPhoto
# Импортируем сериализатор фото, чтобы получить URL картинки
from photos.serializers import RetroPhotoSerializer 
from accounts.views import IsAdminUser
from .serializers import ModerationStatusSerializer, ModerationLogSerializer


def is_moderator_or_admin(user):
    return user.is_authenticated and (user.is_moderator or user.is_admin)

@user_passes_test(is_moderator_or_admin)
def moderation_page(request):
    return render(request, 'moderation.html')


class ModerationPhotosAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_moderator or request.user.is_admin):
            return Response({'error': 'Доступ запрещён'}, status=403)
        
        # Получаем статус "На проверке"
        try:
            pending_status = ModerationStatus.objects.get(name="На проверке")
        except ModerationStatus.DoesNotExist:
            return Response([])
            
        photos = RetroPhoto.objects.filter(status=pending_status).select_related('location', 'owner')
        serializer = RetroPhotoSerializer(photos, many=True)
        return Response(serializer.data)


class ApprovePhotoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not (request.user.is_moderator or request.user.is_admin):
            return Response({'error': 'Доступ запрещён'}, status=403)
        try:
            photo = RetroPhoto.objects.get(pk=pk, status__name="На проверке")
        except RetroPhoto.DoesNotExist:
            return Response({'error': 'Фото не найдено или уже обработано'}, status=404)

        approved_status = ModerationStatus.objects.get(name="Опубликовано")
        photo.status = approved_status
        photo.save()

        comment = request.data.get('comment', '')
        ModerationLog.objects.create(
            photo=photo,
            moderator=request.user,
            comment=comment or 'Одобрено'
        )
        return Response({'status': 'approved'})


class RejectPhotoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not (request.user.is_moderator or request.user.is_admin):
            return Response({'error': 'Доступ запрещён'}, status=403)
        try:
            photo = RetroPhoto.objects.get(pk=pk, status__name="На проверке")
        except RetroPhoto.DoesNotExist:
            return Response({'error': 'Фото не найдено или уже обработано'}, status=404)

        rejected_status = ModerationStatus.objects.get(name="Отклонено")
        photo.status = rejected_status
        photo.save()

        comment = request.data.get('comment', '')
        ModerationLog.objects.create(
            photo=photo,
            moderator=request.user,
            comment=comment or 'Отклонено'
        )
        return Response({'status': 'rejected'})


# === НОВЫЙ КЛАСС ДЛЯ ЖУРНАЛА МОДЕРАЦИИ ===
class ModerationLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_moderator or request.user.is_admin):
            return Response({'error': 'Доступ запрещён'}, status=403)
        
        # Берем последние 100 записей, сортируем по дате проверки
        logs = ModerationLog.objects.select_related('photo', 'moderator', 'photo__location').order_by('-review_date')[:100]
        
        data = []
        for log in logs:
            photo = log.photo
            # Формируем ответ вручную, чтобы фронтенду было удобно
            data.append({
                'id': log.id,
                'image': photo.image.url if photo.image else '',
                'location_name': photo.location.name if photo.location else 'Неизвестно',
                'year': photo.year,
                'action': 'approved' if 'Опубликовано' in str(photo.status) else 'rejected',
                'moderator': log.moderator.username if log.moderator else 'Система',
                'reviewed_at': log.review_date.isoformat(),
                'comment': log.comment
            })
            
        return Response(data)


# ViewSets для админ-панели (оставляем как было)
class AdminModerationStatusViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = ModerationStatus.objects.all()
    serializer_class = ModerationStatusSerializer


class AdminModerationLogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = ModerationLog.objects.all()
    serializer_class = ModerationLogSerializer