from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Utilisateur, ProfilUtilisateur, Abonnement, HistoriqueRemises
from .services import ServiceFidelite
from .utils import CalculateurRemise, ValidateurUtilisateur

class ModelUtilisateurTests(TestCase):
    
    def setUp(self):
        self.utilisateur = Utilisateur.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_creation_utilisateur(self):
        """Test de la création d'un utilisateur"""
        self.assertEqual(self.utilisateur.username, 'testuser')
        self.assertTrue(self.utilisateur.check_password('testpass123'))
        self.assertEqual(self.utilisateur.niveau_fidelite, 1)
        self.assertEqual(self.utilisateur.points_fidelite, 0)
    
    def test_est_client_fidele(self):
        """Test de la propriété est_client_fidele"""
        # Niveau 2 - pas fidèle
        self.utilisateur.niveau_fidelite = 2
        self.utilisateur.nombre_commandes = 10
        self.assertFalse(self.utilisateur.est_client_fidele)
        
        # Niveau 3 avec assez de commandes - fidèle
        self.utilisateur.niveau_fidelite = 3
        self.assertTrue(self.utilisateur.est_client_fidele)
        
        # Niveau 3 mais pas assez de commandes - pas fidèle
        self.utilisateur.nombre_commandes = 2
        self.assertFalse(self.utilisateur.est_client_fidele)
    
    def test_ajouter_points_fidelite(self):
        """Test de l'ajout de points de fidélité"""
        points_initiaux = self.utilisateur.points_fidelite
        
        self.utilisateur.ajouter_points_fidelite(100, Decimal('50.00'))
        
        self.assertEqual(self.utilisateur.points_fidelite, points_initiaux + 100)
        self.assertEqual(self.utilisateur.total_achats, Decimal('50.00'))
        self.assertEqual(self.utilisateur.nombre_commandes, 1)
    
    def test_appliquer_remise_fidelite(self):
        """Test de l'application de remise fidélité"""
        prix_original = Decimal('100.00')
        
        # Niveau 1 - pas de remise
        prix_remise, montant_remise = self.utilisateur.appliquer_remise_fidelite(prix_original)
        self.assertEqual(prix_remise, prix_original)
        self.assertEqual(montant_remise, Decimal('0.00'))
        
        # Niveau 3 - remise de 5%
        self.utilisateur.niveau_fidelite = 3
        prix_remise, montant_remise = self.utilisateur.appliquer_remise_fidelite(prix_original)
        self.assertEqual(prix_remise, Decimal('95.00'))
        self.assertEqual(montant_remise, Decimal('5.00'))

class ServiceFideliteTests(TestCase):
    
    def test_calculer_points_achat(self):
        """Test du calcul des points d'achat"""
        points = ServiceFidelite.calculer_points_achat(Decimal('75.50'))
        self.assertEqual(points, 75)  # 75.50 arrondi à l'entier inférieur
    
    def test_calculer_niveau_fidelite(self):
        """Test du calcul du niveau de fidélité"""
        self.assertEqual(ServiceFidelite.calculer_niveau_fidelite(Decimal('0')), 1)
        self.assertEqual(ServiceFidelite.calculer_niveau_fidelite(Decimal('25')), 1)
        self.assertEqual(ServiceFidelite.calculer_niveau_fidelite(Decimal('50')), 2)
        self.assertEqual(ServiceFidelite.calculer_niveau_fidelite(Decimal('200')), 3)
        self.assertEqual(ServiceFidelite.calculer_niveau_fidelite(Decimal('500')), 4)
        self.assertEqual(ServiceFidelite.calculer_niveau_fidelite(Decimal('1000')), 5)
    
    def test_appliquer_remise_utilisateur(self):
        """Test de l'application de remise utilisateur"""
        from .models import Utilisateur
        
        utilisateur = Utilisateur.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        utilisateur.niveau_fidelite = 3  # 5% de remise
        
        prix_original = Decimal('100.00')
        prix_remise, montant_remise, pourcentage = ServiceFidelite.appliquer_remise_utilisateur(
            utilisateur, prix_original
        )
        
        self.assertEqual(pourcentage, 5)
        self.assertEqual(prix_remise, Decimal('95.00'))
        self.assertEqual(montant_remise, Decimal('5.00'))

class UtilisateurAPITests(APITestCase):
    
    def setUp(self):
        self.utilisateur_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'Testpass123',
            'password_confirmation': 'Testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.utilisateur = Utilisateur.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )
    
    def test_inscription_utilisateur(self):
        """Test de l'inscription via API"""
        url = reverse('utilisateurs-inscrire')
        response = self.client.post(url, self.utilisateur_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertEqual(Utilisateur.objects.count(), 2)
    
    def test_connexion_utilisateur(self):
        """Test de la connexion via API"""
        url = reverse('utilisateurs-connecter')
        data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_statistiques_fidelite(self):
        """Test des statistiques de fidélité"""
        self.client.force_authenticate(user=self.utilisateur)
        url = reverse('statistiques-fidelite')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('points_fidelite', response.data)
        self.assertIn('niveau_fidelite', response.data)

class UtilsTests(TestCase):
    
    def test_calculateur_remise(self):
        """Test du calculateur de remise"""
        prix_original = Decimal('100.00')
        
        # Remise de 10%
        prix_remise, montant_remise = CalculateurRemise.calculer_remise(prix_original, 10)
        self.assertEqual(prix_remise, Decimal('90.00'))
        self.assertEqual(montant_remise, Decimal('10.00'))
        
        # Calcul pourcentage
        pourcentage = CalculateurRemise.calculer_pourcentage_remise(prix_original, Decimal('90.00'))
        self.assertEqual(pourcentage, Decimal('10.00'))
    
    def test_validateur_utilisateur(self):
        """Test du validateur utilisateur"""
        # Validation email
        self.assertTrue(ValidateurUtilisateur.valider_email('test@example.com'))
        self.assertFalse(ValidateurUtilisateur.valider_email('invalid-email'))
        
        # Validation téléphone
        self.assertTrue(ValidateurUtilisateur.valider_telephone('+33123456789'))
        self.assertFalse(ValidateurUtilisateur.valider_telephone('invalid'))
        
        # Validation mot de passe
        est_valide, erreurs = ValidateurUtilisateur.valider_mot_de_passe('StrongPass123')
        self.assertTrue(est_valide)
        self.assertEqual(len(erreurs), 0)

class SignalTests(TestCase):
    
    def test_creation_profil_automatique(self):
        """Test de la création automatique du profil"""
        utilisateur = Utilisateur.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Vérifier que le profil a été créé automatiquement
        self.assertTrue(hasattr(utilisateur, 'profil'))
        self.assertIsNotNone(utilisateur.profil)
    
    def test_creation_abonnement_automatique(self):
        """Test de la création automatique de l'abonnement"""
        utilisateur = Utilisateur.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Vérifier que l'abonnement a été créé automatiquement
        self.assertTrue(hasattr(utilisateur, 'abonnement'))
        self.assertIsNotNone(utilisateur.abonnement)
        self.assertTrue(utilisateur.abonnement.est_valide)