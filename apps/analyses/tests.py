from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from produits.models import Produit, Categorie
from magasins.models import Magasin, Enseigne, Ville, Region
from prix.models import Prix
from .models import AnalysePrix, RapportAnalyse, AnalysisResult, PriceAggregate
from .utils import OptimiseurRequetes, CalculateurMetriques

User = get_user_model()

class AnalysePrixModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.categorie = Categorie.objects.create(nom='Test Catégorie')
        self.enseigne = Enseigne.objects.create(nom='Test Enseigne')
        self.ville = Ville.objects.create(nom='Test Ville', code_postal='12345')
        self.region = Region.objects.create(nom='Test Région', code='TEST')
        self.magasin = Magasin.objects.create(
            nom='Test Magasin', 
            enseigne=self.enseigne,
            ville=self.ville
        )
        self.produit = Produit.objects.create(
            nom='Test Produit',
            categorie=self.categorie,
            marque='Test Marque'
        )
    
    def test_creation_analyse_prix(self):
        analyse = AnalysePrix.objects.create(
            utilisateur=self.user,
            type_analyse='comparaison_enseigne',
            titre='Test Analyse',
            description='Description test',
            date_debut_periode=timezone.now().date(),
            date_fin_periode=timezone.now().date()
        )
        self.assertEqual(analyse.titre, 'Test Analyse')
        self.assertEqual(analyse.utilisateur, self.user)

class AnalysisResultModelTest(TestCase):
    def test_creation_analysis_result(self):
        result = AnalysisResult.objects.create(
            type='tendance',
            nom='Test Tendance',
            donnees={'test': 'data'}
        )
        self.assertEqual(result.type, 'tendance')
        self.assertEqual(result.nom, 'Test Tendance')

class OptimiseurRequetesTest(TestCase):
    def setUp(self):
        self.optimiseur = OptimiseurRequetes()
    
    def test_executer_comparaison_enseignes(self):
        # Test avec des paramètres de base
        resultat = self.optimiseur.executer_comparaison_enseignes(1, '2023-01-01', '2023-12-31')
        self.assertIn('resultats', resultat)
        self.assertIn('metriques', resultat)

class CalculateurMetriquesTest(TestCase):
    def test_calculer_statistiques_prix(self):
        # Test avec des données simulées
        class MockPrix:
            def __init__(self, prix):
                self.prix = prix
        
        mock_queryset = [MockPrix(10), MockPrix(20), MockPrix(30)]
        stats = CalculateurMetriques.calculer_statistiques_prix(mock_queryset)
        
        self.assertEqual(stats['moyenne'], 20)
        self.assertEqual(stats['minimum'], 10)
        self.assertEqual(stats['maximum'], 30)

class AnalysePrixViewSetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.force_login(self.user)
    
    def test_list_analyses(self):
        response = self.client.get('/api/analyses/')
        self.assertEqual(response.status_code, 200)