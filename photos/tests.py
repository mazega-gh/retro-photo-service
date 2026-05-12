from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from locations.models import Location
from moderation.models import ModerationStatus

from .models import RetroPhoto


PNG_1X1 = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
    b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
    b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
    b'\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)


class RetroPhotoApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username='user', password='pass')
        self.location = Location.objects.create(
            name='Test location',
            coordinates=Point(39.8737, 57.6299, srid=4326),
        )
        self.pending, _ = ModerationStatus.objects.get_or_create(name='На проверке')
        self.published, _ = ModerationStatus.objects.get_or_create(name='Опубликовано')

    def image(self, name='photo.png'):
        return SimpleUploadedFile(name, PNG_1X1, content_type='image/png')

    def test_uploaded_photo_is_waiting_for_moderation(self):
        self.client.force_authenticate(self.user)

        response = self.client.post('/api/photos/', {
            'image': self.image(),
            'year': 1950,
            'description': 'Archive view',
            'location': self.location.id,
        }, format='multipart')

        self.assertEqual(response.status_code, 201)
        photo = RetroPhoto.objects.get()
        self.assertEqual(photo.owner, self.user)
        self.assertEqual(photo.status.name, 'На проверке')

    def test_public_list_contains_only_published_photos(self):
        RetroPhoto.objects.create(
            image=self.image('published.png'),
            year=1950,
            location=self.location,
            owner=self.user,
            status=self.published,
        )
        RetroPhoto.objects.create(
            image=self.image('pending.png'),
            year=1960,
            location=self.location,
            owner=self.user,
            status=self.pending,
        )

        response = self.client.get('/api/photos/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['year'], 1950)

    def test_rejects_invalid_year_and_azimuth(self):
        self.client.force_authenticate(self.user)

        response = self.client.post('/api/photos/', {
            'image': self.image(),
            'year': 1700,
            'azimuth': 361,
            'location': self.location.id,
        }, format='multipart')

        self.assertEqual(response.status_code, 400)
        self.assertIn('year', response.data)
        self.assertIn('azimuth', response.data)
