from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Produit
from .search import index_product, delete_product
import os

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
    except Exception:
        pass

@receiver(post_delete, sender=Produit)
def product_deleted(sender, instance, **kwargs):
    try:
        enabled = os.getenv('SEARCH_INDEX_ENABLED', 'true').lower() in ('1','true','yes','y')
        if not enabled:
            return
        delete_product(instance.id)
    except Exception:
        pass
