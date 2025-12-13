"""
Script pour réinitialiser la base de données Railway.
Usage: python scripts/reset_railway_db.py
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.management import call_command
from django.db import connection

def reset_database():
    """Supprime toutes les tables et recrée la structure."""
    print("⚠️  ATTENTION : Cette opération va supprimer TOUTES les données !")
    print(f"Base de données : {connection.settings_dict['NAME']}")
    print(f"Hôte : {connection.settings_dict['HOST']}")
    
    confirmation = input("\nTaper 'OUI' pour confirmer la suppression : ")
    
    if confirmation != 'OUI':
        print("❌ Opération annulée.")
        return
    
    print("\n🗑️  Suppression de toutes les tables...")
    
    # Obtenir toutes les tables
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
        """)
        tables = cursor.fetchall()
        
        if tables:
            print(f"📋 {len(tables)} tables trouvées")
            
            # Désactiver les contraintes de clés étrangères
            cursor.execute("SET session_replication_role = 'replica';")
            
            # Supprimer chaque table
            for table in tables:
                table_name = table[0]
                print(f"  - Suppression de {table_name}...")
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
            
            # Réactiver les contraintes
            cursor.execute("SET session_replication_role = 'origin';")
            
            print("✅ Toutes les tables ont été supprimées")
        else:
            print("ℹ️  Aucune table à supprimer")
    
    print("\n🔨 Recréation de la structure de la base...")
    call_command('migrate', '--run-syncdb')
    print("✅ Structure de la base recréée")
    
    print("\n🎉 Base de données réinitialisée avec succès !")
    print("\n💡 Prochaines étapes :")
    print("   1. Créer un superutilisateur : python manage.py createsuperuser")
    print("   2. Peupler avec des données de test : python manage.py seed_data")
    print("   3. Ou scraper les données DGCCRF : python manage.py scrape_dgccrf")

if __name__ == '__main__':
    reset_database()
