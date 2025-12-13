# 🔧 Résolution des Crashs Celery

## Problème Identifié

Les logs Railway montrent que Celery Worker et Beat crashent après le démarrage :

```
[2025-12-13 07:06:47 +0000] [1] [ERROR] Worker (pid:105) exited with code 1
[2025-12-13 07:06:47 +0000] [1] [ERROR] Worker (pid:102) exited with code 1
```

## Causes Possibles

### 1. Variable Redis Non Résolue

Le log montre :
```
URL Redis invalide (ne commence pas par redis:// ou rediss://): ${REDIS_URL}
```

La variable `${REDIS_URL}` n'est pas interpolée correctement dans Railway.

### 2. Dépendances Manquantes

Celery Beat nécessite `django-celery-beat` qui pourrait ne pas être installé.

### 3. Configuration Celery

Les processus Celery peuvent crasher si la configuration est incorrecte.

## Solutions

### Solution 1: Corriger la Variable Redis dans Railway

Dans Railway, la variable doit être définie directement, pas avec `${}`:

1. Aller dans Railway Dashboard
2. Variables d'environnement
3. Modifier `CELERY_BROKER_URL` et `CELERY_RESULT_BACKEND`:
   - Au lieu de: `${REDIS_URL}`
   - Utiliser: `${{REDIS_URL}}` (notation Railway)
   - Ou copier directement l'URL Redis

### Solution 2: Vérifier les Dépendances

Assurez-vous que `requirements.txt` contient :

```txt
celery==5.3.4
redis==5.0.1
django-celery-beat==2.5.0
django-celery-results==2.5.1
```

### Solution 3: Simplifier le Démarrage

Modifier `start.sh` pour mieux gérer les erreurs :

```bash
#!/bin/bash
set -e  # Arrêter en cas d'erreur

# Fonction pour logger
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Fonction pour vérifier Redis
check_redis() {
    if [ -z "$REDIS_URL" ]; then
        log "⚠️ REDIS_URL non défini, Celery ne fonctionnera pas"
        return 1
    fi
    log "✅ REDIS_URL défini: ${REDIS_URL:0:20}..."
    return 0
}

# Migrations
log "📦 Application des migrations..."
python manage.py migrate --noinput
log "✅ Migrations appliquées"

# Collecte des fichiers statiques
log "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
log "✅ Fichiers statiques collectés"

# Vérifier Redis avant de démarrer Celery
if check_redis; then
    # Démarrer Celery Worker
    log "🔄 Démarrage de Celery Worker..."
    celery -A config worker \
        --loglevel=info \
        --concurrency=2 \
        --max-tasks-per-child=100 \
        --time-limit=300 \
        --soft-time-limit=240 \
        --logfile=/tmp/celery-worker.log \
        --detach
    
    sleep 2
    
    # Démarrer Celery Beat
    log "⏰ Démarrage de Celery Beat..."
    celery -A config beat \
        --loglevel=info \
        --scheduler=django_celery_beat.schedulers:DatabaseScheduler \
        --logfile=/tmp/celery-beat.log \
        --detach
    
    log "✅ Celery démarré"
else
    log "⚠️ Celery non démarré (Redis non disponible)"
fi

# Démarrer Gunicorn
log "✅ Démarrage du serveur Gunicorn..."
log "   📍 Écoute sur: 0.0.0.0:${PORT:-8080}"
log "   🔗 Health check: http://0.0.0.0:${PORT:-8080}/api/health/"

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### Solution 4: Désactiver Celery Temporairement

Si Celery n'est pas critique immédiatement, on peut le désactiver :

```bash
#!/bin/bash
# Version sans Celery

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:${PORT:-8080} \
    --workers 2 \
    --timeout 120
```

## Vérification

### 1. Vérifier les Variables Railway

```bash
railway variables
```

Doit afficher :
- `REDIS_URL`: URL complète Redis
- `CELERY_BROKER_URL`: Doit pointer vers Redis
- `CELERY_RESULT_BACKEND`: Doit pointer vers Redis

### 2. Tester Localement

```bash
# Avec les variables Railway
railway run python scripts/check_celery_health.py
```

### 3. Vérifier les Logs

```bash
railway logs --lines 100
```

Chercher :
- ✅ "Celery Worker démarré"
- ✅ "Celery Beat démarré"
- ❌ "Worker exited with code 1"

## Configuration Recommandée Railway

### Variables d'Environnement

```env
# Redis (fourni par Railway)
REDIS_URL=redis://default:***@redis.railway.internal:6379

# Celery (utiliser la notation Railway)
CELERY_BROKER_URL=${{REDIS_URL}}
CELERY_RESULT_BACKEND=${{REDIS_URL}}

# Django
DJANGO_SECRET_KEY=<votre-clé-secrète>
DEBUG=False
ALLOWED_HOSTS=.railway.app

# PostgreSQL (fourni par Railway)
DATABASE_URL=postgresql://...
```

### Procfile (Alternative)

Si `start.sh` pose problème, utiliser un Procfile :

```procfile
web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A config worker --loglevel=info
beat: celery -A config beat --loglevel=info --scheduler=django_celery_beat.schedulers:DatabaseScheduler
```

Puis dans Railway, déployer seulement le process `web`.

## Monitoring Post-Déploiement

### 1. Health Check

```bash
curl https://comparo.up.railway.app/api/health/
```

### 2. Diagnostic Complet

```bash
curl https://comparo.up.railway.app/api/diagnostic/
```

### 3. Vérifier Celery

```bash
railway run python scripts/check_celery_health.py
```

### 4. Vérifier PostgreSQL

```bash
railway run python scripts/verify_postgresql.py
```

## Prochaines Étapes

1. ✅ Corriger la variable `REDIS_URL` dans Railway
2. ✅ Redéployer l'application
3. ✅ Vérifier les logs
4. ✅ Tester les endpoints
5. ✅ Activer le monitoring

## Support

Si le problème persiste :

1. Vérifier les logs détaillés : `railway logs --lines 200`
2. Tester la connexion Redis : `railway run python -c "from django.core.cache import cache; print(cache.get('test'))"`
3. Vérifier les processus : `railway ps`
4. Consulter la documentation Railway : https://docs.railway.app/
