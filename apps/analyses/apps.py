from django.apps import AppConfig

class AnalysesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analyses'
    verbose_name = 'Analyses de Prix'

    def ready(self):
        import apps.analyses.signals