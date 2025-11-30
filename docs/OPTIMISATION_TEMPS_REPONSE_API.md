# ⚡ Guide d'Optimisation du Temps de Réponse API

Guide complet pour optimiser les performances de l'API et réduire le temps de réponse.

## 📊 Vue d'ensemble

Ce guide présente les optimisations par ordre de priorité (impact vs facilité d'implémentation) :

1. **Impact élevé, facile** : Cache des endpoints fréquents ✅ (déjà implémenté)
2. **Impact élevé, moyen** : Optimisation des requêtes DB (N+1) ⚠️ (partiellement implémenté)
3. **Impact moyen, facile** : Pagination et limites ✅ (déjà implémenté)
4. **Impact moyen, moyen** : Endpoints batch ✅ (déjà implémenté)
5. **Impact élevé, complexe** : Indexation DB et requêtes optimisées ⚠️ (à améliorer)

---

## 🎯 Optimisations Prioritaires

### 1. Optimisation des Requêtes Database (N+1)

#### Problème identifié

Dans `apps/api/views.py`, la fonction `search_produits` fait une requête par produit pour récupérer les prix :

```python
# ❌ Problème : N+1 queries
for p in produits.order_by("nom")[start:end]:
    items.append({
        "min_prix": p.min_prix,  # Annotation OK
        "marque": (p.marque.nom if getattr(p, "marque", None) else ""),  # select_related OK
        # Mais pas de prefetch_related pour les prix
    })
```

#### Solution : Améliorer les annotations

```python
# ✅ Solution optimisée
@api_view(["GET"])
def search_produits(request):
    """Recherche de produits avec prix minimum agrégé (option filtres)."""
    q = (request.GET.get("q") or "").strip()
    categorie = request.GET.get("categorie")
    marque = (request.GET.get("marque") or "").strip()
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    # Cache key
    params = {
        'q': q, 'categorie': categorie, 'marque': marque,
        'page': page, 'page_size': page_size,
    }
    cache_key = f"search_produits:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
    
    cached = cache.get(cache_key)
    if cached:
        return Response(cached, status=HTTP_200_OK)

    # ✅ Optimisation : select_related + annotation en une requête
    produits = Produit.objects.select_related("categorie", "marque", "unite_mesure")
    
    if q:
        produits = produits.filter(
            Q(nom__icontains=q)
            | Q(marque__nom__icontains=q)
            | Q(categorie__nom__icontains=q)
        )
    if categorie:
        produits = produits.filter(categorie_id=categorie)
    if marque:
        produits = produits.filter(marque__nom__icontains=marque)

    # ✅ Annotation optimisée avec filtre sur est_disponible
    produits = produits.annotate(
        min_prix=Min("prix__prix_actuel", filter=Q(prix__est_disponible=True)),
        max_prix=Max("prix__prix_actuel", filter=Q(prix__est_disponible=True)),
        prix_count=Count("prix", filter=Q(prix__est_disponible=True)),
    ).filter(est_actif=True)  # Filtrer les produits actifs

    # ✅ Compter AVANT de paginer (plus efficace)
    total = produits.count()
    start = (page - 1) * page_size
    
    # ✅ Utiliser values() pour réduire la taille des données
    items = list(
        produits.order_by("nom")[start:start + page_size]
        .values(
            "id", "nom",
            "categorie_id", "categorie__nom",
            "marque__nom",
            "min_prix", "max_prix", "prix_count"
        )
    )
    
    # Formater les résultats
    results = [
        {
            "id": item["id"],
            "nom": item["nom"],
            "marque": item["marque__nom"] or "",
            "categorie_id": item["categorie_id"],
            "categorie_nom": item["categorie__nom"] or "",
            "min_prix": item["min_prix"],
            "max_prix": item["max_prix"],
            "prix_count": item["prix_count"],
            "devise": "XAF" if item["min_prix"] is not None else None,
        }
        for item in items
    ]

    data = {"count": total, "results": ProductSearchResultSerializer(results, many=True).data}

    # Cache avec TTL adaptatif
    ttl = 900 if (categorie or marque) else 300
    cache.set(cache_key, data, ttl)

    # Journaliser (asynchrone si possible)
    try:
        if q:
            user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
            ip = (request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or '').split(',')[0].strip()
            ip_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()[:64] if ip else ''
            SearchEvent.objects.create(q=q, utilisateur=user, ip_hash=ip_hash)
    except Exception:
        pass  # Ne jamais bloquer la réponse

    return Response(data, status=HTTP_200_OK)
```

**Gain estimé** : Réduction de 50-80% du temps de réponse pour les recherches avec beaucoup de résultats.

---

### 2. Optimisation de `autocomplete_produits`

#### Problème actuel

La requête utilise `values()` mais peut être optimisée avec un index et une limite plus stricte.

```python
# ✅ Version optimisée
@api_view(["GET"])
def autocomplete_produits(request):
    q = (request.GET.get("q") or "").strip()
    if not q or len(q) < 2:  # Minimum 2 caractères
        return Response({"results": []}, status=HTTP_200_OK)
    
    cache_key = f"autocomplete:{q.lower()}"
    cached = cache.get(cache_key)
    if cached:
        return Response(cached, status=HTTP_200_OK)
    
    # ✅ Optimisation : utiliser only() pour limiter les champs chargés
    # ✅ Limite stricte à 10 résultats (suffisant pour autocomplete)
    qs = (
        Produit.objects
        .filter(est_actif=True, nom__icontains=q)
        .only("id", "nom")  # Charger uniquement les champs nécessaires
        .order_by("nom")
        .values("id", "nom")[:10]  # Limite stricte
    )
    
    results = [{"id": row["id"], "label": row["nom"]} for row in qs]
    data = {"results": AutocompleteResultSerializer(results, many=True).data}
    
    # Cache court (2 minutes) car très fréquent
    cache.set(cache_key, data, 120)
    
    return Response(data, status=HTTP_200_OK)
```

**Gain estimé** : Réduction de 30-50% du temps de réponse.

---

### 3. Optimisation des ViewSets avec Pagination

#### Problème identifié

Certains ViewSets chargent trop de données avant la pagination.

#### Solution : Pagination précoce

```python
# ✅ Exemple pour ProduitViewSet
class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.select_related(
        'categorie', 'marque', 'unite_mesure'
    ).prefetch_related(
        'caracteristiques', 'avis'
    ).filter(est_actif=True)
    
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # ✅ Appliquer les annotations AVANT la pagination
        if self.action == 'list':
            queryset = queryset.annotate(
                prix_moyen_agg=Avg('prix__prix_actuel', filter=Q(prix__est_disponible=True)),
                prix_min_agg=Min('prix__prix_actuel', filter=Q(prix__est_disponible=True)),
                prix_max_agg=Max('prix__prix_actuel', filter=Q(prix__est_disponible=True)),
                prix_count=Count('prix', filter=Q(prix__est_disponible=True)),
            )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # ✅ La pagination se fait automatiquement par DRF
        # ✅ Le queryset est déjà optimisé avec select_related/prefetch_related
        return super().list(request, *args, **kwargs)
```

---

### 4. Cache avec Invalidation Intelligente

#### Problème actuel

Le cache est invalidé de manière globale, ce qui peut être inefficace.

#### Solution : Tags de cache (avec django-redis)

```python
# ✅ Installation requise : pip install django-redis
# Dans settings.py :
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_CACHE_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'comparateur_prix',
    }
}

# ✅ Utilisation avec tags
from django_redis import get_redis_connection
from django.core.cache import cache

def search_produits_with_tags(request):
    # ... code de recherche ...
    
    # Cache avec tags
    cache_key = f"search_produits:{hash_key}"
    cache.set(cache_key, data, ttl)
    
    # Ajouter des tags pour invalidation ciblée
    redis_client = get_redis_connection("default")
    redis_client.sadd(f"cache:tag:produit:{produit_id}", cache_key)
    redis_client.sadd(f"cache:tag:categorie:{categorie_id}", cache_key)
    
    return Response(data)

# ✅ Invalidation ciblée
def invalidate_search_cache(produit_id=None, categorie_id=None):
    redis_client = get_redis_connection("default")
    
    if produit_id:
        keys = redis_client.smembers(f"cache:tag:produit:{produit_id}")
        if keys:
            cache.delete_many([k.decode() for k in keys])
            redis_client.delete(f"cache:tag:produit:{produit_id}")
    
    if categorie_id:
        keys = redis_client.smembers(f"cache:tag:categorie:{categorie_id}")
        if keys:
            cache.delete_many([k.decode() for k in keys])
            redis_client.delete(f"cache:tag:categorie:{categorie_id}")
```

---

### 5. Indexation Database

#### Indexes recommandés

Créer une migration pour ajouter des indexes sur les champs fréquemment utilisés :

```python
# apps/produits/migrations/XXXX_add_indexes.py
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('produits', 'XXXX_previous_migration'),
    ]

    operations = [
        # Index sur nom pour recherches
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_produit_nom_icontains ON produits_produit (LOWER(nom));",
            reverse_sql="DROP INDEX IF EXISTS idx_produit_nom_icontains;"
        ),
        # Index composite pour prix
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_prix_produit_disponible ON produits_prix (produit_id, est_disponible, prix_actuel);",
            reverse_sql="DROP INDEX IF EXISTS idx_prix_produit_disponible;"
        ),
        # Index sur date_modification pour filtres temporels
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_prix_date_modification ON produits_prix (date_modification);",
            reverse_sql="DROP INDEX IF EXISTS idx_prix_date_modification;"
        ),
    ]
```

**Gain estimé** : Réduction de 40-60% du temps de requête sur les recherches.

---

### 6. Compression des Réponses

#### Solution : Middleware de compression

```python
# config/middleware.py
from django.utils.deprecation import MiddlewareMixin
import gzip
from django.http import HttpResponse

class CompressionMiddleware(MiddlewareMixin):
    """Compresse les réponses JSON si le client le supporte."""
    
    def process_response(self, request, response):
        # Vérifier si le client accepte la compression
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        if 'gzip' in accept_encoding and response.get('Content-Type', '').startswith('application/json'):
            # Compresser la réponse
            content = gzip.compress(response.content)
            response = HttpResponse(content, content_type=response['Content-Type'])
            response['Content-Encoding'] = 'gzip'
            response['Content-Length'] = str(len(content))
        
        return response

# Dans settings.py :
MIDDLEWARE = [
    # ... autres middlewares ...
    'config.middleware.CompressionMiddleware',
    # ...
]
```

**Gain estimé** : Réduction de 60-80% de la taille des réponses (surtout pour les listes).

---

### 7. Requêtes Asynchrones pour Logs

#### Problème

Les logs de recherche bloquent la réponse.

#### Solution : Tâches Celery

```python
# apps/api/tasks.py
from celery import shared_task
from .models import SearchEvent

@shared_task
def log_search_event(q, produit_id=None, utilisateur_id=None, ip_hash=None):
    """Log asynchrone des recherches."""
    try:
        produit_obj = None
        if produit_id:
            produit_obj = Produit.objects.only('id').get(id=produit_id)
        
        user_obj = None
        if utilisateur_id:
            user_obj = Utilisateur.objects.only('id').get(id=utilisateur_id)
        
        SearchEvent.objects.create(
            q=q,
            produit=produit_obj,
            utilisateur=user_obj,
            ip_hash=ip_hash
        )
    except Exception as e:
        logger.error(f"Erreur lors du log de recherche: {e}")

# Dans views.py :
from .tasks import log_search_event

@api_view(["GET"])
def search_produits(request):
    # ... code de recherche ...
    
    # ✅ Log asynchrone (ne bloque pas la réponse)
    if q:
        user_id = request.user.id if request.user.is_authenticated else None
        ip = (request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or '').split(',')[0].strip()
        ip_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()[:64] if ip else ''
        
        # Trouver le produit si nom exact
        produit_id = None
        try:
            produit_id = Produit.objects.filter(nom__iexact=q).values_list('id', flat=True).first()
        except Exception:
            pass
        
        # Envoyer la tâche asynchrone
        log_search_event.delay(q, produit_id, user_id, ip_hash)
    
    return Response(data, status=HTTP_200_OK)
```

**Gain estimé** : Réduction de 10-50ms par requête (selon la complexité du log).

---

## 📈 Métriques de Performance

### Outils de Monitoring

1. **django-debug-toolbar** (développement)
   ```bash
   pip install django-debug-toolbar
   ```

2. **django-silk** (production)
   ```bash
   pip install django-silk
   ```

3. **APM (Application Performance Monitoring)**
   - New Relic
   - Datadog
   - Sentry Performance

### Métriques à Surveiller

- **Temps de réponse moyen** : < 200ms pour les endpoints fréquents
- **Temps de réponse P95** : < 500ms
- **Temps de réponse P99** : < 1000ms
- **Nombre de requêtes DB par endpoint** : < 5
- **Taux de cache hit** : > 70%

---

## 🚀 Checklist d'Implémentation

### Phase 1 : Optimisations Faciles (1-2 jours)
- [ ] Optimiser `search_produits` avec `values()` et annotations
- [ ] Optimiser `autocomplete_produits` avec `only()`
- [ ] Ajouter compression gzip
- [ ] Déplacer les logs en asynchrone

### Phase 2 : Optimisations Moyennes (3-5 jours)
- [ ] Implémenter tags de cache avec django-redis
- [ ] Ajouter indexes database
- [ ] Optimiser tous les ViewSets avec pagination précoce
- [ ] Ajouter monitoring avec django-silk

### Phase 3 : Optimisations Avancées (1-2 semaines)
- [ ] Implémenter cache distribué avec Redis Cluster
- [ ] Optimiser les requêtes complexes avec raw SQL si nécessaire
- [ ] Ajouter CDN pour les assets statiques
- [ ] Implémenter rate limiting intelligent

---

## 📚 Ressources

- [Django Performance Best Practices](https://docs.djangoproject.com/en/stable/topics/performance/)
- [Django REST Framework Performance](https://www.django-rest-framework.org/topics/performance/)
- [PostgreSQL Indexing](https://www.postgresql.org/docs/current/indexes.html)
- [Redis Caching Strategies](https://redis.io/docs/manual/patterns/cache/)

---

*Dernière mise à jour : 2025-01-17*

