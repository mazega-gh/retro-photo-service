from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role
from locations.models import Location
from photos.models import RetroPhoto

from .models import ModerationLog, ModerationStatus


PNG_1X1 = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
    b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


class ModerationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username='user', password='pass')
        moderator_role, _ = Role.objects.get_or_create(name='moderator')
        self.moderator = get_user_model().objects.create_user(
            username='moderator',
            password='pass',
            role=moderator_role,
        )
        self.location = Location.objects.create(
            name='Test location',
            coordinates=Point(39.8737, 57.6299, srid=4326),
        )
        self.pending, _ = ModerationStatus.objects.get_or_create(name='На проверке')
        ModerationStatus.objects.get_or_create(name='Опубликовано')
        ModerationStatus.objects.get_or_create(name='Отклонено')
        self.photo = RetroPhoto.objects.create(
            image=SimpleUploadedFile('photo.png', PNG_1X1, content_type='image/png'),
            year=1950,
            location=self.location,
            owner=self.user,
            status=self.pending,
        )

    def test_moderator_can_approve_photo(self):
        self.client.force_authenticate(self.moderator)

        response = self.client.post(f'/api/moderation/photos/{self.photo.id}/approve/', {
            'comment': 'Looks good',
        }, format='json')

        self.assertEqual(response.status_code, 200)
        self.photo.refresh_from_db()
        self.assertEqual(self.photo.status.name, 'Опубликовано')
        self.assertTrue(ModerationLog.objects.filter(photo=self.photo, action='approved').exists())

    def test_regular_user_cannot_moderate(self):
        self.client.force_authenticate(self.user)

        response = self.client.post(f'/api/moderation/photos/{self.photo.id}/reject/', {
            'comment': 'No',
        }, format='json')

        self.assertEqual(response.status_code, 403)
