"""
Script pour créer les indexes optimisés.
Usage: python scripts/create_indexes.py
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

from apps.api.database_optimizations import DatabaseOptimizer

def main():
    """Créer les indexes."""
    print("🔨 Création des indexes optimisés...")
    
    created, errors = DatabaseOptimizer.create_missing_indexes()
    
    print(f"\n✅ {len(created)} index(es) créé(s):")
    for index in created:
        print(f"   - {index}")
    
    if errors:
        print(f"\n⚠️  {len(errors)} erreur(s):")
        for error in errors:
            print(f"   - {error}")
    
    print("\n✅ Terminé !")

if __name__ == '__main__':
    main()
