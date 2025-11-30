from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Produit, Prix
from .search import index_product, delete_product
from .services.price_enrichment import PriceEnrichmentService
import os
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Produit)
def product_saved(sender, instance, created, **kwargs):
    # Indexer/mettre à jour dans Elasticsearch si activé
    try:
        enabled = os.getenv('SEARCH_INDEX_ENABLED', 'true').lower() in ('1','true','yes','y')
        if not enabled:
            return
        if instance.est_actif:
            index_product(instance)
        else:
            delete_product(instance.id)
    except Exception as e:
        # Ne pas bloquer la création de produit si Elasticsearch n'est pas disponible
        # Logger l'erreur mais continuer
        logger.warning(f"Impossible d'indexer le produit {instance.id} dans Elasticsearch: {type(e).__name__} - {str(e)}")
        pass
    
    # Invalider le cache de recherche (les recherches peuvent inclure ce produit)
    try:
        # Invalider les caches de recherche génériques
        # Note: On ne peut pas invalider toutes les clés de recherche facilement,
        # mais on peut invalider les caches spécifiques au produit
        PriceEnrichmentService.invalidate_cache(produit_id=instance.id)
        logger.debug(f"Cache invalidé pour produit {instance.id} après sauvegarde")
    except Exception as e:
        logger.warning(f"Erreur lors de l'invalidation du cache pour produit {instance.id}: {e}")

@receiver(post_delete, sender=Produit)
def product_deleted(sender, instance, **kwargs):
    try:
        enabled = os.getenv('SEARCH_INDEX_ENABLED', 'true').lower() in ('1','true','yes','y')
        if not enabled:
            return
        delete_product(instance.id)
    except Exception:
        pass
    
    # Invalider le cache du produit supprimé
    try:
        PriceEnrichmentService.invalidate_cache(produit_id=instance.id)
        logger.debug(f"Cache invalidé pour produit {instance.id} après suppression")
    except Exception as e:
        logger.warning(f"Erreur lors de l'invalidation du cache pour produit {instance.id}: {e}")

@receiver(post_save, sender=Prix)
def price_saved(sender, instance, created, **kwargs):
    """Invalide le cache quand un prix est créé ou modifié"""
    try:
        # Invalider le cache du service d'enrichissement des prix
        PriceEnrichmentService.invalidate_cache(
            produit_id=instance.produit_id,
            magasin_id=instance.magasin_id
        )
        logger.debug(f"Cache invalidé pour prix produit={instance.produit_id}, magasin={instance.magasin_id}")
    except Exception as e:
        logger.warning(f"Erreur lors de l'invalidation du cache pour prix {instance.id}: {e}")

@receiver(post_delete, sender=Prix)
def price_deleted(sender, instance, **kwargs):
    """Invalide le cache quand un prix est supprimé"""
    try:
        # Invalider le cache du service d'enrichissement des prix
        PriceEnrichmentService.invalidate_cache(
            produit_id=instance.produit_id,
            magasin_id=instance.magasin_id
        )
        logger.debug(f"Cache invalidé pour prix supprimé produit={instance.produit_id}, magasin={instance.magasin_id}")
    except Exception as e:
        logger.warning(f"Erreur lors de l'invalidation du cache pour prix supprimé {instance.id}: {e}")
