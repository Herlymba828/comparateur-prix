from django.apps import AppConfig
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class RecommandationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.recommandations'
    verbose_name = 'Système de Recommandations'

    def ready(self):
        """Initialisation au démarrage de l'application (optionnelle).
        Par défaut, on évite toute initialisation lourde (sklearn/xgboost) au startup.
        Activez via settings.RECO_INIT_MODELS_ON_STARTUP = True si nécessaire.
        """
        if getattr(settings, 'RECO_INIT_MODELS_ON_STARTUP', False):
            try:
                from .modeles_ml import GestionnaireRecommandations
                self.gestionnaire = GestionnaireRecommandations()
                # Initialisation asynchrone pour ne pas bloquer le démarrage
                import threading
                thread = threading.Thread(target=self.gestionnaire.initialiser_modeles)
                thread.daemon = True
                thread.start()
                logger.info("Application Recommandations initialisée (modèles en cours d'init)")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation des modèles: {e}")
        else:
            logger.info("Application Recommandations chargée (init ML désactivée).")