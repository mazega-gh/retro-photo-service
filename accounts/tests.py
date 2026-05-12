from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Role


class AccountApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        Role.objects.get_or_create(name='user')

    def test_register_creates_user_with_default_role(self):
        response = self.client.post('/api/register/', {
            'username': 'new-user',
            'email': 'new@example.com',
            'password': 'StrongPass123',
            'password2': 'StrongPass123',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username='new-user')
        self.assertEqual(user.role.name, 'user')

    def test_login_rejects_wrong_password(self):
        get_user_model().objects.create_user(username='user', password='right-password')

        response = self.client.post('/api/login/', {
            'username': 'user',
            'password': 'wrong-password',
        }, format='json')

        self.assertEqual(response.status_code, 401)
