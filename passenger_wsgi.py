"""
Fichier WSGI pour Passenger (cPanel)
Ce fichier est utilisé par Passenger pour démarrer l'application Django
"""
import sys
import os

# Ajouter le répertoire du projet au path Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Activer l'environnement virtuel
activate_this = '/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate_this.py'
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Charger les variables d'environnement depuis .env si python-dotenv est installé
try:
    from dotenv import load_dotenv
    env_path = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv n'est pas installé, continuer sans

# Importer l'application WSGI Django
from django.core.wsgi import get_wsgi_application

# Créer l'application WSGI
application = get_wsgi_application()

