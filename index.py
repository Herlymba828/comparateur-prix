#!/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/python
"""
Point d'entrée alternatif pour les serveurs web qui ne supportent pas Passenger
"""
import sys
import os

# Ajouter le répertoire du projet au path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    env_path = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Importer et créer l'application WSGI
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

