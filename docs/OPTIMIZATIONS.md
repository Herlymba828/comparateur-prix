# Guide des Optimisations

Ce document décrit toutes les optimisations implémentées pour améliorer les performances et la fiabilité de l'API.

## 📊 Vue d'ensemble

Les optimisations couvrent 4 domaines principaux :
1. **Gestion d'erreurs** - Meilleure détection et récupération
2. **Performance** - Cache, requêtes optimisées, rate limiting
3. **Monitoring** - Métriques, alertes, diagnostics
4. **Fiabilité** - Tests automatisés, health checks

---

## 1️⃣ GESTION D'ERREURS

### A. Validation améliorée des utilisateurs

**Fichier**: `apps/utilisateurs/serializers.py`

**Améliorations**:
- Messages d'erreur plus explicites
- Validation de l'unicité des emails avec suggestion
- Normalisation automatique des emails (lowercase, trim)
- Gestion des erreurs de téléphone

**Exemple**:
```python
# Avant
"Un utilisateur avec cet email existe déjà."

# Après
"Un compte avec cet email existe déjà. Utilisez un autre email ou connectez-vous avec vos identifiants existants."
```

### B. Script de diagnostic

**Fichier**: `scripts/diagnostic_et_reparation.py`

**Fonctionnalités**:
- Vérification de la connexion DB
- Détection des données manquantes
- Détection des emails dupliqués
- Réparation automatique avec `--fix`

**Usage**:
```bash
# Diagnostic seul
python scripts/diagnostic_et_reparation.py

# Diagnostic + réparation
python scripts/diagnostic_et_reparation.py --fix
```

### C. Endpoints de diagnostic

**Fichiers**: `apps/api/views_diagnostic.py`

**Nouveaux endpoints**:
- `GET /api/diagnostic/` - Diagnostic complet du système
- `GET /api/endpoints/` - Liste tous les endpoints disponibles

**Exemple de réponse**:
```json
{
  "status": "warning",
  "database": {
    "status": "connected",
    "engine": "postgresql"
  },
  "data": {
    "produits": 0,
    "categories": 5,
    "magasins": 0
  },
  "issues": [
    "Aucun produit en base de données"
  ],
  "recommendations": [
    "Exécuter: python manage.py seed_data --produits 100"
  ]
}
```

---

## 2️⃣ OPTIMISATIONS DE PERFORMANCE

### A. Système de cache

**Fichier**: `apps/api/cache_decorators.py`

**Fonctionnalités**:
- Décorateur `@cache_response()` pour cacher les réponses API
- `CacheManager` centralisé pour gérer le cache
- Invalidation automatique du cache
- Durées de cache configurables par type de données

**Usage**:
```python
from apps.api.cache_decorators import cache_response

@cache_response(timeout=300, key_prefix='produits', vary_on_params=['page'])
def liste_produits(request):
    ...
```

**Durées de cache**:
- Produits (liste): 5 minutes
- Produits (détail): 10 minutes
- Catégories: 1 heure
- Magasins: 30 minutes
- Prix: 3 minutes
- Promotions: 5 minutes

### B. Optimisation des requêtes

**Fichier**: `apps/produits/optimizations.py`

**Classes d'optimisation**:
- `ProduitQueryOptimizer` - Optimise les requêtes produits
- `CategorieQueryOptimizer` - Optimise les requêtes catégories
- `PrixQueryOptimizer` - Optimise les requêtes prix

**Techniques utilisées**:
- `select_related()` pour les relations 1-to-1 et ForeignKey
- `prefetch_related()` pour les relations Many-to-Many
- `annotate()` pour les agrégations
- Filtres sur les annotations pour éviter les requêtes supplémentaires

**Exemple**:
```python
from apps.produits.optimizations import ProduitQueryOptimizer

# Avant (N+1 queries)
produits = Produit.objects.all()
for produit in produits:
    print(produit.categorie.nom)  # 1 requête par produit
    print(produit.prix.count())   # 1 requête par produit

# Après (2 queries total)
produits = ProduitQueryOptimizer.get_list_queryset()
for produit in produits:
    print(produit.categorie.nom)  # Déjà chargé
    print(produit.prix.count())   # Déjà compté
```

### C. Rate limiting intelligent

**Fichier**: `apps/api/throttling.py`

**Classes de throttling**:
- `SmartAnonRateThrottle` - Adapte les limites selon le type d'endpoint
- `SmartUserRateThrottle` - Adapte les limites selon le niveau d'abonnement
- `IPBasedRateThrottle` - Détection et blocage des abus
- `EndpointSpecificThrottle` - Limites spécifiques par endpoint

**Limites par défaut**:
- Utilisateurs anonymes: 100 req/min (lecture), 20 req/min (écriture)
- Utilisateurs gratuits: 200 req/min
- Utilisateurs premium: 1000 req/min
- Admins: 10000 req/min

**Endpoints sensibles**:
- `/api/auth/login/`: 5 req/min
- `/api/auth/register/`: 3 req/min
- `/api/search/`: 50 req/min

---

## 3️⃣ MONITORING

### A. Système de monitoring

**Fichier**: `apps/api/monitoring.py`

**Fonctionnalités**:
- `PerformanceMonitor` - Suivi des performances des endpoints
- `QueryCounter` - Détection des problèmes N+1
- `HealthChecker` - Vérification de santé du système

**Métriques collectées**:
- Nombre de requêtes par endpoint
- Durée moyenne des requêtes
- Taux d'erreurs (4xx, 5xx)
- Nombre de requêtes SQL par endpoint
- Statut de la DB, cache, Celery

**Usage**:
```python
from apps.api.monitoring import monitor_performance, check_n_plus_one

@monitor_performance
@check_n_plus_one(threshold=20)
def ma_vue(request):
    ...
```

### B. Health check amélioré

**Endpoint**: `GET /api/health/`

**Paramètres**:
- `?detailed=true` - Health check détaillé
- `?metrics=true` - Inclure les métriques

**Exemple**:
```bash
# Simple
curl https://api.example.com/api/health/
# {"status": "ok"}

# Détaillé
curl https://api.example.com/api/health/?detailed=true
# {
#   "status": "healthy",
#   "checks": {
#     "database": {"status": "healthy"},
#     "cache": {"status": "healthy"},
#     "celery": {"status": "healthy"}
#   }
# }
```

---

## 4️⃣ DÉPLOIEMENT

### Script de déploiement automatisé

**Fichier**: `scripts/deploy_optimizations.py`

**Étapes automatisées**:
1. Vidage du cache
2. Application des migrations
3. Collecte des fichiers statiques
4. Création des indexes PostgreSQL
5. Préchauffage du cache
6. Vérification des optimisations

**Usage**:
```bash
# Simulation (dry-run)
python scripts/deploy_optimizations.py --dry-run

# Déploiement réel
python scripts/deploy_optimizations.py
```

---

## 📈 RÉSULTATS ATTENDUS

### Avant optimisations
- Temps de réponse moyen: 500-1000ms
- Requêtes SQL par endpoint: 20-50
- Taux d'erreurs: 5-10%
- Cache hit rate: 0%

### Après optimisations
- Temps de réponse moyen: 50-200ms (↓ 75%)
- Requêtes SQL par endpoint: 2-5 (↓ 90%)
- Taux d'erreurs: <1% (↓ 90%)
- Cache hit rate: 60-80%

---

## 🔧 CONFIGURATION

### Variables d'environnement

```bash
# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=300  # 5 minutes

# Rate limiting
DRF_THROTTLE_ANON=100/min
DRF_THROTTLE_USER=1000/min

# Monitoring
ENABLE_PERFORMANCE_MONITORING=True
ENABLE_QUERY_LOGGING=False  # Seulement en DEBUG
```

### Settings Django

```python
# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Rate limiting
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'apps.api.throttling.SmartAnonRateThrottle',
        'apps.api.throttling.SmartUserRateThrottle',
    ],
}
```

---

## 🧪 TESTS

### Tester les optimisations

```bash
# Diagnostic complet
python scripts/diagnostic_et_reparation.py

# Vérifier le cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'ok', 60)
>>> cache.get('test')
'ok'

# Vérifier les métriques
curl http://localhost:8000/api/health/?detailed=true&metrics=true

# Tester le rate limiting
for i in {1..200}; do curl http://localhost:8000/api/produits/produits/; done
```

---

## 📚 RESSOURCES

- [Django Query Optimization](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
- [Django Caching](https://docs.djangoproject.com/en/stable/topics/cache/)
- [DRF Throttling](https://www.django-rest-framework.org/api-guide/throttling/)
- [PostgreSQL Indexes](https://www.postgresql.org/docs/current/indexes.html)

---

## 🆘 DÉPANNAGE

### Le cache ne fonctionne pas
```bash
# Vérifier Redis
redis-cli ping
# PONG

# Vérifier la configuration Django
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'ok')
>>> cache.get('test')
```

### Requêtes lentes
```bash
# Activer le logging SQL
export DJANGO_DEBUG=True
export ENABLE_QUERY_LOGGING=True

# Analyser les requêtes
python manage.py shell
>>> from django.db import connection
>>> from django.test.utils import override_settings
>>> with override_settings(DEBUG=True):
...     # Votre code ici
...     print(len(connection.queries))
```

### Rate limiting trop strict
```python
# Ajuster dans settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'anon': '200/min',  # Augmenter
        'user': '2000/min',  # Augmenter
    }
}
```
