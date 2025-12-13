# Débogage du Déploiement Railway

## Date: 13 décembre 2025

## Problèmes Résolus ✅

### 1. Validation du mot de passe DATABASE_URL
**Problème**: L'application refusait de démarrer car la validation du mot de passe échouait même avec `DATABASE_URL` défini.

**Solution**: Modifié `config/settings.py` pour skip la validation quand `DATABASE_URL` est utilisé (le mot de passe est dans l'URL).

```python
if using_database_url:
    # DATABASE_URL est utilisé, le mot de passe est dans l'URL - pas de validation nécessaire
    pass
elif not db_password:
    # Validation seulement si DATABASE_URL n'est pas utilisé
    raise ImproperlyConfigured(error_msg)
```

### 2. Variables Redis avec références non résolues
**Problème**: Les variables `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, et `REDIS_CACHE_URL` étaient définies comme `${REDIS_URL}` (référence littérale non résolue).

**Solution**: Remplacé par l'URL Redis complète:
```bash
railway variables --set CELERY_BROKER_URL="redis://default:WJVWXycBmIRVlZZVYhbSedvzRjInWfia@redis.railway.internal:6379"
railway variables --set CELERY_RESULT_BACKEND="redis://default:WJVWXycBmIRVlZZVYhbSedvzRjInWfia@redis.railway.internal:6379"
railway variables --set REDIS_CACHE_URL="redis://default:WJVWXycBmIRVlZZVYhbSedvzRjInWfia@redis.railway.internal:6379"
```

### 3. PYTHONPATH manquant pour le module 'apps'
**Problème**: Les modules `apps.*` ne pouvaient pas être importés car le répertoire racine n'était pas dans le PYTHONPATH.

**Solution**: Ajouté la configuration du PYTHONPATH dans:
- `config/wsgi.py`
- `config/celery.py`
- `manage.py`

```python
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
```

## Problème Actuel ❌

### Erreur 500 sur tous les endpoints

**Symptômes**:
- L'application démarre (migrations OK, collectstatic OK)
- Gunicorn démarre et écoute sur le port 8080
- Les workers Gunicorn crashent avec le code 1
- Tous les endpoints retournent une erreur 500

**Logs observés**:
```
[2025-12-13 20:34:15 +0000] [1] [INFO] Starting gunicorn 21.2.0
[2025-12-13 20:34:15 +0000] [1] [INFO] Listening at: http://0.0.0.0:8080 (1)
[2025-12-13 20:34:15 +0000] [1] [INFO] Using worker: sync
[2025-12-13 20:34:15 +0000] [74] [INFO] Booting worker with pid: 74
[2025-12-13 20:34:15 +0000] [75] [INFO] Booting worker with pid: 75
[2025-12-13 20:34:18 +0000] [1] [ERROR] Worker (pid:73) exited with code 1
```

**Tests effectués**:
1. ✅ Désactivation de Celery → Pas d'effet
2. ✅ Simplification du endpoint health → Pas d'effet
3. ✅ Désactivation des middlewares personnalisés → Pas d'effet
4. ✅ Fix du PYTHONPATH → Pas d'effet (mais nécessaire)
5. ✅ Configuration Gunicorn avec logging détaillé → En cours

**Hypothèses restantes**:
1. Problème d'import d'un module spécifique lors du chargement de l'application
2. Problème de connexion à la base de données lors de la première requête
3. Problème avec une dépendance manquante ou incompatible
4. Problème avec les fichiers statiques ou media
5. Problème avec les clés JWT ou autres secrets

**Prochaines étapes**:
1. Analyser les logs Gunicorn détaillés avec la nouvelle configuration
2. Créer un endpoint de diagnostic ultra-minimal
3. Vérifier les dépendances dans requirements.txt
4. Tester l'import de chaque application Django individuellement
5. Vérifier les variables d'environnement critiques (JWT_PRIVATE_KEY_PATH, etc.)

## Variables d'Environnement Railway

### Base de données ✅
- `DATABASE_URL`: Défini (PostgreSQL interne)
- `DATABASE_PUBLIC_URL`: Défini (PostgreSQL public)

### Redis ✅
- `REDIS_URL`: Défini
- `CELERY_BROKER_URL`: Défini (URL complète)
- `CELERY_RESULT_BACKEND`: Défini (URL complète)
- `REDIS_CACHE_URL`: Défini (URL complète)

### Django ✅
- `DJANGO_SECRET_KEY`: Défini
- `DJANGO_DEBUG`: False
- `DJANGO_ALLOWED_HOSTS`: Défini

### Potentiellement problématiques ⚠️
- `JWT_PRIVATE_KEY_PATH`: secrets/jwt_private.pem (fichier existe?)
- `JWT_PUBLIC_KEY_PATH`: secrets/jwt_public.pem (fichier existe?)
- `APPLE_PRIVATE_KEY_PEM`: Défini mais peut-être invalide
- `ELASTICSEARCH_HOST`: localhost (non disponible sur Railway)

## Commandes Utiles

```bash
# Voir les logs Railway
railway logs

# Tester l'endpoint health
curl https://comparo.up.railway.app/api/health/

# Voir les variables d'environnement
railway variables

# Redéployer
git push

# Tester localement avec railway run
railway run python manage.py check
```
