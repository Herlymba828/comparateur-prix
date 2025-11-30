import logging
import sys
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

logger = logging.getLogger(__name__)


class JWTAuthenticationLoggingMiddleware:
    """Middleware pour logger les tentatives d'authentification JWT avec détails"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        # Logger les tentatives d'authentification pour les endpoints protégés
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        
        # Vérifier si c'est un endpoint protégé (nécessite authentification)
        protected_paths = [
            '/api/utilisateurs/twofa',
            '/api/utilisateurs/me',
            '/api/auth/sessions',
            '/api/produits/alertes-prix',
            '/api/produits/produits/',
            '/api/recommandations/pour_moi',
        ]
        is_protected = any(request.path.startswith(path) for path in protected_paths)
        
        if auth_header and request.path.startswith('/api/'):
            try:
                # Essayer d'authentifier pour voir si le token est valide
                user, token = self.jwt_auth.authenticate(request)
                if user:
                    logger.debug(
                        f"[JWT] ✅ Authentification réussie - User ID: {user.id}, "
                        f"Username: {user.username}, Path: {request.path}, IP: {ip_address}"
                    )
                else:
                    if is_protected:
                        logger.warning(
                            f"[JWT] ⚠️ Authentification échouée (user=None) - Path: {request.path}, "
                            f"Method: {request.method}, IP: {ip_address}, "
                            f"Token présent: Oui, Token preview: {auth_header[:50]}..."
                        )
                        print(
                            f"[WARNING] JWT auth failed (user=None) - {request.method} {request.path}, "
                            f"IP: {ip_address}",
                            file=sys.stderr,
                            flush=True
                        )
            except (InvalidToken, TokenError) as e:
                if is_protected:
                    error_details = (
                        f"[JWT] ❌ Token invalide - Path: {request.path}, "
                        f"Method: {request.method}, IP: {ip_address}, "
                        f"Erreur: {str(e)}, Type: {type(e).__name__}, "
                        f"Token preview: {auth_header[:50]}..."
                    )
                    logger.warning(error_details)
                    print(
                        f"[WARNING] JWT token invalid - {request.method} {request.path}, "
                        f"Error: {type(e).__name__} - {str(e)}, IP: {ip_address}",
                        file=sys.stderr,
                        flush=True
                    )
            except Exception as e:
                if is_protected:
                    error_details = (
                        f"[JWT] ❌ Erreur authentification - Path: {request.path}, "
                        f"Method: {request.method}, IP: {ip_address}, "
                        f"Erreur: {str(e)}, Type: {type(e).__name__}"
                    )
                    logger.error(error_details, exc_info=True)
                    print(
                        f"[ERROR] JWT auth error - {request.method} {request.path}, "
                        f"Error: {type(e).__name__} - {str(e)}, IP: {ip_address}",
                        file=sys.stderr,
                        flush=True
                    )
        elif is_protected and not auth_header:
            # Logger les tentatives sans token sur les endpoints protégés
            warning_msg = (
                f"[JWT] ⚠️ Tentative d'accès sans token - Path: {request.path}, "
                f"Method: {request.method}, IP: {ip_address}, User-Agent: {user_agent[:50]}"
            )
            logger.warning(warning_msg)
            print(
                f"[WARNING] Unauthorized access attempt (no token) - {request.method} {request.path}, "
                f"IP: {ip_address}",
                file=sys.stderr,
                flush=True
            )
        
        response = self.get_response(request)
        
        # Logger les réponses 401 pour les endpoints protégés
        if response.status_code == 401 and is_protected:
            auth_info = "Token présent" if auth_header else "Aucun token"
            logger.warning(
                f"[JWT] 🔒 Réponse 401 Unauthorized - Path: {request.path}, "
                f"Method: {request.method}, IP: {ip_address}, {auth_info}"
            )
        
        return response
