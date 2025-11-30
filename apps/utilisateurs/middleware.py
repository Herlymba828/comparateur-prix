"""
Middleware pour améliorer la gestion des erreurs 401 et suggérer le refresh du token
"""
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class AuthErrorEnhancementMiddleware(MiddlewareMixin):
    """
    Middleware qui améliore les réponses 401 en ajoutant des suggestions utiles
    """
    
    def process_response(self, request, response):
        # Seulement pour les requêtes API
        if not request.path.startswith('/api/'):
            return response
        
        # Si c'est une erreur 401, améliorer la réponse
        if response.status_code == 401:
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            ip_address = request.META.get('REMOTE_ADDR', 'unknown')
            
            # Logger l'erreur pour diagnostic
            logger.warning(
                f"[AUTH] Réponse 401 - Path: {request.path}, Method: {request.method}, "
                f"IP: {ip_address}, Auth header présent: {bool(auth_header)}"
            )
            
            # Si la réponse est JSON, améliorer le contenu
            if hasattr(response, 'content') and response.get('Content-Type', '').startswith('application/json'):
                try:
                    # Essayer de parser le contenu JSON existant
                    if hasattr(response, 'data'):
                        response_data = response.data
                    else:
                        response_data = json.loads(response.content.decode('utf-8')) if response.content else {}
                    
                    # Ajouter des informations utiles si elles n'existent pas déjà
                    if 'code' not in response_data:
                        response_data['code'] = 'authentication_required'
                    
                    if 'auth_header_present' not in response_data:
                        response_data['auth_header_present'] = bool(auth_header)
                    
                    if 'refresh_endpoint' not in response_data:
                        response_data['refresh_endpoint'] = '/api/auth/token/refresh/'
                    
                    if 'suggestion' not in response_data:
                        if not auth_header:
                            response_data['suggestion'] = (
                                'Aucun token d\'authentification fourni. '
                                'Ajoutez le header: Authorization: Bearer <token>'
                            )
                        else:
                            response_data['suggestion'] = (
                                'Le token fourni est invalide ou expiré. '
                                'Essayez de rafraîchir votre token avec /api/auth/token/refresh/'
                            )
                    
                    # Mettre à jour la réponse
                    if hasattr(response, 'data'):
                        response.data = response_data
                    else:
                        response.content = json.dumps(response_data).encode('utf-8')
                except (json.JSONDecodeError, AttributeError):
                    # Si on ne peut pas parser, créer une nouvelle réponse
                    pass
        
        return response

