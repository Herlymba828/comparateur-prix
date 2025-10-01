from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class UtilisateursConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.utilisateurs'
    verbose_name = _('Utilisateurs')
    
    def ready(self):
        """Import des signaux lors du chargement de l'application"""
        import apps.utilisateurs.signals