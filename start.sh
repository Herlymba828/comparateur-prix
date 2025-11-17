#!/bin/bash
set -e

echo "🚀 Démarrage de l'application Django..."

# Appliquer les migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput || {
    echo "⚠️  Erreur lors de l'application des migrations"
    echo "   Les migrations seront réessayées au prochain démarrage"
}

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput || {
    echo "⚠️  Erreur lors de la collecte des fichiers statiques"
}

# Démarrer Gunicorn
echo "✅ Démarrage du serveur Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT

