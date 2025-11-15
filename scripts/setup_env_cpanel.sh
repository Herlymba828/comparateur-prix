#!/bin/bash
# Script d'aide pour configurer le fichier .env sur cPanel

set -e

echo "============================================"
echo "Configuration du fichier .env pour cPanel"
echo "============================================"
echo ""

# Vérifier si on est dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur : Ce script doit être exécuté depuis la racine du projet Django"
    echo "   (répertoire contenant manage.py)"
    exit 1
fi

# Vérifier si .env existe déjà
if [ -f ".env" ]; then
    echo "⚠️  Le fichier .env existe déjà."
    read -p "Voulez-vous le sauvegarder et créer un nouveau ? (o/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[OoYy]$ ]]; then
        cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        echo "✅ Fichier .env sauvegardé"
    else
        echo "❌ Annulé. Le fichier .env n'a pas été modifié."
        exit 0
    fi
fi

echo ""
echo "Configuration du fichier .env"
echo "=============================="
echo ""

# Générer une clé secrète Django
echo "Génération de la clé secrète Django..."
SECRET_KEY=$(python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

# Demander les informations à l'utilisateur
read -p "Mode DEBUG (False pour production) [False]: " DEBUG_MODE
DEBUG_MODE=${DEBUG_MODE:-False}

read -p "Nom de la base de données PostgreSQL: " DB_NAME
read -p "Utilisateur PostgreSQL: " DB_USER
read -sp "Mot de passe PostgreSQL: " DB_PASSWORD
echo ""
read -p "Hôte PostgreSQL [localhost]: " DB_HOST
DB_HOST=${DB_HOST:-localhost}
read -p "Port PostgreSQL [5432]: " DB_PORT
DB_PORT=${DB_PORT:-5432}

read -p "Hôtes autorisés (séparés par des virgules, optionnel): " ALLOWED_HOSTS

# Créer le fichier .env
cat > .env << EOF
# ============================================
# Configuration Django - PRODUCTION
# Généré le $(date)
# ============================================

# Mode Debug (False en production)
DJANGO_DEBUG=${DEBUG_MODE}

# Clé secrète Django (générée automatiquement)
DJANGO_SECRET_KEY=${SECRET_KEY}

# Configuration PostgreSQL
DB_ENGINE=postgresql
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}

# SSL PostgreSQL (False par défaut sur cPanel)
POSTGRES_SSL_REQUIRE=False

EOF

# Ajouter les hôtes autorisés si fournis
if [ ! -z "$ALLOWED_HOSTS" ]; then
    echo "DJANGO_ALLOWED_HOSTS=${ALLOWED_HOSTS}" >> .env
fi

# Ajouter la configuration ML
cat >> .env << EOF

# Initialisation des modèles ML au démarrage (False pour économiser la mémoire)
RECO_INIT_MODELS_ON_STARTUP=False
EOF

# Définir les permissions
chmod 600 .env

echo ""
echo "✅ Fichier .env créé avec succès !"
echo ""
echo "Prochaines étapes :"
echo "1. Vérifiez le fichier .env : cat .env"
echo "2. Testez la connexion : python manage.py dbshell"
echo "3. Appliquez les migrations : python manage.py migrate"
echo "4. Vérifiez la configuration : python manage.py check --deploy"
echo ""

