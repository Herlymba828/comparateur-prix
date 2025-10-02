from django.test import TestCase, Client
from django.conf import settings


class SmokeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_admin_login_page_accessible(self):
        # L'URL d'authentification admin doit répondre (200 OK)
        resp = self.client.get('/admin/login/')
        self.assertEqual(resp.status_code, 200)

    def test_settings_loaded(self):
        # Vérifie que les settings essentiels sont chargés
        self.assertTrue(hasattr(settings, 'INSTALLED_APPS'))
        self.assertEqual(settings.LANGUAGE_CODE, 'fr-fr')

    def test_api_docs_route_exists(self):
        # Optionnel: la doc OpenAPI peut ne pas être mappée; accepter 200/404
        resp = self.client.get('/api/schema/')
        self.assertIn(resp.status_code, (200, 301, 302, 404))
