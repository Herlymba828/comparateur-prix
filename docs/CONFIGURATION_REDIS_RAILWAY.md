# 🔴 Configuration Redis pour Railway

Guide complet pour configurer Redis sur Railway pour votre application Django.

---

## 🚀 Configuration sur Railway

### Étape 1 : Ajouter le service Redis

1. Allez sur https://railway.app
2. Ouvrez votre projet
3. Cliquez sur **"+ New"**
4. Sélectionnez **"Database"** → **"Add Redis"**
5. Attendez 1-2 minutes que Railway crée l'instance Redis

✅ **C'est tout !** Railway configure automatiquement `REDIS_URL`.

---

### Étape 2 : Vérifier la variable REDIS_URL

Railway ajoute automatiquement `REDIS_URL` dans les variables d'environnement de votre service Django.

**Pour vérifier :**
1. Dans Railway → Votre service Django → **Variables**
2. Cherchez `REDIS_URL`
3. Vous devriez voir quelque chose comme : `redis://default:password@redis.railway.internal:6379`

**Note :** Railway utilise le format interne `.railway.internal` pour la communication entre services.

---

### Étape 3 : Configuration automatique

Votre application Django est déjà configurée pour utiliser `REDIS_URL` automatiquement :

```python
# Dans config/settings.py
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
```

**Aucune configuration supplémentaire nécessaire !**

---

## 🔧 Configuration avancée (optionnel)

### Utiliser des bases Redis distinctes

Si vous voulez séparer le cache Django et Celery :

1. **Dans Railway**, ajoutez une variable d'environnement :
   ```
   REDIS_CACHE_URL=redis://default:password@redis.railway.internal:6379/1
   ```

2. **Configuration automatique** :
   - Celery utilisera `REDIS_URL` (base 0)
   - Cache Django utilisera `REDIS_CACHE_URL` (base 1) si défini, sinon `REDIS_URL`

---

## ✅ Vérification

### Vérifier la connexion Redis

**Via Railway CLI :**
```bash
railway run python manage.py shell
```

Puis dans le shell Python :
```python
import redis
import os

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
r = redis.from_url(redis_url)
r.ping()  # Devrait retourner True
print("✅ Redis connecté !")
```

### Vérifier Celery

**Via Railway CLI :**
```bash
railway run celery -A config inspect ping
```

Vous devriez voir :
```
-> celery@hostname: OK
```

---

## 🐛 Dépannage

### Erreur : "Connection refused"

**Cause :** Redis n'est pas encore démarré ou `REDIS_URL` n'est pas configuré.

**Solution :**
1. Vérifiez que le service Redis est créé dans Railway
2. Vérifiez que `REDIS_URL` est présent dans les variables d'environnement
3. Redéployez votre application Django

### Erreur : "Module 'redis' not found"

**Solution :**
Vérifiez que `redis` est dans `requirements.txt` :
```bash
redis==5.0.1
```

### Erreur : "Celery broker connection failed"

**Solution :**
1. Vérifiez que Redis est démarré
2. Vérifiez que `REDIS_URL` est correct
3. Vérifiez les logs Railway pour plus de détails

---

## 📊 Utilisation

### Cache Django

Le cache Django utilise automatiquement Redis en production :

```python
from django.core.cache import cache

# Mettre en cache
cache.set('ma_cle', 'ma_valeur', 3600)

# Récupérer du cache
valeur = cache.get('ma_cle')
```

### Celery

Celery utilise automatiquement Redis comme broker :

```python
from apps.tasks import ma_tache

# Exécuter une tâche asynchrone
result = ma_tache.delay(arg1, arg2)
```

---

## 🔄 Redéploiement

Après avoir ajouté Redis :

1. Railway redéploiera automatiquement votre application
2. Ou redéployez manuellement :
   ```bash
   railway up
   ```

---

## 📝 Variables d'environnement

### Variables automatiques (fournies par Railway)

- `REDIS_URL` : URL de connexion Redis (automatique)

### Variables optionnelles

- `REDIS_CACHE_URL` : URL Redis pour le cache Django (si différent de Celery)
- `CELERY_BROKER_URL` : URL Redis pour Celery broker (par défaut = REDIS_URL)
- `CELERY_RESULT_BACKEND` : URL Redis pour les résultats Celery (par défaut = REDIS_URL)

---

## ✅ Checklist

- [ ] Service Redis créé dans Railway
- [ ] `REDIS_URL` visible dans les variables d'environnement
- [ ] Application redéployée
- [ ] Connexion Redis vérifiée
- [ ] Celery fonctionne correctement
- [ ] Cache Django fonctionne

---

## 🎯 Résumé

1. **Créer Redis** : Railway → "+ New" → "Database" → "Add Redis"
2. **Vérifier** : `REDIS_URL` est automatiquement ajouté
3. **C'est tout !** Votre application utilise Redis automatiquement

**Pas besoin de configuration manuelle !** 🎉

