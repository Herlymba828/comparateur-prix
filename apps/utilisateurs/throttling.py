"""
Throttling personnalisé avec gestion gracieuse des erreurs Redis
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle
import logging

logger = logging.getLogger(__name__)


class SafeAnonRateThrottle(AnonRateThrottle):
    """
    AnonRateThrottle qui gère gracieusement les erreurs de connexion Redis
    """
    
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as e:
            # Si Redis n'est pas disponible, logger l'erreur mais autoriser la requête
            logger.warning(f"Erreur Redis dans throttling (autorisation de la requête): {e}")
            # Autoriser la requête si le cache échoue
            return True


class SafeUserRateThrottle(UserRateThrottle):
    """
    UserRateThrottle qui gère gracieusement les erreurs de connexion Redis
    """
    
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as e:
            # Si Redis n'est pas disponible, logger l'erreur mais autoriser la requête
            logger.warning(f"Erreur Redis dans throttling (autorisation de la requête): {e}")
            # Autoriser la requête si le cache échoue
            return True


class SafeScopedRateThrottle(ScopedRateThrottle):
    """
    ScopedRateThrottle qui gère gracieusement les erreurs de connexion Redis
    """
    
    def allow_request(self, request, view):
        try:
            return super().allow_request(request, view)
        except Exception as e:
            # Si Redis n'est pas disponible, logger l'erreur mais autoriser la requête
            logger.warning(f"Erreur Redis dans throttling (autorisation de la requête): {e}")
            # Autoriser la requête si le cache échoue
            return True

