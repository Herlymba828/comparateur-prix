# ♻️ Guide de Refactoring

Ce guide explique comment refactorer le code pour séparer la logique métier des vues et améliorer la maintenabilité.

---

## 🎯 Principes

### Single Responsibility Principle (SRP)

Chaque classe/fonction doit avoir une seule responsabilité.

### Separation of Concerns

Séparer :
- **Vues** : Gestion des requêtes HTTP
- **Services** : Logique métier
- **Modèles** : Structure des données
- **Serializers** : Validation et sérialisation

---

## 📁 Structure recommandée

```
apps/
├── produits/
│   ├── services/              # Logique métier
│   │   ├── __init__.py
│   │   ├── price_comparison.py
│   │   ├── product_analysis.py
│   │   └── price_aggregation.py
│   ├── domain/               # Domain models (optionnel, si DDD)
│   │   ├── __init__.py
│   │   └── entities.py
│   ├── views.py              # Vues minces
│   ├── serializers.py
│   └── models.py
```

---

## 🔄 Exemples de refactoring

### Exemple 1 : Comparaison de prix

**Avant** (logique dans la vue) :

```python
# apps/produits/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Min, Max, Avg
from decimal import Decimal

class ComparePricesView(APIView):
    def get(self, request):
        produit_id = request.query_params.get('produit_id')
        produit = Produit.objects.get(id=produit_id)
        
        # 30 lignes de logique métier...
        prix_list = Prix.objects.filter(produit=produit)
        min_prix = prix_list.aggregate(Min('prix_actuel'))['prix_actuel__min']
        max_prix = prix_list.aggregate(Max('prix_actuel'))['prix_actuel__max']
        avg_prix = prix_list.aggregate(Avg('prix_actuel'))['prix_actuel__avg']
        
        # Calculs complexes...
        ecart = max_prix - min_prix if min_prix else Decimal('0')
        pourcentage_ecart = (ecart / min_prix * 100) if min_prix else Decimal('0')
        
        return Response({
            'min': min_prix,
            'max': max_prix,
            'avg': avg_prix,
            'ecart': ecart,
            'pourcentage_ecart': pourcentage_ecart
        })
```

**Après** (logique dans un service) :

```python
# apps/produits/services/price_comparison.py
from decimal import Decimal
from django.db.models import Min, Max, Avg
from apps.produits.models import Produit, Prix
from typing import Dict, Optional


class PriceComparisonService:
    """Service pour comparer les prix d'un produit."""
    
    @staticmethod
    def get_price_statistics(produit: Produit) -> Dict[str, Optional[Decimal]]:
        """
        Calcule les statistiques de prix pour un produit.
        
        Args:
            produit: Instance du produit
            
        Returns:
            Dictionnaire avec min, max, avg, ecart, pourcentage_ecart
        """
        prix_list = Prix.objects.filter(produit=produit)
        
        if not prix_list.exists():
            return {
                'min': None,
                'max': None,
                'avg': None,
                'ecart': Decimal('0'),
                'pourcentage_ecart': Decimal('0')
            }
        
        min_prix = prix_list.aggregate(Min('prix_actuel'))['prix_actuel__min']
        max_prix = prix_list.aggregate(Max('prix_actuel'))['prix_actuel__max']
        avg_prix = prix_list.aggregate(Avg('prix_actuel'))['prix_actuel__avg']
        
        ecart = max_prix - min_prix if min_prix else Decimal('0')
        pourcentage_ecart = (
            (ecart / min_prix * 100) if min_prix else Decimal('0')
        )
        
        return {
            'min': min_prix,
            'max': max_prix,
            'avg': avg_prix,
            'ecart': ecart,
            'pourcentage_ecart': pourcentage_ecart
        }
    
    @staticmethod
    def find_best_price(produit: Produit) -> Optional[Prix]:
        """
        Trouve le meilleur prix (le plus bas) pour un produit.
        
        Args:
            produit: Instance du produit
            
        Returns:
            Instance Prix avec le prix le plus bas, ou None
        """
        return Prix.objects.filter(
            produit=produit
        ).order_by('prix_actuel').first()


# apps/produits/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.produits.models import Produit
from apps.produits.services.price_comparison import PriceComparisonService

class ComparePricesView(APIView):
    """Vue pour comparer les prix d'un produit."""
    
    def get(self, request):
        produit_id = request.query_params.get('produit_id')
        
        try:
            produit = Produit.objects.get(id=produit_id)
        except Produit.DoesNotExist:
            return Response(
                {'error': 'Produit non trouvé'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        statistics = PriceComparisonService.get_price_statistics(produit)
        return Response(statistics)
```

### Exemple 2 : Tâche Celery

**Avant** (tâche complexe) :

```python
# apps/produits/tasks.py
from celery import shared_task
from apps.produits.models import Produit, Prix
import requests
from bs4 import BeautifulSoup

@shared_task
def update_prices():
    """Met à jour tous les prix - TROP COMPLEXE!"""
    produits = Produit.objects.all()
    
    for produit in produits:
        # Scraping
        response = requests.get(produit.url)
        soup = BeautifulSoup(response.content, 'html.parser')
        prix = soup.find('span', class_='price').text
        
        # Parsing
        prix_float = float(prix.replace('€', '').replace(',', '.'))
        
        # Sauvegarde
        Prix.objects.create(
            produit=produit,
            prix_actuel=prix_float
        )
        
        # Envoi d'email si changement
        # ... 20 lignes de plus
```

**Après** (tâche simple, logique dans des services) :

```python
# apps/produits/services/scraping.py
import requests
from bs4 import BeautifulSoup
from decimal import Decimal
from typing import Optional

class PriceScrapingService:
    """Service pour scraper les prix."""
    
    @staticmethod
    def scrape_price(url: str) -> Optional[Decimal]:
        """
        Scrape le prix depuis une URL.
        
        Args:
            url: URL à scraper
            
        Returns:
            Prix en Decimal, ou None si erreur
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            price_element = soup.find('span', class_='price')
            
            if not price_element:
                return None
            
            price_text = price_element.text
            price_float = float(price_text.replace('€', '').replace(',', '.'))
            return Decimal(str(price_float))
            
        except Exception:
            return None


# apps/produits/services/price_update.py
from apps.produits.models import Produit, Prix
from apps.produits.services.scraping import PriceScrapingService
from decimal import Decimal

class PriceUpdateService:
    """Service pour mettre à jour les prix."""
    
    @staticmethod
    def update_product_price(produit: Produit) -> bool:
        """
        Met à jour le prix d'un produit.
        
        Args:
            produit: Instance du produit
            
        Returns:
            True si mis à jour, False sinon
        """
        if not produit.url:
            return False
        
        nouveau_prix = PriceScrapingService.scrape_price(produit.url)
        
        if nouveau_prix is None:
            return False
        
        # Vérifier si le prix a changé
        dernier_prix = Prix.objects.filter(
            produit=produit
        ).order_by('-date_creation').first()
        
        if dernier_prix and dernier_prix.prix_actuel == nouveau_prix:
            return False  # Pas de changement
        
        # Créer le nouveau prix
        Prix.objects.create(
            produit=produit,
            prix_actuel=nouveau_prix
        )
        
        return True


# apps/produits/tasks.py
from celery import shared_task
from apps.produits.models import Produit
from apps.produits.services.price_update import PriceUpdateService

@shared_task
def update_single_product_price(produit_id: int):
    """Met à jour le prix d'un seul produit."""
    try:
        produit = Produit.objects.get(id=produit_id)
        PriceUpdateService.update_product_price(produit)
    except Produit.DoesNotExist:
        pass

@shared_task
def update_all_prices():
    """Met à jour tous les prix."""
    produits = Produit.objects.all()
    for produit in produits:
        update_single_product_price.delay(produit.id)
```

---

## ✅ Checklist de refactoring

Avant de refactorer :

- [ ] Identifier la logique métier dans les vues
- [ ] Créer un service pour cette logique
- [ ] Écrire des tests pour le service
- [ ] Refactorer la vue pour utiliser le service
- [ ] Vérifier que les tests passent
- [ ] Vérifier la complexité cyclomatique (< 10)

---

## 🧪 Tests pour les services

```python
# apps/produits/tests/test_services.py
import pytest
from decimal import Decimal
from apps.produits.models import Produit, Prix
from apps.produits.services.price_comparison import PriceComparisonService

@pytest.mark.django_db
class TestPriceComparisonService:
    def test_get_price_statistics_with_prices(self):
        # Arrange
        produit = Produit.objects.create(nom="Test")
        Prix.objects.create(produit=produit, prix_actuel=Decimal("100"))
        Prix.objects.create(produit=produit, prix_actuel=Decimal("150"))
        Prix.objects.create(produit=produit, prix_actuel=Decimal("125"))
        
        # Act
        stats = PriceComparisonService.get_price_statistics(produit)
        
        # Assert
        assert stats['min'] == Decimal("100")
        assert stats['max'] == Decimal("150")
        assert stats['avg'] == Decimal("125")
        assert stats['ecart'] == Decimal("50")
    
    def test_get_price_statistics_no_prices(self):
        # Arrange
        produit = Produit.objects.create(nom="Test")
        
        # Act
        stats = PriceComparisonService.get_price_statistics(produit)
        
        # Assert
        assert stats['min'] is None
        assert stats['max'] is None
        assert stats['ecart'] == Decimal("0")
```

---

## 📚 Ressources

- [Clean Code - Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Refactoring - Martin Fowler](https://refactoring.com/)
- [Django Best Practices](https://docs.djangoproject.com/en/stable/misc/design-philosophies/)

