#!/bin/bash
# Script pour tester la base PostgreSQL sur Railway

echo "🔍 Test de la base de données PostgreSQL sur Railway..."
echo ""

# Copier le script de vérification
railway run python scripts/verify_postgresql.py

echo ""
echo "✅ Test terminé"
