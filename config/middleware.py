"""
Middleware personnalisé pour gérer les erreurs et retourner du JSON pour les API
"""
import json
import logging
import traceback
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

logger = logging.getLogger(__name__)


class JSONExceptionMiddleware(MiddlewareMixin):
    """
    Middleware pour intercepter les exceptions et retourner du JSON
    pour les requêtes API au lieu du HTML par défaut de Django
    """
    
    def process_exception(self, request, exception):
        """
        Intercepte toutes les exceptions et retourne du JSON pour les requêtes API
        """
        # Seulement pour les requêtes API
        if not request.path.startswith('/api/'):
            return None  # Laisser Django gérer normalement
        
        # Logger l'erreur complète
        error_traceback = traceback.format_exc()
        error_message = (
            f"❌ EXCEPTION NON GÉRÉE - {request.method} {request.path}\n"
            f"Type: {type(exception).__name__}\n"
            f"Message: {str(exception)}\n"
            f"Traceback complet:\n{error_traceback}\n"
            f"Données reçues: {getattr(request, 'data', {})}\n"
            f"Body: {getattr(request, 'body', b'').decode('utf-8', errors='ignore')[:500]}"
        )
        
        logger.error(error_message, exc_info=True)
        
        # Forcer l'affichage sur stdout/stderr pour Railway
        import sys
        print(error_message, file=sys.stderr, flush=True)
        print(f"[ERROR] {type(exception).__name__}: {str(exception)}", file=sys.stdout, flush=True)
        
        # Préparer la réponse JSON
        error_response = {
            'detail': 'Une erreur est survenue sur le serveur.',
            'error_type': type(exception).__name__,
        }
        
        # En mode DEBUG, ajouter plus de détails
        if settings.DEBUG:
            error_response.update({
                'error_message': str(exception),
                'traceback': error_traceback.split('\n')[-15:],  # Dernières 15 lignes
            })
        else:
            error_response['debug_info'] = 'Consultez les logs du serveur pour plus de détails.'
        
        # Retourner une réponse JSON au lieu de laisser Django retourner du HTML
        return JsonResponse(error_response, status=500)

