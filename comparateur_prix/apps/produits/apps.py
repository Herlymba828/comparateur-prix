from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ProduitsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.produits'
    verbose_name = _("Gestion des produits")
    
    def ready(self):
        import apps.produits.signals