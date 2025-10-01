from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from .models import Categorie, Produit
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from apps.produits.models import Produit, Categorie, UniteMesure
from apps.magasins.models import Magasin, Region, Ville
from .models import Prix, HistoriquePrix

class PrixModelTest(TestCase):
    def setUp(self):
        self.categorie = Categorie.objects.create(nom="Électronique", slug="electronique")
        self.unite = UniteMesure.objects.create(nom="Unité", symbole="u")

        # Ville / Magasin
        reg = Region.objects.create(nom="Estuaire")
        ville = Ville.objects.create(nom="Libreville", region=reg)
        self.magasin = Magasin.objects.create(nom="Supermarket Test", type="supermarche", ville=ville)

        # Produit (champs requis)
        self.produit = Produit.objects.create(
            code_barre="1234567890123",
            nom="Smartphone Samsung",
            slug="smartphone-samsung",
            categorie=self.categorie,
            unite_mesure=self.unite,
        )

        self.prix = Prix.objects.create(
            produit=self.produit,
            magasin=self.magasin,
            prix_actuel=Decimal("150000"),
            prix_origine=Decimal("180000"),
        )

    def test_creation_prix(self):
        self.assertEqual(self.prix.prix_actuel, Decimal("150000"))
        # Vérifier calcul de pourcentage si implémenté via méthode/propriété
        if hasattr(self.prix, 'get_pourcentage_promotion'):
            pct = self.prix.get_pourcentage_promotion()
            self.assertGreater(pct, 0)

    def test_historique_prix(self):
        h = HistoriquePrix.objects.create(
            prix=self.prix,
            ancien_prix=Decimal("180000"),
            nouveau_prix=Decimal("150000"),
            variation=Decimal("-30000"),
            pourcentage_variation=Decimal("-16.67"),
            raison='promotion',
        )
        self.assertEqual(h.nouveau_prix, Decimal("150000"))


class PrixAPITest(APITestCase):
    def setUp(self):
        self.categorie = Categorie.objects.create(nom="Alimentation", slug="alimentation")
        self.unite = UniteMesure.objects.create(nom="Litre", symbole="L")

        reg = Region.objects.create(nom="Estuaire")
        ville = Ville.objects.create(nom="Libreville", region=reg)
        self.magasin1 = Magasin.objects.create(nom="Carrefour", type="hypermarche", ville=ville)
        self.magasin2 = Magasin.objects.create(nom="Super U", type="supermarche", ville=ville)

        self.produit = Produit.objects.create(
            code_barre="0000000000001",
            nom="Lait Nestlé",
            slug="lait-nestle",
            categorie=self.categorie,
            unite_mesure=self.unite,
        )

        self.prix1 = Prix.objects.create(produit=self.produit, magasin=self.magasin1, prix_actuel=Decimal("1200"))
        self.prix2 = Prix.objects.create(produit=self.produit, magasin=self.magasin2, prix_actuel=Decimal("1100"))
    
    def test_liste_prix(self):
        response = self.client.get('/api/prix/prix/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Selon la config DRF/Router, la clé peut être 'results' si pagination
        data = response.data
        count = len(data['results']) if isinstance(data, dict) and 'results' in data else len(data)
        self.assertEqual(count, 2)

class ProduitModelTest(TestCase):
    def setUp(self):
        self.categorie = Categorie.objects.create(nom='Test Catégorie')
    
    def test_create_produit(self):
        produit = Produit.objects.create(
            nom='Test Produit',
            categorie=self.categorie,
            marque='Test Marque'
        )
        self.assertEqual(produit.nom, 'Test Produit')
        self.assertEqual(produit.categorie.nom, 'Test Catégorie')


class ProduitsViewsTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat1 = Categorie.objects.create(nom="Epicerie")
        self.cat2 = Categorie.objects.create(nom="Frais")
        self.p1 = Produit.objects.create(nom="Riz", categorie=self.cat1, marque="Marca", code_barre="12345678")
        self.p2 = Produit.objects.create(nom="Lait", categorie=self.cat2, marque="Lacto")

    def test_categories_list(self):
        url = reverse('categorie-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # DRF default list returns list or paginated; check presence
        self.assertTrue(resp.data)

    def test_produits_list_and_filter(self):
        url = reverse('produit-list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # Filter by categorie
        resp = self.client.get(url, {'categorie': self.cat1.id})
        self.assertEqual(resp.status_code, 200)
        # Free-text q (nom icontains)
        resp = self.client.get(url, {'q': 'lai'})
        self.assertEqual(resp.status_code, 200)
        # Search backend
        resp = self.client.get(url, {'search': 'Riz'})
        self.assertEqual(resp.status_code, 200)
        # Ordering by marque
        resp = self.client.get(url, {'ordering': 'marque'})
        self.assertEqual(resp.status_code, 200)

    def test_produits_fragment(self):
        url = reverse('produits-fragment')
        resp = self.client.get(url, {'q': 'ri', 'ordering': 'nom'})
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/html', resp.headers.get('Content-Type', ''))