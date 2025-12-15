#!/bin/bash
# Script de démarrage pour Celery Worker sur Railway
# Ce service doit être créé séparément dans Railway Dashboard

echo "🚀 Démarrage de Celery Worker..."
echo "📡 Variables d'environnement:"
echo "   CELERY_BROKER_URL: ${CELERY_BROKER_URL:0:30}..."
echo "   DATABASE_URL: ${DATABASE_URL:0:30}..."

# Vérifier que les variables essentielles sont définies
if [ -z "$CELERY_BROKER_URL" ]; then
    echo "❌ ERREUR: CELERY_BROKER_URL non défini"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERREUR: DATABASE_URL non défini"
    exit 1
fi

# Démarrer Celery Worker
# --loglevel=info : Logs détaillés
# --concurrency=1 : 1 worker seulement
# --max-tasks-per-child=1000 : Recycler le worker après 1000 tâches
# --time-limit=3600 : Timeout de 1 heure par tâche
# --soft-time-limit=3300 : Soft timeout de 55 minutes

echo "⏳ Démarrage du worker Celery (1 worker)..."
exec celery -A config worker \
    --loglevel=info \
    --concurrency=1 \
    --max-tasks-per-child=1000 \
    --time-limit=3600 \
    --soft-time-limit=3300 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat
