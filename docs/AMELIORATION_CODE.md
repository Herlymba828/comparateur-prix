# 🚀 Guide d'Amélioration du Code

Ce guide décrit toutes les améliorations mises en place pour améliorer la qualité, la sécurité et la maintenabilité du code.

---

## 📋 Table des matières

1. [Outils de qualité de code](#outils-de-qualité-de-code)
2. [Outils de sécurité](#outils-de-sécurité)
3. [Pipeline CI/CD](#pipeline-cicd)
4. [Refactoring de la logique métier](#refactoring-de-la-logique-métier)
5. [Sécurisation](#sécurisation)
6. [Amélioration de la résilience Celery](#amélioration-de-la-résilience-celery)
7. [Tests automatisés](#tests-automatisés)
8. [Documentation](#documentation)
9. [Audit et suivi de la sécurité](#audit-et-suivi-de-la-sécurité)

---

## 🛠️ Outils de qualité de code

### Installation

```bash
pip install -r requirements-dev.txt
```

### Configuration

Les fichiers de configuration sont :
- `setup.cfg` : Configuration pour flake8, pylint, isort, mypy
- `pyproject.toml` : Configuration pour black, isort, pytest, coverage
- `.bandit` : Configuration pour bandit
- `.pre-commit-config.yaml` : Hooks pre-commit

### Utilisation

#### Black (formatage automatique)

```bash
# Formater tout le code
black .

# Vérifier sans formater
black --check .
```

#### isort (tri des imports)

```bash
# Trier les imports
isort .

# Vérifier sans trier
isort --check-only .
```

#### Flake8 (linting)

```bash
flake8 .
```

#### Pylint (analyse statique)

```bash
# Analyser tout le projet
pylint apps config

# Analyser un fichier spécifique
pylint apps/produits/views.py
```

#### Radon (complexité cyclomatique)

```bash
# Mesurer la complexité
radon cc . --min B

# Mesurer l'indice de maintenabilité
radon mi . --min B

# Afficher la complexité avec détails
radon cc . --show-complexity
```

#### MyPy (vérification de types)

```bash
mypy . --ignore-missing-imports
```

---

## 🔒 Outils de sécurité

### Bandit (vulnérabilités Python)

```bash
# Scanner le code
bandit -r . -ll

# Générer un rapport JSON
bandit -r . -f json -o bandit-report.json
```

### pip-audit (vulnérabilités des dépendances)

```bash
# Scanner les dépendances
pip-audit --requirement requirements.txt

# Générer un rapport JSON
pip-audit --requirement requirements.txt --format json --output pip-audit-report.json
```

### Safety (vérification des dépendances)

```bash
# Vérifier les dépendances
safety check

# Vérifier avec un fichier requirements
safety check --file requirements.txt
```

---

## 🔄 Pipeline CI/CD

### Configuration GitHub Actions

Le fichier `.github/workflows/ci.yml` contient :

1. **Job Quality** : Vérifie la qualité du code
   - Black, isort, Flake8, Pylint, Radon, MyPy

2. **Job Security** : Vérifie la sécurité
   - Bandit, pip-audit, Safety

3. **Job Tests** : Exécute les tests
   - Tests unitaires et d'intégration avec coverage

4. **Job Lint** : Vérifie le formatage
   - Black et isort en mode check

### Utilisation

Le pipeline s'exécute automatiquement sur :
- Push vers `main` ou `develop`
- Pull requests vers `main` ou `develop`

### Exécution locale

```bash
# Installer pre-commit
pip install pre-commit

# Installer les hooks
pre-commit install

# Exécuter manuellement
pre-commit run --all-files
```

---

## 🏗️ Refactoring de la logique métier

### Structure recommandée

```
apps/
├── produits/
│   ├── services/          # Logique métier
│   │   ├── price_comparison.py
│   │   └── product_analysis.py
│   ├── domain/            # Domain models (si DDD)
│   │   └── entities.py
│   ├── views.py          # Vues minces (délèguent aux services)
│   └── serializers.py
```

### Exemple de refactoring

**Avant** (logique dans la vue) :
```python
# apps/produits/views.py
def compare_prices(request):
    produits = Produit.objects.all()
    # 50 lignes de logique métier...
    return Response(results)
```

**Après** (logique dans un service) :
```python
# apps/produits/services/price_comparison.py
class PriceComparisonService:
    @staticmethod
    def compare_prices(produits):
        # Logique métier isolée
        pass

# apps/produits/views.py
from .services.price_comparison import PriceComparisonService

def compare_prices(request):
    produits = Produit.objects.all()
    results = PriceComparisonService.compare_prices(produits)
    return Response(results)
```

### Principes à suivre

1. **Single Responsibility Principle (SRP)** : Chaque fonction/classe fait une seule chose
2. **Separation of Concerns** : Séparer la logique métier des vues
3. **Dependency Injection** : Injecter les dépendances plutôt que de les créer

---

## 🔐 Sécurisation

### Validation des données

Utiliser des serializers DRF bien définis :

```python
# apps/produits/serializers.py
class ProduitSerializer(serializers.ModelSerializer):
    prix = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=0,
        validators=[validate_prix_positif]
    )
    
    def validate_prix(self, value):
        if value < 0:
            raise serializers.ValidationError("Le prix doit être positif")
        return value
```

### Headers de sécurité

Déjà configurés dans `config/settings.py` :

```python
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_CONTENT_TYPE_NOSNIFF = True
```

### Configuration séparée dev/prod

Créer `config/settings/` :

```
config/
├── settings/
│   ├── __init__.py
│   ├── base.py      # Configuration commune
│   ├── development.py
│   └── production.py
```

### Gestion des secrets

Utiliser des variables d'environnement (déjà en place avec `.env`).

---

## ⚡ Amélioration de la résilience Celery

### Configuration des retries

```python
# apps/produits/tasks.py
from celery import shared_task
from celery.exceptions import Retry

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True
)
def update_prices(self, produit_id):
    try:
        # Logique de la tâche
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### Monitoring avec Flower

```bash
# Installer Flower
pip install flower

# Lancer Flower
celery -A config flower --port=5555
```

Accéder à : `http://localhost:5555`

### Configuration Prometheus (optionnel)

```python
# config/celery.py
from celery import Celery
from prometheus_client import Counter, Histogram

app = Celery('config')

# Métriques Prometheus
task_counter = Counter('celery_tasks_total', 'Total tasks', ['task_name', 'status'])
task_duration = Histogram('celery_task_duration_seconds', 'Task duration', ['task_name'])
```

---

## 🧪 Tests automatisés

### Structure des tests

```
apps/
├── produits/
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   ├── test_views.py
│   │   ├── test_services.py
│   │   └── test_tasks.py
```

### Exemple de test unitaire

```python
# apps/produits/tests/test_services.py
import pytest
from decimal import Decimal
from apps.produits.services.price_comparison import PriceComparisonService
from apps.produits.models import Produit, Prix

@pytest.mark.django_db
class TestPriceComparisonService:
    def test_compare_prices_with_valid_data(self):
        # Arrange
        produit = Produit.objects.create(nom="Test")
        Prix.objects.create(produit=produit, prix_actuel=Decimal("100"))
        
        # Act
        result = PriceComparisonService.compare_prices([produit])
        
        # Assert
        assert result is not None
        assert len(result) > 0
    
    def test_compare_prices_with_missing_data(self):
        # Test edge case : données manquantes
        result = PriceComparisonService.compare_prices([])
        assert result == []
```

### Tests Celery

```python
# apps/produits/tests/test_tasks.py
from unittest.mock import patch
from apps.produits.tasks import update_prices

@pytest.mark.django_db
def test_update_prices_task():
    with patch('apps.produits.tasks.update_prices.apply_async') as mock_task:
        update_prices.delay(produit_id=1)
        mock_task.assert_called_once()
```

### Exécution des tests

```bash
# Tous les tests
pytest

# Avec coverage
pytest --cov=. --cov-report=html

# Tests spécifiques
pytest apps/produits/tests/test_services.py

# Tests avec markers
pytest -m "not slow"
```

---

## 📚 Documentation

### Swagger/OpenAPI

Déjà configuré avec `drf-spectacular` :

- Accéder à : `https://votre-domaine.com/api/docs/`
- Schéma : `https://votre-domaine.com/api/schema/`

### Structure de la documentation

```
docs/
├── README.md                    # Vue d'ensemble
├── INSTALLATION.md              # Installation locale
├── DEVELOPMENT.md               # Guide de développement
├── ARCHITECTURE.md              # Architecture de l'application
├── API.md                       # Documentation API
└── DEPLOIEMENT.md               # Guide de déploiement
```

### Exemples dans le README

```markdown
## 🚀 Démarrage rapide

### Installation locale

```bash
# Cloner le projet
git clone https://github.com/votre-repo/comparateur-prix.git
cd comparateur-prix

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configurer .env
cp .env.example .env
# Éditer .env avec vos configurations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Lancer le serveur
python manage.py runserver
```

### Lancer Celery

```bash
# Terminal 1 : Worker
celery -A config worker -l info

# Terminal 2 : Beat (tâches périodiques)
celery -A config beat -l info

# Terminal 3 : Flower (monitoring)
celery -A config flower
```
```

---

## 🔍 Audit et suivi de la sécurité

### Checklist de sécurité pour les PRs

Créer `.github/PULL_REQUEST_TEMPLATE.md` :

```markdown
## Checklist de sécurité

- [ ] Validation des entrées utilisateur
- [ ] Pas de secrets hardcodés
- [ ] Headers de sécurité configurés
- [ ] Tests de sécurité ajoutés
- [ ] Dépendances vérifiées (pip-audit)
- [ ] Code review effectué
```

### Threat Modeling

#### Menaces identifiées

1. **Falsification des prix**
   - Mitigation : Validation côté serveur, authentification

2. **Vol de données**
   - Mitigation : Chiffrement, HTTPS, gestion des secrets

3. **Spam de requêtes**
   - Mitigation : Rate limiting, throttling DRF

4. **Injection SQL**
   - Mitigation : ORM Django, requêtes paramétrées

### Revues de code

Processus recommandé :
1. Auteur crée une PR
2. Vérification automatique (CI)
3. Review par au moins 2 développeurs
4. Checklist de sécurité vérifiée
5. Merge après approbation

---

## 📊 Métriques et monitoring

### Code Coverage

Objectif : **> 80%**

```bash
# Générer le rapport
pytest --cov=. --cov-report=html

# Voir le rapport
open htmlcov/index.html
```

### Complexité cyclomatique

Objectif : **< 10 par fonction**

```bash
radon cc . --min B
```

### Indice de maintenabilité

Objectif : **> 70**

```bash
radon mi . --min B
```

---

## 🎯 Prochaines étapes

1. ✅ Configuration des outils de qualité
2. ✅ Configuration des outils de sécurité
3. ✅ Pipeline CI/CD
4. ⏳ Refactoring progressif de la logique métier
5. ⏳ Ajout de tests unitaires et d'intégration
6. ⏳ Amélioration de la documentation
7. ⏳ Mise en place du monitoring Celery

---

## 📞 Support

Pour toute question ou problème :
1. Consultez la documentation dans `docs/`
2. Vérifiez les issues GitHub
3. Contactez l'équipe de développement

