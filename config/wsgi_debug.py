"""
WSGI debug config - Version ultra-minimale pour diagnostic.
"""
import os
import sys
from pathlib import Path

print("=" * 80)
print("WSGI DEBUG - Démarrage")
print("=" * 80)

# Ajouter le répertoire racine du projet au PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
print(f"✅ PYTHONPATH configuré: {BASE_DIR}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
print(f"✅ DJANGO_SETTINGS_MODULE: {os.getenv('DJANGO_SETTINGS_MODULE')}")

try:
    print("🔍 Import de Django...")
    from django.core.wsgi import get_wsgi_application
    print("✅ Django importé avec succès")
    
    print("🔍 Chargement de l'application WSGI...")
    application = get_wsgi_application()
    print("✅ Application WSGI chargée avec succès!")
    print("=" * 80)
    
except Exception as e:
    print("=" * 80)
    print(f"❌ ERREUR lors du chargement de l'application WSGI:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    print("=" * 80)
    print("Traceback complet:")
    import traceback
    traceback.print_exc()
    print("=" * 80)
    raise
