from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from .models import HistoriqueRecommandation, ModeleML
from apps.produits.models import Produit, Categorie
from .modeles_ml import ModeleRecommandationContenu, GestionnaireRecommandations

User = get_user_model()

class ModeleRecommandationContenuTests(TestCase):
    def setUp(self):
        self.modele = ModeleRecommandationContenu()
        self.donnees_test = [
            {
                'id': 1,
                'nom': 'Laptop Gaming ASUS',
                'categorie': 'Informatique',
                'marque': 'ASUS',
                'description': 'Laptop gaming puissant avec RTX 3080'
            },
            {
                'id': 2,
                'nom': 'Laptop Dell Professionnel',
                'categorie': 'Informatique',
                'marque': 'Dell',
                'description': 'Laptop professionnel pour le travail'
            }
        ]
    
    def test_entrainement_modele(self):
        """Test l'entraînement du modèle"""
        self.modele.entrainer(self.donnees_test)
        self.assertTrue(self.modele.est_entraine)
    
    def test_recommandation(self):
        """Test la génération de recommandations"""
        self.modele.entrainer(self.donnees_test)
        recommandations = self.modele.recommander(1, n_recommandations=1)
        self.assertEqual(len(recommandations), 1)
        self.assertIn('produit', recommandations[0])
        self.assertIn('score_similarite', recommandations[0])

class GestionnaireRecommandationsTests(TestCase):
    def setUp(self):
        self.gestionnaire = GestionnaireRecommandations()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        
        # Créer des produits de test
        self.categorie = Categorie.objects.create(nom='Informatique')
        self.produit1 = Produit.objects.create(
            nom='Laptop ASUS',
            categorie=self.categorie,
            marque='ASUS',
            description='Laptop gaming'
        )
        self.produit2 = Produit.objects.create(
            nom='Laptop Dell',
            categorie=self.categorie,
            marque='Dell',
            description='Laptop professionnel'
        )
    
    def test_recommandations_produit(self):
        """Test les recommandations par produit"""
        recommandations = self.gestionnaire.get_recommandations_produit(
            self.produit1.id, 
            n_recommandations=1
        )
        # Le modèle n'étant pas entraîné, devrait retourner des populaires
        self.assertTrue(isinstance(recommandations, list))

class RecommandationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.force_authenticate(user=self.user)
    
    def test_recommandations_utilisateur(self):
        """Test l'API de recommandations utilisateur"""
        response = self.client.get('/api/recommandations/pour_moi/?n_recommandations=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(isinstance(response.data, list))
    
    def test_statut_modeles(self):
        """Test l'endpoint de statut des modèles"""
        response = self.client.get('/api/statut-modeles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('modele_contenu_entraine', response.data)

class ModelTests(TestCase):
    def test_creation_historique(self):
        """Test la création d'un historique de recommandation"""
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        categorie = Categorie.objects.create(nom='Test')
        produit = Produit.objects.create(
            nom='Produit Test',
            categorie=categorie,
            marque='Test'
        )
        
        historique = HistoriqueRecommandation.objects.create(
            utilisateur=user,
            produit_recommande=produit,
            score_confiance=0.85,
            algorithme_utilise='contenu'
        )
        
        self.assertEqual(historique.utilisateur, user)
        self.assertEqual(historique.produit_recommande, produit)
        self.assertTrue(historique.score_confiance > 0)