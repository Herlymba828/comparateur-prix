import os
import sys

# Désactiver le mode debug en production
os.environ['DJANGO_DEBUG'] = 'False'
os.environ['PYTHONUNBUFFERED'] = '1'

# Chemin du projet
INTERP = os.path.expanduser('~/venv/bin/python')
if os.path.isfile(INTERP) and os.environ.get('_') != INTERP:
    try:
        os.execl(INTERP, INTERP, *sys.argv)
    except OSError:
        pass

# Configuration du chemin
INTERP = os.path.join(os.getcwd(), "venv", "bin", "python")
if os.path.isfile(INTERP) and not os.environ.get('_') == INTERP:
    try:
        os.environ['_'] = INTERP
        os.execl(INTERP, INTERP, *sys.argv)
    except OSError:
        pass

# Ajout du répertoire du projet au chemin Python
sys.path.append(os.getcwd())

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Configuration du logger
import logging
logging.basicConfig(stream=sys.stderr)

# Démarrer l'application Django
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Si vous utilisez WhiteNoise pour les fichiers statiques
# (décommentez ces lignes si vous utilisez WhiteNoise)
# from whitenoise import WhiteNoise
# application = WhiteNoise(application, root='staticfiles')
# application.add_files('static', prefix='static/')

# Gestion des erreurs
def error_handler(environ, start_response):
    try:
        return application(environ, start_response)
    except Exception as e:
        import traceback
        error_msg = f"Error: {str(e)}\n\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')])
        return [b'An error occurred. Please try again later.']

# Utiliser le gestionnaire d'erreurs en production
application = error_handler