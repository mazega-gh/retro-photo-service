from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from PIL import Image, ImageDraw
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

    def patterned_image(self, name, variant):
        image = Image.new('RGB', (96, 96), 'white')
        draw = ImageDraw.Draw(image)

        if variant == 'vertical':
            draw.rectangle((40, 0, 56, 96), fill='black')
            draw.rectangle((0, 68, 96, 82), fill=(180, 180, 180))
        elif variant == 'vertical_shifted':
            draw.rectangle((42, 0, 58, 96), fill='black')
            draw.rectangle((0, 66, 96, 80), fill=(180, 180, 180))
        elif variant == 'diagonal':
            draw.line((0, 95, 95, 0), fill='black', width=12)
            draw.rectangle((0, 0, 96, 16), fill=(90, 90, 90))
        else:
            draw.ellipse((18, 18, 78, 78), fill='black')

        buffer = BytesIO()
        image.save(buffer, format='PNG')
        return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')

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

    def test_smart_compare_selects_best_visual_match_across_all_pairs(self):
        very_old_unmatched = RetroPhoto.objects.create(
            image=self.patterned_image('unmatched-old.png', 'diagonal'),
            year=1800,
            azimuth=220,
            location=self.location,
            owner=self.user,
            status=self.published,
        )
        old_match = RetroPhoto.objects.create(
            image=self.patterned_image('match-old.png', 'vertical'),
            year=1900,
            azimuth=15,
            location=self.location,
            owner=self.user,
            status=self.published,
        )
        new_match = RetroPhoto.objects.create(
            image=self.patterned_image('match-new.png', 'vertical_shifted'),
            year=2020,
            azimuth=18,
            location=self.location,
            owner=self.user,
            status=self.published,
        )
        RetroPhoto.objects.create(
            image=self.patterned_image('newest-unmatched.png', 'circle'),
            year=2025,
            azimuth=260,
            location=self.location,
            owner=self.user,
            status=self.published,
        )

        response = self.client.get(f'/api/photos/smart-compare/?location={self.location.id}')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['old_photo']['id'], old_match.id)
        self.assertEqual(response.data['new_photo']['id'], new_match.id)
        self.assertNotEqual(response.data['old_photo']['id'], very_old_unmatched.id)
        self.assertEqual(response.data['metrics']['candidates_analyzed'], 6)
        self.assertGreater(response.data['metrics']['visual_similarity'], 80)
