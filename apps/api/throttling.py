"""
Rate limiting personnalisé pour l'API.
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.core.cache import cache
from django.conf import settings
import time


class SmartAnonRateThrottle(AnonRateThrottle):
    """
    Rate limiting intelligent pour les utilisateurs anonymes.
    Adapte les limites selon le type d'endpoint.
    """
    scope = 'anon'
    
    # Limites par type d'endpoint (requêtes/minute)
    RATE_LIMITS = {
        'read': '100/min',      # Endpoints de lecture (GET)
        'write': '20/min',      # Endpoints d'écriture (POST, PUT, DELETE)
        'auth': '10/min',       # Endpoints d'authentification
        'search': '50/min',     # Endpoints de recherche
    }
    
    def get_rate(self):
        """Déterminer la limite selon le type d'endpoint."""
        request = self.get_request()
        
        # Si pas de requête, retourner la limite par défaut
        if not request:
            return self.RATE_LIMITS['read']
        
        # Authentification
        if 'auth' in request.path or 'login' in request.path or 'register' in request.path:
            return self.RATE_LIMITS['auth']
        
        # Recherche
        if 'search' in request.path or 'autocomplete' in request.path:
            return self.RATE_LIMITS['search']
        
        # Écriture
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return self.RATE_LIMITS['write']
        
        # Lecture par défaut
        return self.RATE_LIMITS['read']
    
    def get_request(self):
        """Récupérer la requête depuis le contexte."""
        return getattr(self, 'request', None)


class SmartUserRateThrottle(UserRateThrottle):
    """
    Rate limiting intelligent pour les utilisateurs authentifiés.
    Adapte les limites selon le niveau d'abonnement.
    """
    scope = 'user'
    
    # Limites par type d'utilisateur (requêtes/minute)
    RATE_LIMITS = {
        'free': '200/min',
        'premium': '1000/min',
        'admin': '10000/min',
    }
    
    def get_rate(self):
        """Déterminer la limite selon le type d'utilisateur."""
        request = self.get_request()
        
        # Si pas de requête, retourner la limite par défaut
        if not request:
            return self.RATE_LIMITS['free']
        
        if not request.user or not request.user.is_authenticated:
            return self.RATE_LIMITS['free']
        
        user = request.user
        
        # Admin/Staff
        if user.is_staff or user.is_superuser:
            return self.RATE_LIMITS['admin']
        
        # Premium (avec abonnement actif)
        if hasattr(user, 'abonnement') and user.abonnement and user.abonnement.est_valide:
            return self.RATE_LIMITS['premium']
        
        # Utilisateur gratuit
        return self.RATE_LIMITS['free']
    
    def get_request(self):
        """Récupérer la requête depuis le contexte."""
        return getattr(self, 'request', None)


class BurstRateThrottle(AnonRateThrottle):
    """
    Rate limiting pour les pics de trafic.
    Permet des rafales courtes mais limite sur une période plus longue.
    """
    scope = 'burst'
    rate = '10/sec'  # 10 requêtes par seconde max


class SustainedRateThrottle(AnonRateThrottle):
    """
    Rate limiting pour le trafic soutenu.
    Limite sur une période plus longue.
    """
    scope = 'sustained'
    rate = '1000/hour'  # 1000 requêtes par heure max


class IPBasedRateThrottle(AnonRateThrottle):
    """
    Rate limiting basé sur l'IP avec détection d'abus.
    """
    scope = 'ip'
    
    def get_cache_key(self, request, view):
        """Générer une clé de cache basée sur l'IP."""
        if request.user.is_authenticated:
            return None  # Ne pas limiter les utilisateurs authentifiés
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': self.get_ident(request)
        }
    
    def allow_request(self, request, view):
        """Vérifier si la requête est autorisée."""
        # Vérifier d'abord si l'IP est bloquée
        ip = self.get_ident(request)
        if self.is_ip_blocked(ip):
            return False
        
        # Appliquer le rate limiting normal
        allowed = super().allow_request(request, view)
        
        # Si refusé, incrémenter le compteur d'abus
        if not allowed:
            self.increment_abuse_counter(ip)
        
        return allowed
    
    def is_ip_blocked(self, ip):
        """Vérifier si une IP est bloquée."""
        block_key = f'blocked_ip:{ip}'
        return cache.get(block_key, False)
    
    def increment_abuse_counter(self, ip):
        """Incrémenter le compteur d'abus pour une IP."""
        abuse_key = f'abuse_counter:{ip}'
        counter = cache.get(abuse_key, 0)
        counter += 1
        
        # Bloquer l'IP si trop d'abus (10 refus en 1 heure)
        if counter >= 10:
            block_key = f'blocked_ip:{ip}'
            cache.set(block_key, True, 3600)  # Bloquer pour 1 heure
            cache.delete(abuse_key)
        else:
            cache.set(abuse_key, counter, 3600)


class EndpointSpecificThrottle(AnonRateThrottle):
    """
    Rate limiting spécifique par endpoint.
    """
    
    # Configuration des limites par endpoint
    ENDPOINT_RATES = {
        '/api/auth/login/': '5/min',
        '/api/auth/register/': '3/min',
        '/api/produits/produits/': '100/min',
        '/api/search/': '50/min',
    }
    
    def get_rate(self):
        """Déterminer la limite selon l'endpoint."""
        request = self.get_request()
        if not request or not hasattr(request, 'path'):
            return '100/min'
        
        # Chercher une correspondance exacte
        path = request.path
        if path in self.ENDPOINT_RATES:
            return self.ENDPOINT_RATES[path]
        
        # Chercher une correspondance partielle
        for endpoint, rate in self.ENDPOINT_RATES.items():
            if endpoint in path:
                return rate
        
        # Limite par défaut
        return '100/min'
    
    def get_request(self):
        """Récupérer la requête depuis le contexte."""
        return getattr(self, 'request', None)


# Fonction utilitaire pour combiner plusieurs throttles

def get_throttle_classes_for_view(view_name):
    """
    Retourne les classes de throttle appropriées pour une vue.
    
    Args:
        view_name: Nom de la vue
    
    Returns:
        Liste de classes de throttle
    """
    # Configuration par défaut
    default_throttles = [SmartAnonRateThrottle, SmartUserRateThrottle]
    
    # Configuration spécifique par vue
    view_throttles = {
        'auth': [IPBasedRateThrottle, EndpointSpecificThrottle],
        'search': [BurstRateThrottle, SustainedRateThrottle],
        'produits': [SmartAnonRateThrottle, SmartUserRateThrottle],
    }
    
    # Retourner les throttles spécifiques ou par défaut
    for key, throttles in view_throttles.items():
        if key in view_name.lower():
            return throttles
    
    return default_throttles
