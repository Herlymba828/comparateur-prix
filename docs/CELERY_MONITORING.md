# 🔍 Monitoring et Gestion de Celery

## Vue d'ensemble

Ce document décrit le système de monitoring et de gestion automatique des crashs pour Celery Worker et Beat.

## Scripts de Monitoring

### 1. `check_celery_health.py`

Vérifie la santé de Celery Worker et Beat.

**Utilisation:**
```bash
python scripts/check_celery_health.py
```

**Vérifications:**
- ✅ Connexion Redis
- ✅ Workers actifs
- ✅ Tâches en cours
- ✅ Tâches périodiques (Beat)
- ✅ Dernières exécutions

**Exit codes:**
- `0`: Tout est OK
- `1`: Problèmes détectés

### 2. `celery_monitor.py`

Monitoring continu avec auto-restart en cas de crash.

**Utilisation:**
```bash
python scripts/celery_monitor.py
```

**Fonctionnalités:**
- 🔄 Démarrage automatique de Worker et Beat
- 🔍 Vérification toutes les 10 secondes
- 🚀 Redémarrage automatique en cas de crash
- 🛡️ Protection contre les boucles de redémarrage (max 5 en 5 minutes)
- 📊 Logs détaillés des événements

**Signaux supportés:**
- `SIGINT` (Ctrl+C): Arrêt propre
- `SIGTERM`: Arrêt propre

### 3. `verify_postgresql.py`

Vérification complète de la base de données PostgreSQL.

**Utilisation:**
```bash
python scripts/verify_postgresql.py
```

**Vérifications:**
- ✅ Connexion PostgreSQL/SQLite
- ✅ Tables et nombre de lignes
- ✅ Indexes de performance
- ✅ Données des modèles Django
- ✅ Taille de la base
- ✅ Contraintes et clés étrangères
- ✅ Statistiques de performance

## Configuration Railway

### Variables d'environnement

Assurez-vous que ces variables sont définies:

```bash
# Redis
REDIS_URL=redis://default:***@redis.railway.internal:6379

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# PostgreSQL (automatique sur Railway)
DATABASE_URL=postgresql://...
```

### Procfile

Le `start.sh` gère automatiquement:
1. Migrations
2. Collecte des fichiers statiques
3. Démarrage de Celery Worker
4. Démarrage de Celery Beat
5. Démarrage de Gunicorn

## Gestion des Crashs

### Stratégie de Redémarrage

Le monitoring implémente une stratégie intelligente:

1. **Détection**: Vérification toutes les 10 secondes
2. **Redémarrage**: Automatique en cas de crash
3. **Limite**: Maximum 5 redémarrages en 5 minutes
4. **Logs**: Capture des sorties stderr/stdout

### Causes Communes de Crash

#### Worker

- **Mémoire insuffisante**: Augmenter `--max-tasks-per-child`
- **Timeout**: Ajuster `--time-limit` et `--soft-time-limit`
- **Connexion Redis perdue**: Vérifier la stabilité de Redis
- **Tâche bloquante**: Utiliser des timeouts appropriés

#### Beat

- **Base de données inaccessible**: Vérifier la connexion PostgreSQL
- **Tâches périodiques invalides**: Vérifier la configuration
- **Conflits de schedule**: Éviter les overlaps

### Configuration Optimale

```python
# config/celery.py
app.conf.update(
    # Worker
    worker_max_tasks_per_child=100,  # Redémarre après 100 tâches
    worker_prefetch_multiplier=1,    # Une tâche à la fois
    
    # Timeouts
    task_time_limit=300,             # 5 minutes max
    task_soft_time_limit=240,        # Warning à 4 minutes
    
    # Retry
    task_acks_late=True,             # Acknowledge après exécution
    task_reject_on_worker_lost=True, # Rejeter si worker crash
    
    # Beat
    beat_scheduler='django_celery_beat.schedulers:DatabaseScheduler',
)
```

## Commandes Utiles

### Vérifier l'état

```bash
# Santé de Celery
railway run python scripts/check_celery_health.py

# Base de données
railway run python scripts/verify_postgresql.py

# Logs en temps réel
railway logs --tail
```

### Redémarrer manuellement

```bash
# Redéployer l'application
railway up

# Ou redémarrer via l'interface Railway
```

### Inspecter Celery

```bash
# Workers actifs
railway run celery -A config inspect active

# Tâches enregistrées
railway run celery -A config inspect registered

# Stats
railway run celery -A config inspect stats
```

## Monitoring en Production

### Métriques à Surveiller

1. **Worker**
   - Nombre de workers actifs
   - Tâches en cours
   - Tâches échouées
   - Temps d'exécution moyen

2. **Beat**
   - Tâches périodiques actives
   - Dernière exécution
   - Tâches manquées

3. **Redis**
   - Connexions actives
   - Mémoire utilisée
   - Latence

4. **PostgreSQL**
   - Connexions actives
   - Taille de la base
   - Cache hit ratio
   - Requêtes lentes

### Alertes Recommandées

- ❌ Worker down > 1 minute
- ❌ Beat down > 1 minute
- ⚠️ Tâches échouées > 10%
- ⚠️ Temps d'exécution > 2 minutes
- ⚠️ Redis mémoire > 80%
- ⚠️ PostgreSQL connexions > 80%

## Dépannage

### Worker ne démarre pas

```bash
# Vérifier les logs
railway logs --tail | grep celery

# Vérifier Redis
railway run python -c "from django.core.cache import cache; print(cache.get('test'))"

# Tester manuellement
railway run celery -A config worker --loglevel=debug
```

### Beat ne démarre pas

```bash
# Vérifier la base de données
railway run python manage.py migrate

# Vérifier les tâches périodiques
railway run python manage.py shell
>>> from django_celery_beat.models import PeriodicTask
>>> PeriodicTask.objects.all()

# Tester manuellement
railway run celery -A config beat --loglevel=debug
```

### Tâches bloquées

```bash
# Purger la queue
railway run celery -A config purge

# Révoquer une tâche
railway run celery -A config revoke <task_id>

# Inspecter les tâches actives
railway run celery -A config inspect active
```

## Optimisations

### Performance

1. **Concurrency**: Ajuster selon les ressources
   ```bash
   celery -A config worker --concurrency=4
   ```

2. **Prefetch**: Limiter pour les tâches longues
   ```python
   worker_prefetch_multiplier=1
   ```

3. **Max tasks per child**: Éviter les fuites mémoire
   ```python
   worker_max_tasks_per_child=100
   ```

### Fiabilité

1. **Acks late**: Garantir l'exécution
   ```python
   task_acks_late=True
   ```

2. **Retry**: Réessayer en cas d'échec
   ```python
   @app.task(bind=True, max_retries=3)
   def my_task(self):
       try:
           # ...
       except Exception as exc:
           raise self.retry(exc=exc, countdown=60)
   ```

3. **Timeouts**: Éviter les blocages
   ```python
   task_time_limit=300
   task_soft_time_limit=240
   ```

## Ressources

- [Documentation Celery](https://docs.celeryproject.org/)
- [Django Celery Beat](https://django-celery-beat.readthedocs.io/)
- [Railway Docs](https://docs.railway.app/)
