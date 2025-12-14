# Compatibilité Redis - Guide Complet

## 📦 Versions Actuelles

### Dépendances Redis du Projet
```
redis==5.0.1
django-redis==5.4.0
celery==5.3.4
Django==5.1.2
```

## ✅ Versions Compatibles Recommandées

### Option 1: Redis 4.x (Stable et Testé) ⭐ RECOMMANDÉ
```python
# requirements.txt
redis==4.6.0
django-redis==5.4.0
celery==5.3.4
```

**Avantages**:
- ✅ Stable et bien testé
- ✅ Compatible avec Django's RedisCache backend
- ✅ Pas de problèmes de paramètres (SOCKET_CONNECT_TIMEOUT)
- ✅ Fonctionne avec Celery 5.3.4
- ✅ Documentation complète

**Configuration**:
```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_CACHE_URL,
        'OPTIONS': {
            'SOCKET_CONNECT_TIMEOUT': 5,  # Fonctionne avec redis 4.x
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'comparateur_prix',
    }
}
```

### Option 2: Redis 5.x avec django-redis (Moderne)
```python
# requirements.txt
redis==5.0.1
django-redis==5.4.0
celery==5.3.4
```

**Avantages**:
- ✅ Version moderne de redis
- ✅ Meilleures performances
- ✅ Support des nouvelles fonctionnalités Redis
- ✅ Gestion d'erreurs améliorée avec IGNORE_EXCEPTIONS

**Configuration**:
```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',  # Utiliser django-redis
        'LOCATION': REDIS_CACHE_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'IGNORE_EXCEPTIONS': True,  # Important: ne pas crasher si Redis est down
        },
        'KEY_PREFIX': 'comparateur_prix',
    }
}
```

### Option 3: Redis 5.x avec Django's RedisCache (Minuscules)
```python
# requirements.txt
redis==5.0.1
celery==5.3.4
```

**Configuration**:
```python
# config/settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_CACHE_URL,
        'OPTIONS': {
            'socket_connect_timeout': 5,  # Minuscules pour redis 5.x
            'socket_timeout': 5,
        },
        'KEY_PREFIX': 'comparateur_prix',
    }
}
```

**Note**: Cette option a causé des problèmes dans notre projet. Préférer Option 1 ou 2.

## ❌ Versions Non Compatibles

### Redis 3.x
- ❌ Trop ancien
- ❌ Manque de fonctionnalités
- ❌ Problèmes de sécurité

### Redis 6.x+
- ⚠️ Peut nécessiter des ajustements
- ⚠️ Changements d'API
- ⚠️ Non testé avec ce projet

## 🔧 Matrice de Compatibilité

| redis-py | django-redis | Django | Celery | Status |
|----------|--------------|--------|--------|--------|
| 4.6.0 | 5.4.0 | 5.1.2 | 5.3.4 | ✅ Recommandé |
| 5.0.1 | 5.4.0 | 5.1.2 | 5.3.4 | ✅ Avec django-redis |
| 5.0.1 | N/A | 5.1.2 | 5.3.4 | ⚠️ Problèmes connus |
| 4.5.x | 5.4.0 | 5.1.2 | 5.3.4 | ✅ Compatible |
| 3.x | 5.4.0 | 5.1.2 | 5.3.4 | ❌ Non recommandé |

## 🚀 Migration Recommandée

### Étape 1: Choisir la Solution

**Pour la Stabilité Maximale** (Recommandé):
```bash
# Revenir à redis 4.6.0
pip install redis==4.6.0
```

**Pour les Fonctionnalités Modernes**:
```bash
# Garder redis 5.0.1 mais utiliser django-redis
pip install redis==5.0.1 django-redis==5.4.0
```

### Étape 2: Mettre à Jour requirements.txt

**Option A: Redis 4.x (Stable)**
```python
# requirements.txt
redis==4.6.0  # Version stable et testée
django-redis==5.4.0
celery==5.3.4
```

**Option B: Redis 5.x avec django-redis**
```python
# requirements.txt
redis==5.0.1  # Version moderne
django-redis==5.4.0  # Nécessaire pour redis 5.x
celery==5.3.4
```

### Étape 3: Mettre à Jour settings.py

**Pour Option A (Redis 4.x)**:
```python
# Garder la configuration actuelle
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_CACHE_URL,
        'OPTIONS': {
            'SOCKET_CONNECT_TIMEOUT': 5,  # Majuscules OK avec redis 4.x
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'comparateur_prix',
    }
}
```

**Pour Option B (Redis 5.x + django-redis)**:
```python
# Utiliser django-redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_CACHE_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'IGNORE_EXCEPTIONS': True,  # Fallback automatique
        },
        'KEY_PREFIX': 'comparateur_prix',
    }
}
```

### Étape 4: Tester

```bash
# Tester localement
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
'value'

# Tester sur Railway
railway run python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
```

### Étape 5: Déployer

```bash
# Commit et push
git add requirements.txt config/settings.py
git commit -m "Migrer vers redis 4.6.0 pour stabilité"
git push

# Retirer FORCE_LOCAL_CACHE sur Railway
railway variables --unset FORCE_LOCAL_CACHE
```

## 📊 Comparaison des Options

### Redis 4.6.0 (Option A)
**Avantages**:
- ✅ Stable et éprouvé
- ✅ Pas de changements de configuration nécessaires
- ✅ Fonctionne immédiatement
- ✅ Documentation abondante

**Inconvénients**:
- ⚠️ Version plus ancienne
- ⚠️ Moins de fonctionnalités modernes

**Recommandé pour**: Production, stabilité maximale

### Redis 5.0.1 + django-redis (Option B)
**Avantages**:
- ✅ Version moderne
- ✅ Meilleures performances
- ✅ IGNORE_EXCEPTIONS pour fallback automatique
- ✅ Plus de fonctionnalités

**Inconvénients**:
- ⚠️ Nécessite django-redis
- ⚠️ Configuration plus complexe
- ⚠️ Moins testé dans ce projet

**Recommandé pour**: Nouveaux projets, fonctionnalités avancées

## 🔍 Diagnostic des Problèmes

### Problème: TypeError SOCKET_CONNECT_TIMEOUT
**Cause**: redis 5.x avec Django's RedisCache backend

**Solutions**:
1. Revenir à redis 4.6.0 (plus simple)
2. Utiliser django-redis avec redis 5.x
3. Utiliser des paramètres en minuscules (non recommandé)

### Problème: Redis Connection Failed
**Cause**: Redis non disponible ou mal configuré

**Solutions**:
1. Vérifier REDIS_URL
2. Activer IGNORE_EXCEPTIONS (avec django-redis)
3. Utiliser FORCE_LOCAL_CACHE comme fallback

### Problème: Celery ne démarre pas
**Cause**: Incompatibilité redis/celery

**Solutions**:
1. Vérifier que redis et celery sont compatibles
2. Utiliser redis 4.6.0 avec celery 5.3.4 (testé)

## 📝 Recommandation Finale

### Pour Ce Projet: Redis 4.6.0 ⭐

**Raison**:
- Stable et testé
- Pas de changements de configuration
- Compatible avec toutes les dépendances
- Fonctionne immédiatement

**Action**:
```bash
# 1. Mettre à jour requirements.txt
redis==4.6.0

# 2. Commit et push
git add requirements.txt
git commit -m "Revenir à redis 4.6.0 pour stabilité"
git push

# 3. Retirer FORCE_LOCAL_CACHE
railway variables --unset FORCE_LOCAL_CACHE

# 4. Vérifier
curl https://comparo.up.railway.app/api/health/
```

## 🔗 Ressources

- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [django-redis Documentation](https://github.com/jazzband/django-redis)
- [Django Cache Framework](https://docs.djangoproject.com/en/5.1/topics/cache/)
- [Celery with Redis](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html)

## ✅ Checklist de Migration

- [ ] Choisir la version de redis (4.6.0 recommandé)
- [ ] Mettre à jour requirements.txt
- [ ] Mettre à jour config/settings.py si nécessaire
- [ ] Tester localement
- [ ] Commit et push
- [ ] Retirer FORCE_LOCAL_CACHE sur Railway
- [ ] Vérifier que l'application fonctionne
- [ ] Tester les endpoints API
- [ ] Vérifier Celery
- [ ] Documenter les changements
