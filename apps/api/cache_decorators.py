"""
Décorateurs de cache personnalisés pour optimiser les performances.
"""
from functools import wraps
from django.core.cache import cache
from django.conf import settings
from rest_framework.response import Response
import hashlib
import json

def cache_response(timeout=300, key_prefix='api', vary_on_user=False, vary_on_params=None):
    """
    Décorateur pour mettre en cache les réponses API.
    
    Args:
        timeout: Durée du cache en secondes (défaut: 5 minutes)
        key_prefix: Préfixe pour la clé de cache
        vary_on_user: Si True, cache différent par utilisateur
        vary_on_params: Liste des paramètres de requête à inclure dans la clé
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Ne pas cacher en mode DEBUG
            if settings.DEBUG:
                return view_func(request, *args, **kwargs)
            
            # Construire la clé de cache
            cache_key_parts = [key_prefix, request.path]
            
            # Ajouter l'utilisateur si nécessaire
            if vary_on_user and request.user.is_authenticated:
                cache_key_parts.append(f"user_{request.user.id}")
            
            # Ajouter les paramètres de requête
            if vary_on_params:
                for param in vary_on_params:
                    value = request.GET.get(param)
                    if value:
                        cache_key_parts.append(f"{param}_{value}")
            
            # Créer un hash de la clé pour éviter les clés trop longues
            cache_key_str = ":".join(cache_key_parts)
            cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()
            
            # Essayer de récupérer depuis le cache
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                return Response(cached_response)
            
            # Exécuter la vue
            response = view_func(request, *args, **kwargs)
            
            # Mettre en cache si la réponse est OK
            if isinstance(response, Response) and response.status_code == 200:
                cache.set(cache_key, response.data, timeout)
            
            return response
        
        return wrapper
    return decorator


def invalidate_cache(key_patterns):
    """
    Décorateur pour invalider le cache après une modification.
    
    Args:
        key_patterns: Liste de patterns de clés à invalider
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Exécuter la vue
            response = view_func(request, *args, **kwargs)
            
            # Invalider le cache si la modification a réussi
            if isinstance(response, Response) and 200 <= response.status_code < 300:
                for pattern in key_patterns:
                    cache.delete_pattern(pattern)
            
            return response
        
        return wrapper
    return decorator


class CacheManager:
    """Gestionnaire de cache centralisé."""
    
    # Durées de cache par type de données
    TIMEOUTS = {
        'produits_list': 300,  # 5 minutes
        'produits_detail': 600,  # 10 minutes
        'categories': 3600,  # 1 heure
        'magasins': 1800,  # 30 minutes
        'prix': 180,  # 3 minutes
        'promotions': 300,  # 5 minutes
        'recommandations': 600,  # 10 minutes
        'stats': 1800,  # 30 minutes
    }
    
    @staticmethod
    def get_key(prefix, *args):
        """Générer une clé de cache."""
        parts = [prefix] + [str(arg) for arg in args]
        return ":".join(parts)
    
    @staticmethod
    def get(key, default=None):
        """Récupérer une valeur du cache."""
        return cache.get(key, default)
    
    @staticmethod
    def set(key, value, timeout=None):
        """Définir une valeur dans le cache."""
        cache.set(key, value, timeout)
    
    @staticmethod
    def delete(key):
        """Supprimer une clé du cache."""
        cache.delete(key)
    
    @staticmethod
    def delete_pattern(pattern):
        """Supprimer toutes les clés correspondant à un pattern."""
        try:
            cache.delete_pattern(pattern)
        except AttributeError:
            # Fallback si delete_pattern n'est pas disponible
            pass
    
    @staticmethod
    def clear_all():
        """Vider tout le cache."""
        cache.clear()
    
    @classmethod
    def invalidate_produits(cls):
        """Invalider le cache des produits."""
        cls.delete_pattern("api:*produits*")
        cls.delete_pattern("api:*prix*")
    
    @classmethod
    def invalidate_magasins(cls):
        """Invalider le cache des magasins."""
        cls.delete_pattern("api:*magasins*")
    
    @classmethod
    def invalidate_categories(cls):
        """Invalider le cache des catégories."""
        cls.delete_pattern("api:*categories*")
