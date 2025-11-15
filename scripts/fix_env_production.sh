#!/bin/bash
# Script pour corriger automatiquement le fichier .env pour la production

set -e

echo "============================================"
echo "Correction du fichier .env pour la production"
echo "============================================"
echo ""

# Vérifier si on est dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur : Ce script doit être exécuté depuis la racine du projet Django"
    exit 1
fi

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    echo "❌ Erreur : Le fichier .env n'existe pas"
    echo "   Créez d'abord le fichier .env avec vos configurations"
    exit 1
fi

# Sauvegarder le fichier .env
BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
cp .env "$BACKUP_FILE"
echo "✅ Fichier .env sauvegardé dans $BACKUP_FILE"
echo ""

# Créer un fichier temporaire avec les corrections
TEMP_FILE=$(mktemp)

# Lire le fichier .env ligne par ligne et appliquer les corrections
while IFS= read -r line || [ -n "$line" ]; do
    # Ignorer les lignes vides et les commentaires
    if [[ -z "$line" ]] || [[ "$line" =~ ^[[:space:]]*# ]]; then
        echo "$line" >> "$TEMP_FILE"
        continue
    fi
    
    # Extraire la clé et la valeur
    if [[ "$line" =~ ^([^=]+)=(.*)$ ]]; then
        KEY="${BASH_REMATCH[1]}"
        VALUE="${BASH_REMATCH[2]}"
        
        # Corriger DJANGO_DEBUG
        if [[ "$KEY" == "DJANGO_DEBUG" ]]; then
            echo "🔧 Correction: DJANGO_DEBUG=True → False"
            echo "DJANGO_DEBUG=False" >> "$TEMP_FILE"
            continue
        fi
        
        # Corriger POSTGRES_SSL_REQUIRE
        if [[ "$KEY" == "POSTGRES_SSL_REQUIRE" ]]; then
            echo "🔧 Correction: POSTGRES_SSL_REQUIRE=True → False"
            echo "POSTGRES_SSL_REQUIRE=False" >> "$TEMP_FILE"
            continue
        fi
        
        # Corriger DJANGO_ALLOWED_HOSTS
        if [[ "$KEY" == "DJANGO_ALLOWED_HOSTS" ]]; then
            if [[ ! "$VALUE" =~ ftp\.navixtechnology\.com ]]; then
                echo "🔧 Correction: Ajout des domaines de production à DJANGO_ALLOWED_HOSTS"
                NEW_VALUE="$VALUE,ftp.navixtechnology.com,www.ftp.navixtechnology.com"
                echo "DJANGO_ALLOWED_HOSTS=$NEW_VALUE" >> "$TEMP_FILE"
                continue
            fi
        fi
        
        # Corriger CSRF_TRUSTED_ORIGINS
        if [[ "$KEY" == "CSRF_TRUSTED_ORIGINS" ]]; then
            if [[ ! "$VALUE" =~ ftp\.navixtechnology\.com ]]; then
                echo "🔧 Correction: Ajout des domaines de production à CSRF_TRUSTED_ORIGINS"
                NEW_VALUE="$VALUE,https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com"
                echo "CSRF_TRUSTED_ORIGINS=$NEW_VALUE" >> "$TEMP_FILE"
                continue
            fi
        fi
        
        # Corriger CORS_ALLOW_ALL_ORIGINS (supprimer les doublons, garder False)
        if [[ "$KEY" == "CORS_ALLOW_ALL_ORIGINS" ]]; then
            if [[ "$VALUE" == "True" ]] || [[ "$VALUE" == "true" ]] || [[ "$VALUE" == "1" ]]; then
                echo "🔧 Correction: CORS_ALLOW_ALL_ORIGINS=True → False"
                echo "CORS_ALLOW_ALL_ORIGINS=False" >> "$TEMP_FILE"
                continue
            fi
            # Si déjà False, on garde la première occurrence
            if [[ "$VALUE" == "False" ]] || [[ "$VALUE" == "false" ]] || [[ "$VALUE" == "0" ]]; then
                # Vérifier si on a déjà écrit cette ligne
                if ! grep -q "^CORS_ALLOW_ALL_ORIGINS=False" "$TEMP_FILE"; then
                    echo "CORS_ALLOW_ALL_ORIGINS=False" >> "$TEMP_FILE"
                fi
                continue
            fi
        fi
        
        # Corriger CORS_ALLOWED_ORIGINS
        if [[ "$KEY" == "CORS_ALLOWED_ORIGINS" ]]; then
            if [[ ! "$VALUE" =~ ftp\.navixtechnology\.com ]]; then
                echo "🔧 Correction: Ajout des domaines de production à CORS_ALLOWED_ORIGINS"
                NEW_VALUE="$VALUE,https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com"
                echo "CORS_ALLOWED_ORIGINS=$NEW_VALUE" >> "$TEMP_FILE"
                continue
            fi
        fi
        
        # Corriger BACKEND_URL et FRONTEND_URL (optionnel)
        if [[ "$KEY" == "BACKEND_URL" ]] && [[ "$VALUE" =~ ^http://127\.0\.0\.1:8001$ ]]; then
            echo "🔧 Correction: BACKEND_URL → https://ftp.navixtechnology.com"
            echo "BACKEND_URL=https://ftp.navixtechnology.com" >> "$TEMP_FILE"
            continue
        fi
        
        if [[ "$KEY" == "FRONTEND_URL" ]] && [[ "$VALUE" =~ ^http://127\.0\.0\.1:3000$ ]]; then
            echo "🔧 Correction: FRONTEND_URL → https://comparateurdeprix.com"
            echo "FRONTEND_URL=https://comparateurdeprix.com" >> "$TEMP_FILE"
            continue
        fi
    fi
    
    # Garder la ligne telle quelle si aucune correction n'est nécessaire
    echo "$line" >> "$TEMP_FILE"
    
done < .env

# Remplacer le fichier .env par la version corrigée
mv "$TEMP_FILE" .env
chmod 600 .env

echo ""
echo "✅ Fichier .env corrigé avec succès !"
echo ""
echo "📋 Résumé des corrections appliquées :"
echo "   - DJANGO_DEBUG → False"
echo "   - POSTGRES_SSL_REQUIRE → False"
echo "   - Ajout des domaines de production dans DJANGO_ALLOWED_HOSTS"
echo "   - Ajout des domaines de production dans CSRF_TRUSTED_ORIGINS"
echo "   - Ajout des domaines de production dans CORS_ALLOWED_ORIGINS"
echo "   - CORS_ALLOW_ALL_ORIGINS → False"
echo ""
echo "🔍 Vérifiez les modifications :"
echo "   diff $BACKUP_FILE .env"
echo ""
echo "🚀 Prochaines étapes :"
echo "   1. Vérifiez le fichier : cat .env | grep -E 'DJANGO_DEBUG|POSTGRES_SSL_REQUIRE|DJANGO_ALLOWED_HOSTS'"
echo "   2. Testez la connexion : python manage.py dbshell"
echo "   3. Appliquez les migrations : python manage.py migrate"
echo "   4. Vérifiez la config : python manage.py check --deploy"
echo ""

