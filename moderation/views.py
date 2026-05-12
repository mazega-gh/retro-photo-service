from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.views import IsAdminUser
from photos.models import RetroPhoto
from photos.serializers import RetroPhotoSerializer

from .models import ModerationLog, ModerationStatus
from .serializers import ModerationLogSerializer, ModerationStatusSerializer


PENDING_STATUS = 'На проверке'
PUBLISHED_STATUS = 'Опубликовано'
REJECTED_STATUS = 'Отклонено'


def is_moderator_or_admin(user):
    return user.is_authenticated and (user.is_moderator or user.is_admin)


def get_or_create_status(name):
    status_obj, _ = ModerationStatus.objects.get_or_create(name=name)
    return status_obj


@user_passes_test(is_moderator_or_admin)
def moderation_page(request):
    return render(request, 'moderation.html')


class ModerationPhotosAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_moderator_or_admin(request.user):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        pending_status = get_or_create_status(PENDING_STATUS)
        photos = RetroPhoto.objects.filter(status=pending_status).select_related('location', 'owner', 'status')
        serializer = RetroPhotoSerializer(photos, many=True)
        return Response(serializer.data)


class ApprovePhotoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not is_moderator_or_admin(request.user):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        pending_status = get_or_create_status(PENDING_STATUS)
        try:
            photo = RetroPhoto.objects.get(pk=pk, status=pending_status)
        except RetroPhoto.DoesNotExist:
            return Response({'error': 'Photo not found or already moderated'}, status=status.HTTP_404_NOT_FOUND)

        photo.status = get_or_create_status(PUBLISHED_STATUS)
        photo.save(update_fields=['status', 'updated_at'])

        comment = request.data.get('comment', '')
        ModerationLog.objects.create(
            photo=photo,
            moderator=request.user,
            action='approved',
            comment=comment or 'Approved',
        )
        return Response({'status': 'approved'})


class RejectPhotoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not is_moderator_or_admin(request.user):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        pending_status = get_or_create_status(PENDING_STATUS)
        try:
            photo = RetroPhoto.objects.get(pk=pk, status=pending_status)
        except RetroPhoto.DoesNotExist:
            return Response({'error': 'Photo not found or already moderated'}, status=status.HTTP_404_NOT_FOUND)

        photo.status = get_or_create_status(REJECTED_STATUS)
        photo.save(update_fields=['status', 'updated_at'])

        comment = request.data.get('comment', '')
        ModerationLog.objects.create(
            photo=photo,
            moderator=request.user,
            action='rejected',
            comment=comment or 'Rejected',
        )
        return Response({'status': 'rejected'})


class ModerationLogAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_moderator_or_admin(request.user):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        logs = ModerationLog.objects.select_related('photo', 'moderator', 'photo__location').order_by('-review_date')[:100]
        data = []
        for log in logs:
            photo = log.photo
            data.append({
                'id': log.id,
                'image': photo.image.url if photo.image else '',
                'location_name': photo.location.name if photo.location else 'Unknown',
                'year': photo.year,
                'action': log.action or 'updated',
                'moderator': log.moderator.username if log.moderator else 'System',
                'reviewed_at': log.review_date.isoformat(),
                'comment': log.comment,
            })

        return Response(data)


class AdminModerationStatusViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = ModerationStatus.objects.all()
    serializer_class = ModerationStatusSerializer


class AdminModerationLogViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUser]
    queryset = ModerationLog.objects.select_related('photo', 'moderator')
    serializer_class = ModerationLogSerializer
