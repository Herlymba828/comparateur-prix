#!/usr/bin/env python
"""
Script de diagnostic pour vérifier le chargement des variables d'environnement
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ajouter le répertoire du projet au path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

print("=" * 70)
print("DIAGNOSTIC DES VARIABLES D'ENVIRONNEMENT")
print("=" * 70)
print()

# 1. Vérifier les emplacements possibles du fichier .env
print("1. Recherche du fichier .env:")
print("-" * 70)
env_paths = [
    BASE_DIR / '.env',
    BASE_DIR.parent / '.env',
    Path('/home/rs2694021ez6eg8n/comparer1/comparateur-prix/.env'),
    Path('/home/rs2694021ez6eg8n/public_html/comparer/.env'),
]

env_found = False
for env_path in env_paths:
    exists = env_path.exists()
    status = "✓ TROUVÉ" if exists else "✗ Non trouvé"
    print(f"  {status}: {env_path}")
    if exists:
        env_found = True
        # Charger le fichier trouvé
        load_dotenv(env_path, override=True)
        print(f"    Taille: {env_path.stat().st_size} octets")
        print(f"    Permissions: {oct(env_path.stat().st_mode)[-3:]}")
        break

if not env_found:
    print("\n⚠️  Aucun fichier .env trouvé dans les emplacements testés!")
    print("   Tentative de chargement par défaut...")
    load_dotenv(BASE_DIR / '.env')

print()
print("2. Variables d'environnement de la base de données:")
print("-" * 70)

# Variables à vérifier
db_vars = {
    'DB_ENGINE': os.getenv('DB_ENGINE'),
    'DB_NAME': os.getenv('DB_NAME'),
    'DB_USER': os.getenv('DB_USER'),
    'DB_PASSWORD': os.getenv('DB_PASSWORD'),
    'DB_HOST': os.getenv('DB_HOST'),
    'DB_PORT': os.getenv('DB_PORT'),
    'POSTGRES_DB': os.getenv('POSTGRES_DB'),
    'POSTGRES_USER': os.getenv('POSTGRES_USER'),
    'POSTGRES_PASSWORD': os.getenv('POSTGRES_PASSWORD'),
    'MYSQL_DB': os.getenv('MYSQL_DB'),
    'MYSQL_USER': os.getenv('MYSQL_USER'),
    'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD'),
}

for var_name, var_value in db_vars.items():
    if var_value:
        # Masquer les mots de passe
        if 'PASSWORD' in var_name:
            display_value = '*' * min(len(var_value), 20) + ('...' if len(var_value) > 20 else '')
        else:
            display_value = var_value
        print(f"  ✓ {var_name:20s} = {display_value}")
    else:
        print(f"  ✗ {var_name:20s} = (non défini)")

print()
print("3. Détection du type de base de données:")
print("-" * 70)
DB_ENGINE = os.getenv('DB_ENGINE', 'postgresql').lower()
print(f"  DB_ENGINE détecté: {DB_ENGINE}")

# Calculer les valeurs finales comme dans settings.py
DB_NAME = os.getenv('DB_NAME') or os.getenv('POSTGRES_DB') or os.getenv('MYSQL_DB', 'soutenance2')
DB_USER = os.getenv('DB_USER') or os.getenv('POSTGRES_USER') or os.getenv('MYSQL_USER', 'postgres')
DB_PASSWORD = (
    os.getenv('DB_PASSWORD') or 
    os.getenv('POSTGRES_PASSWORD') or 
    os.getenv('MYSQL_PASSWORD') or 
    ''
)
DB_HOST = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST') or os.getenv('MYSQL_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT') or os.getenv('MYSQL_PORT', '3306' if DB_ENGINE == 'mysql' else '5432')

print(f"  DB_NAME final:   {DB_NAME}")
print(f"  DB_USER final:   {DB_USER}")
print(f"  DB_PASSWORD:     {'✓ Défini (' + str(len(DB_PASSWORD)) + ' caractères)' if DB_PASSWORD else '✗ NON DÉFINI'}")
print(f"  DB_HOST final:   {DB_HOST}")
print(f"  DB_PORT final:   {DB_PORT}")

print()
print("4. Vérification de la configuration Django:")
print("-" * 70)
DEBUG = os.getenv('DJANGO_DEBUG', 'False').lower() in ('1', 'true', 'yes', 'y')
print(f"  DEBUG:            {DEBUG}")
print(f"  Mode production:  {not DEBUG}")

if not DEBUG and not DB_PASSWORD:
    print()
    print("⚠️  ERREUR: Le mot de passe de la base de données n'est pas défini en production!")
    print("   Veuillez définir DB_PASSWORD dans votre fichier .env")
else:
    print("  ✓ Configuration valide")

print()
print("5. Autres variables importantes:")
print("-" * 70)
other_vars = [
    'DJANGO_SECRET_KEY',
    'DJANGO_ALLOWED_HOSTS',
    'CORS_ALLOWED_ORIGINS',
    'CSRF_TRUSTED_ORIGINS',
    'SITE_URL',
    'REDIS_URL',
]
for var_name in other_vars:
    var_value = os.getenv(var_name)
    if var_value:
        # Tronquer les valeurs longues
        display_value = var_value[:50] + '...' if len(var_value) > 50 else var_value
        print(f"  ✓ {var_name:20s} = {display_value}")
    else:
        print(f"  ✗ {var_name:20s} = (non défini)")

print()
print("=" * 70)
print("FIN DU DIAGNOSTIC")
print("=" * 70)

