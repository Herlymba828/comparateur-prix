"""
Utilitaires pour la gestion du cache de l'API.
"""
import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Préfixes des clés de cache
CACHE_PREFIX_SEARCH = 'search_produits'
CACHE_PREFIX_AUTOCOMPLETE = 'autocomplete'
CACHE_PREFIX_HOMOLOGATIONS = 'homologations_stats'


def invalidate_search_cache(produit_id=None, categorie_id=None, marque_nom=None):
    """
    Invalide les caches de recherche.
    
    Args:
        produit_id: ID du produit (optionnel)
        categorie_id: ID de la catégorie (optionnel)
        marque_nom: Nom de la marque (optionnel)
    
    Note:
        Comme les clés de cache sont basées sur des hash MD5 des paramètres,
        on ne peut pas invalider précisément. Cette fonction peut être étendue
        pour utiliser des patterns Redis ou des tags de cache.
    """
    try:
        # Pour l'instant, on ne peut pas invalider précisément les caches de recherche
        # car ils sont basés sur des hash MD5. On pourrait :
        # 1. Utiliser des tags de cache (nécessite django-redis avec tags)
        # 2. Utiliser des patterns Redis (nécessite accès direct à Redis)
        # 3. Utiliser un TTL plus court pour les recherches
        logger.debug(f"Invalidation du cache de recherche demandée (produit={produit_id}, categorie={categorie_id}, marque={marque_nom})")
        # TODO: Implémenter l'invalidation par pattern si nécessaire
    except Exception as e:
        logger.warning(f"Erreur lors de l'invalidation du cache de recherche: {e}")


def invalidate_autocomplete_cache(produit_nom=None):
    """
    Invalide les caches d'autocomplete.
    
    Args:
        produit_nom: Nom du produit (optionnel)
    
    Note:
        Les clés d'autocomplete sont basées sur le nom du produit en minuscules.
        On peut invalider précisément si le nom est fourni.
    """
    try:
        if produit_nom:
            cache_key = f"{CACHE_PREFIX_AUTOCOMPLETE}:{produit_nom.lower()}"
            cache.delete(cache_key)
            logger.debug(f"Cache autocomplete invalidé pour: {produit_nom}")
        else:
            # Invalider tous les caches d'autocomplete (à utiliser avec précaution)
            logger.warning("Invalidation complète du cache autocomplete demandée (non implémentée)")
    except Exception as e:
        logger.warning(f"Erreur lors de l'invalidation du cache autocomplete: {e}")


def invalidate_homologations_cache():
    """
    Invalide tous les caches de statistiques d'homologations.
    
    Note:
        Comme les clés sont basées sur des hash MD5 des filtres,
        on ne peut pas invalider précisément sans pattern matching Redis.
    """
    try:
        logger.debug("Invalidation du cache homologations demandée")
        # TODO: Implémenter l'invalidation par pattern si nécessaire
    except Exception as e:
        logger.warning(f"Erreur lors de l'invalidation du cache homologations: {e}")

