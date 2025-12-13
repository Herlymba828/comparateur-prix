#!/bin/bash
# Script pour tester Celery sur Railway

echo "🔍 Test de Celery sur Railway..."
echo ""

# Vérifier la santé de Celery
railway run python scripts/check_celery_health.py

echo ""
echo "✅ Test terminé"
