from django.urls import reverse
from django.test import override_settings
from django.core import mail
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class AuthApiTests(APITestCase):
    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        USE_JWT_AUTH=False,
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'rest_framework.authentication.SessionAuthentication',
            ),
            'DEFAULT_PERMISSION_CLASSES': (
                'rest_framework.permissions.AllowAny',
            ),
            'DEFAULT_THROTTLE_CLASSES': (
                'rest_framework.throttling.AnonRateThrottle',
            ),
            'DEFAULT_THROTTLE_RATES': {
                'register': '10/min',
                'activate': '10/min',
                'login': '10/min',
            },
        }
    )
    def test_register_sends_activation_email(self):
        url = reverse('utilisateurs:auth-register')
        payload = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'passdemo123',
            'password_confirmation': 'passdemo123',
        }
        resp = self.client.post(url, payload, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertGreaterEqual(len(mail.outbox), 1)
        self.assertIn('Activation', mail.outbox[0].subject)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_CLASSES': (
                'rest_framework.throttling.AnonRateThrottle',
            ),
            'DEFAULT_THROTTLE_RATES': {
                'register': '10/min',
                'activate': '10/min',
                'login': '10/min',
            },
        }
    )
    def test_activation_invalid(self):
        url = reverse('utilisateurs:auth-activate')
        resp = self.client.get(url, {'uid': 'invalid', 'token': 'invalid'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(
        USE_JWT_AUTH=False,
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_CLASSES': (
                'rest_framework.throttling.AnonRateThrottle',
            ),
            'DEFAULT_THROTTLE_RATES': {
                'register': '10/min',
                'activate': '10/min',
                'login': '10/min',
            },
        }
    )
    def test_login_blocked_until_activation(self):
        User.objects.create_user(username='u1', email='u1@example.com', password='passdemo123', is_active=False)
        url = reverse('utilisateurs:auth-login')
        resp = self.client.post(url, {'identifiant': 'u1', 'password': 'passdemo123'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('activer votre compte', str(resp.data))

    @override_settings(
        USE_JWT_AUTH=False,
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_CLASSES': (
                'rest_framework.throttling.AnonRateThrottle',
            ),
            'DEFAULT_THROTTLE_RATES': {
                'register': '10/min',
                'activate': '10/min',
                'login': '10/min',
            },
        }
    )
    def test_login_ok_after_activation(self):
        User.objects.create_user(username='u2', email='u2@example.com', password='passdemo123', is_active=True)
        url = reverse('utilisateurs:auth-login')
        resp = self.client.post(url, {'identifiant': 'u2@example.com', 'password': 'passdemo123'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('utilisateur', resp.data)

    @override_settings(
        USE_JWT_AUTH=False,
        REST_FRAMEWORK={
            'DEFAULT_THROTTLE_CLASSES': (
                'rest_framework.throttling.AnonRateThrottle',
            ),
            'DEFAULT_THROTTLE_RATES': {
                'register': '10/min',
                'activate': '10/min',
                'login': '2/min',
            },
        }
    )
    def test_login_ratelimit(self):
        User.objects.create_user(username='u3', email='u3@example.com', password='passdemo123', is_active=True)
        url = reverse('utilisateurs:auth-login')
        for _ in range(2):
            r = self.client.post(url, {'identifiant': 'u3', 'password': 'passdemo123'}, format='json')
            self.assertEqual(r.status_code, status.HTTP_200_OK)
        # 3ème appel devrait être throttled (429)
        r3 = self.client.post(url, {'identifiant': 'u3', 'password': 'passdemo123'}, format='json')
        self.assertEqual(r3.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
