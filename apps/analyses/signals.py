from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import AnalysePrix, PriceAggregate
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=AnalysePrix)
def log_creation_analyse(sender, instance, created, **kwargs):
    """Logger la création d'une analyse"""
    if created:
        logger.info(f"Nouvelle analyse créée: {instance.titre} (ID: {instance.id})")

@receiver(pre_delete, sender=PriceAggregate)
def nettoyer_cache_aggregats(sender, instance, **kwargs):
    """Nettoyer le cache lié aux agrégats supprimés"""
    from django.core.cache import cache
    # Invalider les caches liés à cet agrégat
    cache_keys_to_delete = [
        f"aggregat_{instance.produit_id}_{instance.fenetre_debut}",
        f"aggregat_{instance.categorie_id}_{instance.fenetre_debut}",
    ]
    for key in cache_keys_to_delete:
        cache.delete(key)