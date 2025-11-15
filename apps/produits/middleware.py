import logging
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


class JWTAuthenticationLoggingMiddleware:
    """Middleware pour logger les tentatives d'authentification JWT"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # Logger les tentatives d'authentification pour les endpoints protégés
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header and request.path.startswith('/api/'):
            try:
                # Essayer d'authentifier pour voir si le token est valide
                user, token = self.jwt_auth.authenticate(request)
                if user:
                    logger.debug(
                        f"[JWT] Authentification réussie - User ID: {user.id}, "
                        f"Username: {user.username}, Path: {request.path}"
                    )
                else:
                    logger.warning(
                        f"[JWT] Authentification échouée - Path: {request.path}, "
                        f"Header présent: Oui, Token: {auth_header[:30]}..."
                    )
            except (InvalidToken, TokenError) as e:
                logger.warning(
                    f"[JWT] Token invalide - Path: {request.path}, "
                    f"Erreur: {str(e)}, Type: {type(e).__name__}, "
                    f"Token: {auth_header[:30]}..."
                )
            except Exception as e:
                logger.error(
                    f"[JWT] Erreur authentification - Path: {request.path}, "
                    f"Erreur: {str(e)}, Type: {type(e).__name__}",
                    exc_info=True
                )
        elif request.path.startswith('/api/produits/produits/') and 'like' in request.path:
            # Logger les tentatives sans token sur les endpoints de likes
            logger.warning(
                f"[JWT] Tentative d'accès sans token - Path: {request.path}, "
                f"Method: {request.method}, IP: {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
        
        response = self.get_response(request)
        return response
