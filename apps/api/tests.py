from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.produits.models import Categorie, Produit, Marque, UniteMesure
from apps.magasins.models import Region, Ville, Magasin
from apps.produits.models import Prix


class ApiBasicsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Taxonomy
        cls.cat = Categorie.objects.create(nom="Boissons", slug="boissons")
        cls.brand = Marque.objects.create(nom="EauPure", slug="eaupure")
        cls.unit = UniteMesure.objects.create(nom="Litre", symbole="L")

        # Produits
        cls.prod1 = Produit.objects.create(
            code_barre="0001",
            nom="Eau minérale 1L",
            slug="eau-minerale-1l",
            categorie=cls.cat,
            marque=cls.brand,
            unite_mesure=cls.unit,
        )
        cls.prod2 = Produit.objects.create(
            code_barre="0002",
            nom="Jus d'orange 1L",
            slug="jus-orange-1l",
            categorie=cls.cat,
            unite_mesure=cls.unit,
        )

        # Magasin
        reg = Region.objects.create(nom="Estuaire")
        ville = Ville.objects.create(nom="Libreville", region=reg)
        cls.store = Magasin.objects.create(nom="Super U", type="supermarche", ville=ville)

        # Prix
        Prix.objects.create(produit=cls.prod1, magasin=cls.store, prix_actuel=Decimal("500"))
        Prix.objects.create(produit=cls.prod1, magasin=cls.store, prix_actuel=Decimal("450"))  # min
        Prix.objects.create(produit=cls.prod2, magasin=cls.store, prix_actuel=Decimal("1200"))

        cls.client = APIClient()

    def test_health(self):
        url = reverse('api-health')
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json().get('status'), 'ok')

    def test_search_produits_min_price_and_filters(self):
        url = reverse('api-search-produits')

        # Sans filtre: prod1 doit avoir min_prix=450, prod2 min_prix=1200
        res = self.client.get(url)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        by_id = {item['id']: item for item in data['results']}
        self.assertEqual(Decimal(str(by_id[self.prod1.id]['min_prix'])), Decimal('450'))
        self.assertEqual(Decimal(str(by_id[self.prod2.id]['min_prix'])), Decimal('1200'))

        # Filtre q sur la marque (FK -> marque__nom__icontains)
        res2 = self.client.get(url, {"q": "EauPure"})
        self.assertEqual(res2.status_code, 200)
        names = [it['nom'] for it in res2.json()['results']]
        self.assertIn("Eau minérale 1L", names)

        # Filtre marque explicite
        res3 = self.client.get(url, {"marque": "eau"})
        self.assertEqual(res3.status_code, 200)
        names3 = [it['nom'] for it in res3.json()['results']]
        self.assertIn("Eau minérale 1L", names3)

    def test_autocomplete(self):
        url = reverse('api-autocomplete-produits')
        res = self.client.get(url, {"q": "eau"})
        self.assertEqual(res.status_code, 200)
        labels = [r['label'] for r in res.json().get('results', [])]
        self.assertTrue(any("Eau" in l for l in labels))
from django.test import TestCase

# Create your tests here.
