#!/bin/bash
# Script de démarrage pour Celery Beat sur Railway
# Ce service doit être créé séparément dans Railway Dashboard

echo "🚀 Démarrage de Celery Beat (Scheduler)..."
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

# Créer le répertoire pour le fichier de schedule
mkdir -p /tmp/celery

# Démarrer Celery Beat
# --loglevel=info : Logs détaillés
# --scheduler=django_celery_beat.schedulers:DatabaseScheduler : Utiliser la base de données pour les schedules
# --pidfile=/tmp/celery/beat.pid : Fichier PID

echo "⏳ Démarrage du scheduler Celery Beat..."
exec celery -A config beat \
    --loglevel=info \
    --scheduler=django_celery_beat.schedulers:DatabaseScheduler \
    --pidfile=/tmp/celery/beat.pid
