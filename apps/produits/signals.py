from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Produit
from .search import index_product, delete_product

@receiver(post_save, sender=Produit)
def product_saved(sender, instance, created, **kwargs):
    # Indexer/mettre à jour dans Elasticsearch si actif
    try:
        if instance.est_actif:
            index_product(instance)
        else:
            delete_product(instance.id)
    except Exception:
        pass

@receiver(post_delete, sender=Produit)
def product_deleted(sender, instance, **kwargs):
    try:
        delete_product(instance.id)
    except Exception:
        pass
