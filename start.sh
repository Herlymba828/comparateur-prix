#!/bin/bash
# Ne pas utiliser set -e pour permettre à l'application de démarrer même si les migrations échouent
# Railway redémarrera le conteneur si Gunicorn crash, donc on veut que Gunicorn démarre toujours

echo "🚀 Démarrage de l'application Django..."

# Vérifier que le port est défini (Railway définit automatiquement PORT)
if [ -z "$PORT" ]; then
    echo "⚠️  PORT non défini, utilisation du port 8080 par défaut"
    export PORT=8080
else
    echo "📡 Port détecté depuis Railway: $PORT"
fi

# Afficher toutes les variables d'environnement liées au port pour le diagnostic
echo "🔍 Variables d'environnement Railway:"
echo "   PORT=$PORT"
echo "   RAILWAY_ENVIRONMENT=${RAILWAY_ENVIRONMENT:-non défini}"
echo "   RAILWAY_PROJECT_ID=${RAILWAY_PROJECT_ID:-non défini}"

# Appliquer les migrations (ne pas faire échouer le démarrage si ça échoue)
echo "📦 Application des migrations..."
if python manage.py migrate --noinput; then
    echo "✅ Migrations appliquées avec succès"
else
    echo "⚠️  Erreur lors de l'application des migrations"
    echo "   Les migrations seront réessayées au prochain démarrage"
    echo "   L'application démarre quand même pour permettre les health checks"
fi

# Collecter les fichiers statiques (ne pas faire échouer le démarrage si ça échoue)
echo "📁 Collecte des fichiers statiques..."
if python manage.py collectstatic --noinput; then
    echo "✅ Fichiers statiques collectés avec succès"
else
    echo "⚠️  Erreur lors de la collecte des fichiers statiques"
    echo "   L'application démarre quand même"
fi

# Démarrer Gunicorn (c'est la partie critique - doit toujours démarrer)
echo "✅ Démarrage du serveur Gunicorn..."
echo "   📍 Écoute sur: 0.0.0.0:$PORT"
echo "   🔗 Health check: http://0.0.0.0:$PORT/api/health/"
echo "   🔗 API Docs: http://0.0.0.0:$PORT/api/docs/"
echo "   ⚙️  Workers: 2"
echo "   ⏱️  Timeout: 120s"

# Note: Ne pas ajouter de sleep ici car Railway fait un health check très rapidement
# Gunicorn avec --preload charge l'application avant de forker, ce qui est plus rapide
# L'endpoint /api/health/ et / ne nécessitent pas de base de données, donc ils répondront immédiatement

# Utiliser exec pour que Gunicorn remplace le processus shell
# Ajouter des options pour améliorer la stabilité
# Note: Railway fait un health check automatique, donc on doit s'assurer que l'application répond rapidement
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --keep-alive 5 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --preload

