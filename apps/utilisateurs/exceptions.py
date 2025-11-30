"""
Exception handler personnalisé pour améliorer les messages d'erreur d'authentification
"""
from rest_framework.views import exception_handler
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Handler personnalisé pour les exceptions DRF qui améliore les messages d'erreur 401
    """
    # Appeler le handler par défaut pour obtenir la réponse standard
    response = exception_handler(exc, context)
    
    if response is not None:
        # Améliorer les réponses d'erreur d'authentification
        if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
            request = context.get('request')
            auth_header = request.META.get('HTTP_AUTHORIZATION', '') if request else ''
            ip_address = request.META.get('REMOTE_ADDR', 'unknown') if request else 'unknown'
            
            # Préparer une réponse améliorée
            custom_response_data = {
                'detail': 'Authentification requise. Token manquant ou invalide.',
                'code': 'authentication_failed',
                'auth_header_present': bool(auth_header),
            }
            
            # Ajouter des suggestions pour résoudre le problème
            if not auth_header:
                custom_response_data['suggestion'] = (
                    'Aucun token d\'authentification fourni. '
                    'Ajoutez le header: Authorization: Bearer <token>'
                )
                custom_response_data['refresh_endpoint'] = '/api/auth/token/refresh/'
            else:
                custom_response_data['suggestion'] = (
                    'Le token fourni est invalide ou expiré. '
                    'Essayez de rafraîchir votre token avec /api/auth/token/refresh/'
                )
                custom_response_data['refresh_endpoint'] = '/api/auth/token/refresh/'
                custom_response_data['token_preview'] = auth_header[:30] + '...' if len(auth_header) > 30 else auth_header
            
            # Logger l'erreur pour diagnostic
            logger.warning(
                f"[AUTH] Erreur d'authentification - Path: {request.path if request else 'unknown'}, "
                f"Method: {request.method if request else 'unknown'}, IP: {ip_address}, "
                f"Auth header présent: {bool(auth_header)}, "
                f"Exception: {type(exc).__name__}"
            )
            
            response.data = custom_response_data
            response.status_code = status.HTTP_401_UNAUTHORIZED
        
        # Améliorer les autres erreurs d'authentification
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            request = context.get('request')
            auth_header = request.META.get('HTTP_AUTHORIZATION', '') if request else ''
            
            if not hasattr(response, 'data') or not isinstance(response.data, dict):
                response.data = {}
            
            response.data['code'] = 'authentication_required'
            response.data['auth_header_present'] = bool(auth_header)
            response.data['refresh_endpoint'] = '/api/auth/token/refresh/'
            
            if not auth_header:
                response.data['suggestion'] = (
                    'Aucun token d\'authentification fourni. '
                    'Ajoutez le header: Authorization: Bearer <token>'
                )
            else:
                response.data['suggestion'] = (
                    'Le token fourni est invalide ou expiré. '
                    'Essayez de rafraîchir votre token.'
                )
    
    return response

