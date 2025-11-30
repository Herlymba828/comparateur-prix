"""
Middleware personnalisé pour gérer les erreurs et retourner du JSON pour les API
"""
import json
import gzip
import logging
import traceback
from django.http import HttpResponse, JsonResponse
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


class CompressionMiddleware(MiddlewareMixin):
    """
    Middleware pour compresser les réponses JSON avec gzip si le client le supporte.
    Réduit significativement la taille des réponses (60-80% de réduction).
    """
    
    def process_response(self, request, response):
        """
        Compresse la réponse si :
        - Le client accepte gzip (via Accept-Encoding)
        - La réponse est JSON ou texte
        - La taille de la réponse est suffisante (> 200 bytes)
        """
        # Vérifier si le client accepte la compression
        accept_encoding = request.META.get('HTTP_ACCEPT_ENCODING', '')
        
        if 'gzip' not in accept_encoding:
            return response
        
        # Vérifier le type de contenu
        content_type = response.get('Content-Type', '')
        if not (content_type.startswith('application/json') or 
                content_type.startswith('text/') or
                content_type.startswith('application/javascript')):
            return response
        
        # Ne pas compresser les réponses trop petites (overhead gzip)
        content_length = len(response.content)
        if content_length < 200:
            return response
        
        # Ne pas compresser si déjà compressé
        if response.get('Content-Encoding'):
            return response
        
        try:
            # Compresser la réponse
            compressed_content = gzip.compress(response.content, compresslevel=6)
            
            # Vérifier que la compression est bénéfique (au moins 20% de réduction)
            if len(compressed_content) >= content_length * 0.8:
                return response
            
            # Créer une nouvelle réponse avec le contenu compressé
            compressed_response = HttpResponse(compressed_content, content_type=content_type)
            compressed_response['Content-Encoding'] = 'gzip'
            compressed_response['Content-Length'] = str(len(compressed_content))
            
            # Copier les autres en-têtes
            for header, value in response.items():
                if header.lower() not in ('content-length', 'content-encoding'):
                    compressed_response[header] = value
            
            logger.debug(
                f"Réponse compressée: {content_length} bytes -> {len(compressed_content)} bytes "
                f"({100 - (len(compressed_content) * 100 / content_length):.1f}% de réduction)"
            )
            
            return compressed_response
            
        except Exception as e:
            logger.warning(f"Erreur lors de la compression de la réponse: {e}")
            # En cas d'erreur, retourner la réponse originale
            return response

