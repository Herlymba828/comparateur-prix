# Ajouter ces tâches dans le fichier config/celery.py existant
from __future__ import absolute_import
import os
import sys
from pathlib import Path
from celery import Celery

# Ajouter le répertoire racine du projet au PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

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
    # Exécute tous les jours avec sauvegarde automatique en base de données
    'dgccrf-scrape-quotidien': {
        'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
        'schedule': 86400.0,  # 1 jour (86400 secondes)
        'kwargs': {
            'limit': None,  # Pas de limite
            'unified': True,
            'save': True,  # Sauvegarde automatique en base de données
            'only_changed': True,  # Mode incrémental pour performance
            'csv_out': None,  # Pas de CSV pour les runs quotidiens (gain d'espace)
            'sql_out': None,  # Pas de SQL pour les runs quotidiens
            'report_out': None,  # Rapport avec timestamp automatique
            'sources': ['auto', 'prix_homologue', 'liste_produit', 'produit_petrolier'],  # Toutes les sources
        },
    },
    # Scraping DGCCRF hebdomadaire (rafraîchissement complet toutes les sources)
    # Exécute tous les 7 jours avec sauvegarde automatique
    'dgccrf-scrape-hebdomadaire': {
        'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
        'schedule': 604800.0,  # 7 jours (604800 secondes)
        'kwargs': {
            'limit': None,
            'unified': True,
            'save': True,  # Sauvegarde automatique en base de données
            'only_changed': False,  # Rafraîchissement complet
            'csv_out': None,
            'sql_out': None,
            'report_out': None,
            'sources': ['auto', 'prix_homologue', 'liste_produit', 'produit_petrolier'],  # Toutes les sources
        },
    },
    # Scraping DGCCRF mensuel (rafraîchissement complet avec exports)
    # Exécute tous les 30 jours avec sauvegarde automatique
    'dgccrf-scrape-mensuel': {
        'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
        'schedule': 2592000.0,  # 30 jours (2592000 secondes)
        'kwargs': {
            'limit': None,
            'unified': True,
            'save': True,  # Sauvegarde automatique en base de données
            'only_changed': False,  # Rafraîchissement complet
            'csv_out': None,  # CSV avec timestamp automatique
            'sql_out': None,  # SQL avec timestamp automatique
            'report_out': None,  # Rapport avec timestamp automatique
            'sources': ['auto', 'prix_homologue', 'liste_produit', 'produit_petrolier'],  # Toutes les sources
        },
    },
    # Géocoder quotidiennement les magasins sans coordonnées (si clé HERE fournie)
    'geocode-magasins-daily': {
        'task': 'apps.magasins.tasks.geocode_missing_magasins',
        'schedule': 86400.0,  # 1 jour
        'args': (200,),
    },
    # Backup quotidien de la base de données (tous les jours à 3h du matin)
    'backup-database-quotidien': {
        'task': 'apps.produits.tasks.backup_database_task',
        'schedule': 86400.0,  # 1 jour (86400 secondes)
        'kwargs': {
            'format_type': 'sql',  # Backup SQL uniquement pour les runs quotidiens
            'compress': True,  # Compresser pour économiser l'espace
            'keep': 7,  # Garder 7 jours de backups
        },
    },
    # Backup complet hebdomadaire (SQL + JSON, tous les dimanches)
    'backup-database-hebdomadaire': {
        'task': 'apps.produits.tasks.backup_database_task',
        'schedule': 604800.0,  # 7 jours (604800 secondes)
        'kwargs': {
            'format_type': 'both',  # Backup SQL + JSON
            'compress': True,
            'keep': 4,  # Garder 4 semaines de backups
        },
    },
}