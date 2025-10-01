# Ajouter ces tâches dans le fichier config/celery.py existant
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['apps.recommandations.tasks', 'apps.produits.tasks', 'apps.analyses.tasks', 'apps.analyses.tasks_graph'])

# Planification des tâches périodiques
app.conf.beat_schedule = {
    'entrainer-modeles-hebdomadaire': {
        'task': 'apps.recommandations.tasks.entrainer_modele_recommandation',
        'schedule': 604800.0,  # 7 jours en secondes
        'args': ('contenu',)
    },
    'generer-recommandations-quotidiennes': {
        'task': 'apps.recommandations.tasks.generer_recommandations_quotidiennes',
        'schedule': 86400.0,  # 1 jour en secondes
    },
    'nettoyer-historique-mensuel': {
        'task': 'apps.recommandations.tasks.nettoyer_historique_ancien',
        'schedule': 2592000.0,  # 30 jours en secondes
    },
    # Vérification des alertes prix
    'verifier-alertes-quotidienne': {
        'task': 'apps.produits.tasks.verifier_alertes_prix_task',
        'schedule': 86400.0,  # 1 jour
        'args': (None, ['quotidienne', 'instantanee']),
    },
    'verifier-alertes-hebdomadaire': {
        'task': 'apps.produits.tasks.verifier_alertes_prix_task',
        'schedule': 604800.0,  # 7 jours
        'args': (None, ['hebdomadaire']),
    },
    'verifier-alertes-mensuelle': {
        'task': 'apps.produits.tasks.verifier_alertes_prix_task',
        'schedule': 2592000.0,  # 30 jours
        'args': (None, ['mensuelle']),
    },
    'verifier-alertes-instantanee': {
        'task': 'apps.produits.tasks.verifier_alertes_prix_task',
        'schedule': 900.0,  # 15 minutes
        'args': (None, ['instantanee']),
    },
    # Comparaison quotidienne des prix actuels vs prix homologués
    'comparer-prix-homologues-quotidien': {
        'task': 'apps.produits.tasks.comparer_prix_homologues_task',
        'schedule': 86400.0,  # 1 jour
    },
    # Graph analytics: build magasin-magasin projection daily at ~02:00
    'build-graph-magasin-daily': {
        'task': 'apps.analyses.tasks_graph.generer_snapshots_graphes',
        'schedule': 86400.0,  # 1 jour
        'args': ('magasin-magasin', 90),  # type, window_days
    },
    # Import quotidien des données DGCCRF (prix homologués, liste produits)
    'import-dgccrf-quotidien': {
        'task': 'apps.produits.tasks.import_dgccrf_task',
        'schedule': 86400.0,  # 1 jour
        'args': (),
    },
}