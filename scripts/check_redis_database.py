#!/usr/bin/env python
"""
Script pour vérifier la configuration de Redis et de la base de données.
Usage: python scripts/check_redis_database.py
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

def check_database():
    """Vérifie la configuration de la base de données."""
    print("=" * 70)
    print("VÉRIFICATION DE LA BASE DE DONNÉES")
    print("=" * 70)
    print()
    
    errors = []
    warnings = []
    info = []
    
    # Vérifier DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        info.append("✅ DATABASE_URL est défini (configuration automatique)")
        print("✅ DATABASE_URL est défini")
        print(f"   URL: {database_url[:50]}..." if len(database_url) > 50 else f"   URL: {database_url}")
    else:
        # Vérifier les variables individuelles
        db_engine = os.getenv('DB_ENGINE', 'postgresql')
        db_name = os.getenv('DB_NAME') or os.getenv('POSTGRES_DB') or os.getenv('MYSQL_DB')
        db_user = os.getenv('DB_USER') or os.getenv('POSTGRES_USER') or os.getenv('MYSQL_USER')
        db_password = os.getenv('DB_PASSWORD') or os.getenv('POSTGRES_PASSWORD') or os.getenv('MYSQL_PASSWORD')
        db_host = os.getenv('DB_HOST') or os.getenv('POSTGRES_HOST') or os.getenv('MYSQL_HOST', 'localhost')
        db_port = os.getenv('DB_PORT') or os.getenv('POSTGRES_PORT') or os.getenv('MYSQL_PORT', '5432' if db_engine == 'postgresql' else '3306')
        
        print(f"Type de base de données: {db_engine.upper()}")
        print()
        
        if not db_name:
            errors.append("❌ DB_NAME n'est pas défini")
            print("❌ DB_NAME n'est pas défini")
        else:
            info.append(f"✅ DB_NAME: {db_name}")
            print(f"✅ DB_NAME: {db_name}")
        
        if not db_user:
            errors.append("❌ DB_USER n'est pas défini")
            print("❌ DB_USER n'est pas défini")
        else:
            info.append(f"✅ DB_USER: {db_user}")
            print(f"✅ DB_USER: {db_user}")
        
        if not db_password:
            warnings.append("⚠️  DB_PASSWORD n'est pas défini (peut causer des erreurs en production)")
            print("⚠️  DB_PASSWORD n'est pas défini")
        else:
            info.append("✅ DB_PASSWORD est défini")
            print("✅ DB_PASSWORD est défini")
        
        info.append(f"✅ DB_HOST: {db_host}")
        info.append(f"✅ DB_PORT: {db_port}")
        print(f"✅ DB_HOST: {db_host}")
        print(f"✅ DB_PORT: {db_port}")
    
    # Tester la connexion Django
    print()
    print("Test de connexion Django...")
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        django.setup()
        
        from django.db import connection
        connection.ensure_connection()
        print("✅ Connexion à la base de données réussie!")
        info.append("✅ Connexion Django réussie")
    except Exception as e:
        errors.append(f"❌ Erreur de connexion Django: {str(e)}")
        print(f"❌ Erreur de connexion Django: {str(e)}")
    
    print()
    return errors, warnings, info


def check_redis():
    """Vérifie la configuration de Redis."""
    print("=" * 70)
    print("VÉRIFICATION DE REDIS")
    print("=" * 70)
    print()
    
    errors = []
    warnings = []
    info = []
    
    # Vérifier REDIS_URL
    redis_url = os.getenv('REDIS_URL') or os.getenv('REDISCLOUD_URL')
    if redis_url:
        info.append(f"✅ REDIS_URL est défini")
        print(f"✅ REDIS_URL est défini")
        print(f"   URL: {redis_url}")
    else:
        warnings.append("⚠️  REDIS_URL n'est pas défini (utilisera redis://localhost:6379 par défaut)")
        print("⚠️  REDIS_URL n'est pas défini")
        print("   Utilisera redis://localhost:6379 par défaut")
    
    # Vérifier REDIS_CACHE_URL
    redis_cache_url = os.getenv('REDIS_CACHE_URL')
    if redis_cache_url:
        info.append(f"✅ REDIS_CACHE_URL est défini")
        print(f"✅ REDIS_CACHE_URL est défini")
        print(f"   URL: {redis_cache_url}")
    else:
        print("ℹ️  REDIS_CACHE_URL n'est pas défini (utilisera REDIS_URL)")
    
    # Tester la connexion Redis
    print()
    print("Test de connexion Redis...")
    try:
        import redis
        redis_url_to_test = redis_url or 'redis://localhost:6379/0'
        r = redis.from_url(redis_url_to_test)
        r.ping()
        print("✅ Connexion à Redis réussie!")
        info.append("✅ Connexion Redis réussie")
    except ImportError:
        errors.append("❌ Le package 'redis' n'est pas installé. Installez-le avec: pip install redis")
        print("❌ Le package 'redis' n'est pas installé")
        print("   Installez-le avec: pip install redis")
    except redis.ConnectionError as e:
        errors.append(f"❌ Impossible de se connecter à Redis: {str(e)}")
        print(f"❌ Impossible de se connecter à Redis: {str(e)}")
        print("   Vérifiez que Redis est démarré et que l'URL est correcte")
    except Exception as e:
        errors.append(f"❌ Erreur Redis: {str(e)}")
        print(f"❌ Erreur Redis: {str(e)}")
    
    # Vérifier Celery
    print()
    print("Vérification Celery...")
    celery_broker = os.getenv('CELERY_BROKER_URL')
    celery_backend = os.getenv('CELERY_RESULT_BACKEND')
    
    if celery_broker:
        info.append(f"✅ CELERY_BROKER_URL est défini")
        print(f"✅ CELERY_BROKER_URL: {celery_broker}")
    else:
        print("ℹ️  CELERY_BROKER_URL n'est pas défini (utilisera REDIS_URL)")
    
    if celery_backend:
        info.append(f"✅ CELERY_RESULT_BACKEND est défini")
        print(f"✅ CELERY_RESULT_BACKEND: {celery_backend}")
    else:
        print("ℹ️  CELERY_RESULT_BACKEND n'est pas défini (utilisera REDIS_URL)")
    
    print()
    return errors, warnings, info


def main():
    """Fonction principale."""
    print("\n" + "=" * 70)
    print("VÉRIFICATION DE LA CONFIGURATION REDIS ET BASE DE DONNÉES")
    print("=" * 70)
    print()
    
    all_errors = []
    all_warnings = []
    all_info = []
    
    # Vérifier la base de données
    db_errors, db_warnings, db_info = check_database()
    all_errors.extend(db_errors)
    all_warnings.extend(db_warnings)
    all_info.extend(db_info)
    
    print("\n")
    
    # Vérifier Redis
    redis_errors, redis_warnings, redis_info = check_redis()
    all_errors.extend(redis_errors)
    all_warnings.extend(redis_warnings)
    all_info.extend(redis_info)
    
    # Résumé
    print("\n" + "=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print()
    
    if all_errors:
        print(f"❌ {len(all_errors)} erreur(s) trouvée(s):")
        for error in all_errors:
            print(f"   {error}")
        print()
    
    if all_warnings:
        print(f"⚠️  {len(all_warnings)} avertissement(s):")
        for warning in all_warnings:
            print(f"   {warning}")
        print()
    
    if all_info:
        print(f"✅ {len(all_info)} élément(s) configuré(s) correctement")
        print()
    
    if not all_errors and not all_warnings:
        print("🎉 Toutes les configurations sont correctes!")
        return 0
    elif not all_errors:
        print("⚠️  Configuration fonctionnelle mais avec des avertissements")
        return 0
    else:
        print("❌ Des erreurs doivent être corrigées avant de continuer")
        return 1


if __name__ == '__main__':
    sys.exit(main())

