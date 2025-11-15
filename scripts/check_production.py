#!/usr/bin/env python
"""
Script pour vérifier la configuration Django en mode production.
Simule les vérifications de sécurité qui seront effectuées en production.
"""
import os
import sys
import django
from pathlib import Path

# Ajouter le répertoire du projet au path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Forcer le mode production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
os.environ['DJANGO_DEBUG'] = 'False'

# Initialiser Django
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

def check_production_settings():
    """Vérifie que tous les paramètres de production sont correctement configurés."""
    print("=" * 70)
    print("VÉRIFICATION DE LA CONFIGURATION PRODUCTION")
    print("=" * 70)
    print()
    
    errors = []
    warnings = []
    
    # Vérifier DEBUG
    if settings.DEBUG:
        errors.append("❌ DEBUG est True - doit être False en production")
    else:
        print("✅ DEBUG est False")
    
    # Vérifier SECRET_KEY
    if not settings.SECRET_KEY:
        errors.append("❌ SECRET_KEY n'est pas défini")
    elif len(settings.SECRET_KEY) < 50:
        warnings.append("⚠️  SECRET_KEY est trop court (< 50 caractères)")
    elif settings.SECRET_KEY.startswith('django-insecure-'):
        warnings.append("⚠️  SECRET_KEY utilise la clé par défaut de Django")
    else:
        print("✅ SECRET_KEY est défini et sécurisé")
    
    # Vérifier les paramètres de sécurité
    security_settings = {
        'SESSION_COOKIE_SECURE': settings.SESSION_COOKIE_SECURE,
        'CSRF_COOKIE_SECURE': settings.CSRF_COOKIE_SECURE,
        'SECURE_SSL_REDIRECT': settings.SECURE_SSL_REDIRECT,
        'SECURE_HSTS_SECONDS': getattr(settings, 'SECURE_HSTS_SECONDS', None),
    }
    
    for setting, value in security_settings.items():
        if value:
            print(f"✅ {setting} est activé")
        else:
            errors.append(f"❌ {setting} n'est pas activé")
    
    # Vérifier ALLOWED_HOSTS
    if 'ftp.navixtechnology.com' not in settings.ALLOWED_HOSTS:
        errors.append("❌ ftp.navixtechnology.com n'est pas dans ALLOWED_HOSTS")
    else:
        print("✅ ftp.navixtechnology.com est dans ALLOWED_HOSTS")
    
    # Vérifier la base de données
    db_config = settings.DATABASES['default']
    if not db_config.get('PASSWORD'):
        warnings.append("⚠️  POSTGRES_PASSWORD n'est pas défini")
    else:
        print("✅ Base de données PostgreSQL configurée")
    
    # Vérifier les variables d'environnement critiques
    critical_env_vars = ['DJANGO_SECRET_KEY', 'POSTGRES_PASSWORD']
    for var in critical_env_vars:
        if not os.getenv(var):
            warnings.append(f"⚠️  Variable d'environnement {var} non définie")
    
    print()
    print("=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    
    if errors:
        print(f"\n❌ ERREURS ({len(errors)}):")
        for error in errors:
            print(f"   {error}")
        print("\n⚠️  Ces erreurs DOIVENT être corrigées avant le déploiement!")
        return False
    
    if warnings:
        print(f"\n⚠️  AVERTISSEMENTS ({len(warnings)}):")
        for warning in warnings:
            print(f"   {warning}")
        print("\n💡 Ces avertissements sont recommandés mais non bloquants.")
    
    if not errors and not warnings:
        print("\n✅ Tous les paramètres de production sont correctement configurés!")
    
    print()
    print("=" * 70)
    print("NOTE: Les avertissements drf_spectacular sont non critiques")
    print("      et concernent uniquement la documentation OpenAPI.")
    print("=" * 70)
    
    return len(errors) == 0

if __name__ == '__main__':
    try:
        success = check_production_settings()
        print()
        
        # Exécuter aussi check --deploy
        print("Exécution de 'python manage.py check --deploy'...")
        print("-" * 70)
        call_command('check', '--deploy')
        
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

