#!/bin/bash
# Script de démarrage pour Celery Worker sur Railway
# Ce service doit être créé séparément dans Railway Dashboard
# Configuration optimisée pour Railway avec 4 workers

set -e  # Arrêter le script en cas d'erreur

echo "🚀 Démarrage de Celery Worker..."
echo "📡 Variables d'environnement:"
echo "   CELERY_BROKER_URL: ${CELERY_BROKER_URL:0:30}..."
echo "   DATABASE_URL: ${DATABASE_URL:0:30}..."
echo "   DJANGO_SETTINGS_MODULE: ${DJANGO_SETTINGS_MODULE:-config.settings}"

# Vérifier que les variables essentielles sont définies
if [ -z "$CELERY_BROKER_URL" ]; then
    echo "❌ ERREUR: CELERY_BROKER_URL non défini"
    echo "   Assurez-vous que Redis est configuré sur Railway"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERREUR: DATABASE_URL non défini"
    echo "   Assurez-vous que PostgreSQL est lié au service Celery Worker"
    exit 1
fi

# Définir les variables par défaut si nécessaire
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings}
export CELERY_LOGLEVEL=${CELERY_LOGLEVEL:-info}

# Créer le répertoire pour les logs Celery
mkdir -p /tmp/celery

echo "⏳ Démarrage du worker Celery (4 workers, configuration optimisée)..."
echo "   Logs: /tmp/celery/worker.log"
echo "   PID: $$"

# Démarrer Celery Worker avec configuration optimisée pour Railway
# --loglevel=info : Logs détaillés
# --concurrency=4 : 4 workers pour meilleure performance
# --max-tasks-per-child=1000 : Recycler le worker après 1000 tâches (évite les fuites mémoire)
# --time-limit=3600 : Timeout dur de 1 heure par tâche
# --soft-time-limit=3300 : Soft timeout de 55 minutes (permet au worker de nettoyer)
# --without-gossip : Désactiver la communication entre workers
# --without-mingle : Désactiver la synchronisation au démarrage
# --without-heartbeat : Désactiver les heartbeats (réduit la charge)
# --pool=prefork : Pool par défaut (meilleur pour multi-workers)
# --prefetch-multiplier=4 : Charger 4 tâches à la fois (1 par worker)
# --broker-connection-retry-on-startup : Réessayer la connexion au broker au démarrage

exec celery -A config worker \
    --loglevel=${CELERY_LOGLEVEL} \
    --concurrency=4 \
    --pool=prefork \
    --max-tasks-per-child=1000 \
    --time-limit=3600 \
    --soft-time-limit=3300 \
    --prefetch-multiplier=4 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat \
    --broker-connection-retry-on-startup \
    --logfile=/tmp/celery/worker.log \
    --pidfile=/tmp/celery/worker.pid
