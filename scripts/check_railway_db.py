#!/usr/bin/env python
"""
Script pour vérifier la configuration de la base de données Railway.
Usage: railway run python scripts/check_railway_db.py
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire du projet au path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Charger les variables d'environnement
from dotenv import load_dotenv
load_dotenv(BASE_DIR / '.env')

print("=" * 70)
print("DIAGNOSTIC DE LA CONFIGURATION RAILWAY")
print("=" * 70)
print()

# Vérifier DATABASE_URL
database_url = os.getenv('DATABASE_URL')
if database_url:
    print("✅ DATABASE_URL est défini")
    # Masquer le mot de passe dans l'URL
    if '@' in database_url:
        parts = database_url.split('@')
        if len(parts) == 2:
            user_pass = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
            if ':' in user_pass:
                user, _ = user_pass.split(':', 1)
                safe_url = database_url.split('@')[0].split('://')[0] + '://' + user + ':****@' + '@'.join(parts[1:])
            else:
                safe_url = database_url
        else:
            safe_url = database_url
    else:
        safe_url = database_url
    
    print(f"   URL: {safe_url}")
    
    # Vérifier si c'est Railway
    if 'railway' in database_url.lower():
        print("   ✅ Détecté comme base de données Railway")
    elif 'localhost' in database_url or '127.0.0.1' in database_url:
        print("   ⚠️  ATTENTION: Connexion à localhost détectée")
        print("   Railway devrait utiliser une URL avec 'railway' dans le nom d'hôte")
    else:
        print("   ℹ️  Base de données externe")
else:
    print("❌ DATABASE_URL n'est PAS défini")
    print()
    print("SOLUTIONS:")
    print("1. Vérifiez que le service PostgreSQL est créé sur Railway")
    print("2. Vérifiez que les services sont dans le même projet Railway")
    print("3. Vérifiez les variables d'environnement dans Railway:")
    print("   - Allez dans votre service Django → Variables")
    print("   - Cherchez DATABASE_URL")
    print("   - Si elle n'existe pas, copiez-la depuis le service PostgreSQL")
    print()

# Vérifier les autres variables
print()
print("Autres variables de base de données:")
print(f"  DB_ENGINE: {os.getenv('DB_ENGINE', 'non défini')}")
print(f"  POSTGRES_HOST: {os.getenv('POSTGRES_HOST', 'non défini')}")
print(f"  POSTGRES_DB: {os.getenv('POSTGRES_DB', 'non défini')}")
print()

# Vérifier DEBUG
debug = os.getenv('DJANGO_DEBUG', 'False')
print(f"DJANGO_DEBUG: {debug}")
if debug.lower() in ('true', '1', 'yes', 'y'):
    print("  ⚠️  DEBUG est activé - la base de données utilisera SQLite en local")
else:
    print("  ✅ DEBUG est désactivé - la base de données utilisera PostgreSQL")
print()

# Tester la connexion Django
print("Test de connexion Django...")
try:
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    
    from django.db import connection
    connection.ensure_connection()
    print("✅ Connexion à la base de données réussie!")
    print(f"   Base de données: {connection.settings_dict.get('NAME', 'N/A')}")
    print(f"   Hôte: {connection.settings_dict.get('HOST', 'N/A')}")
    print(f"   Port: {connection.settings_dict.get('PORT', 'N/A')}")
    print(f"   SSL: {connection.settings_dict.get('OPTIONS', {}).get('sslmode', 'N/A')}")
except Exception as e:
    print(f"❌ Erreur de connexion: {str(e)}")
    print()
    print("SOLUTIONS:")
    if 'SSL' in str(e) or 'ssl' in str(e).lower():
        print("1. Le problème est lié à SSL")
        if 'localhost' in str(e) or '127.0.0.1' in str(e):
            print("2. Vous essayez de vous connecter à localhost avec SSL")
            print("3. Assurez-vous que DATABASE_URL pointe vers Railway, pas localhost")
            print("4. Ou définissez POSTGRES_SSL_REQUIRE=False pour localhost")
    elif 'Connection refused' in str(e) or 'connection' in str(e).lower():
        print("1. Impossible de se connecter à la base de données")
        print("2. Vérifiez que le service PostgreSQL est démarré sur Railway")
        print("3. Vérifiez que DATABASE_URL est correct")
    else:
        print(f"1. Erreur: {str(e)}")
        print("2. Vérifiez les logs Railway pour plus de détails")

print()
print("=" * 70)

