# Ajouter ces tâches dans le fichier config/celery.py existant
from __future__ import absolute_import
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(['apps.recommandations.tasks', 'apps.produits.tasks', 'apps.analyses.tasks', 'apps.analyses.tasks_graph', 'apps.magasins.tasks'])

# Planification des tâches périodiques
app.conf.beat_schedule = {
    'entrainer-modeles-hebdomadaire': {
        'task': 'apps.recommandations.tasks.entrainer_modele_recommandation',
    },
    'generer-recommandations-quotidiennes': {
        'task': 'apps.recommandations.tasks.generer_recommandations_quotidiennes',
        'schedule': 86400.0,  # 1 jour
    },
    'nettoyer-historique-mensuel': {
        'task': 'apps.recommandations.tasks.nettoyer_historique_ancien',
        'schedule': 2592000.0,  # 30 jours
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
    # Scraping DGCCRF quotidien (unified + save + only-changed)
    'dgccrf-scrape-quotidien': {
        'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
        'schedule': 86400.0,  # 1 jour
        'args': (None, True, True, True, 'data/dgccrf_daily.csv', 'data/dgccrf_daily.sql', 'data/dgccrf_daily_report.json'),
    },
    # Scraping DGCCRF mensuel (rafraîchissement complet)
    'dgccrf-scrape-mensuel': {
        'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
        'schedule': 2592000.0,  # 30 jours
        'args': (None, True, True, False, 'data/dgccrf_monthly.csv', 'data/dgccrf_monthly.sql', 'data/dgccrf_monthly_report.json'),
    },
    # Géocoder quotidiennement les magasins sans coordonnées (si clé HERE fournie)
    'geocode-magasins-daily': {
        'task': 'apps.magasins.tasks.geocode_missing_magasins',
        'schedule': 86400.0,  # 1 jour
        'args': (200,),
    },
}