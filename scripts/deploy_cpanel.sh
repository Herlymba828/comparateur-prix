#!/bin/bash
# Script de déploiement pour cPanel
# Usage: bash scripts/deploy_cpanel.sh

set -e  # Arrêter en cas d'erreur

echo "=========================================="
echo "DÉPLOIEMENT DJANGO SUR CPANEL"
echo "=========================================="
echo ""

# Variables
VENV_PATH="/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11"
PROJECT_PATH="/home/rs2694021ez6eg8n/public_html/comparer"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Êtes-vous dans le répertoire du projet?"
    exit 1
fi

echo "✅ Répertoire du projet trouvé"
echo ""

# Activer l'environnement virtuel
echo "📦 Activation de l'environnement virtuel..."
source "$VENV_PATH/bin/activate"
echo "✅ Environnement virtuel activé"
echo ""

# Mettre à jour pip
echo "🔄 Mise à jour de pip..."
pip install --upgrade pip --quiet
echo "✅ pip mis à jour"
echo ""

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install -r requirements.txt --quiet
echo "✅ Dépendances installées"
echo ""

# Vérifier la configuration
echo "🔍 Vérification de la configuration Django..."
python manage.py check --deploy || {
    echo "⚠️  Des avertissements ont été détectés, mais le déploiement continue..."
}
echo ""

# Appliquer les migrations
echo "🗄️  Application des migrations..."
python manage.py migrate --noinput
echo "✅ Migrations appliquées"
echo ""

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput
echo "✅ Fichiers statiques collectés"
echo ""

# Définir les permissions
echo "🔐 Configuration des permissions..."
chmod 755 manage.py
chmod 755 index.py 2>/dev/null || true
chmod 755 passenger_wsgi.py 2>/dev/null || true
chmod 600 .env 2>/dev/null || true
chmod 755 staticfiles 2>/dev/null || true
chmod 755 media 2>/dev/null || true
echo "✅ Permissions configurées"
echo ""

echo "=========================================="
echo "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS!"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "1. Vérifiez que le fichier .env est correctement configuré"
echo "2. Testez l'application: https://ftp.navixtechnology.com"
echo "3. Vérifiez les logs en cas d'erreur"
echo ""

