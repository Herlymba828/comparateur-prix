"""Configuration du scraper DGCCRF."""
import os
from typing import Dict, Any, Optional

# Configuration de base
DEFAULT_BASE_URL = os.getenv('DGCCRF_BASE_URL', 'https://www.dgccrf.ga/')
DEFAULT_USER_AGENT = os.getenv(
    'DGCCRF_USER_AGENT',
    'ComparateurPrixBot/1.0 (+contact@example.com)'
)

# Configuration des requêtes HTTP
REQUEST_DELAY_SEC = float(os.getenv('DGCCRF_REQUEST_DELAY', '1.0'))
REQUEST_TIMEOUT = float(os.getenv('DGCCRF_TIMEOUT', '30'))
MAX_RETRIES = int(os.getenv('DGCCRF_MAX_RETRIES', '3'))
BACKOFF_SEC = float(os.getenv('DGCCRF_BACKOFF', '1.5'))
HTTP_PROXY = os.getenv('DGCCRF_PROXY', '')

# Configuration des chemins
LOG_FILE = os.getenv('DGCCRF_LOG_FILE', '')
STATE_FILE = os.getenv('DGCCRF_STATE_FILE', '.dgccrf_state.json')
CHECKPOINT_PATH = os.getenv('DGCCRF_CHECKPOINT_PATH', '.dgccrf_checkpoint.json')
RAW_DIR = os.getenv('DGCCRF_RAW_DIR', '')
DEFAULT_REPORT_OUT = os.getenv('DGCCRF_REPORT_OUT', 'data/dgccrf_report.json')

# Fonctionnalités
SAVE_TO_DB = os.getenv('DGCCRF_SAVE_TO_DB', 'true').lower() == 'true'
RESPECT_ROBOTS = os.getenv('DGCCRF_RESPECT_ROBOTS', 'true').lower() == 'true'
SKIP_UNCHANGED = os.getenv('DGCCRF_SKIP_UNCHANGED', 'false').lower() == 'true'

# URLs des API
PRIX_HOMOLOGUE_URL = os.getenv(
    'DGCCRF_PRIX_HOMOLOGUE_URL',
    'https://www.dgccrf.ga/echo-prix-homologue'
)
LISTE_PRODUIT_URL = os.getenv(
    'DGCCRF_LISTE_PRODUIT_URL',
    'https://www.dgccrf.ga/echo-liste-produit'
)
PRODUIT_PETROLIER_URL = os.getenv(
    'DGCCRF_PRODUIT_PETROLIER_URL',
    'https://www.dgccrf.ga/echo-produit-petrolier'
)

# Configuration Open Food Facts
OFF_ENABLE = os.getenv('DGCCRF_OFF_ENABLE', 'false').lower() == 'true'
OFF_TIMEOUT = float(os.getenv('DGCCRF_OFF_TIMEOUT', '5'))
OFF_MIN_SCORE = float(os.getenv('DGCCRF_OFF_MIN_SCORE', '0.6'))

def get_config() -> Dict[str, Any]:
    """Retourne la configuration actuelle sous forme de dictionnaire."""
    return {
        'base_url': DEFAULT_BASE_URL,
        'user_agent': DEFAULT_USER_AGENT,
        'request_delay': REQUEST_DELAY_SEC,
        'timeout': REQUEST_TIMEOUT,
        'max_retries': MAX_RETRIES,
        'backoff': BACKOFF_SEC,
        'http_proxy': HTTP_PROXY,
        'log_file': LOG_FILE,
        'state_file': STATE_FILE,
        'checkpoint_path': CHECKPOINT_PATH,
        'raw_dir': RAW_DIR,
        'report_out': DEFAULT_REPORT_OUT,
        'save_to_db': SAVE_TO_DB,
        'respect_robots': RESPECT_ROBOTS,
        'skip_unchanged': SKIP_UNCHANGED,
        'prix_homologue_url': PRIX_HOMOLOGUE_URL,
        'liste_produit_url': LISTE_PRODUIT_URL,
        'produit_petrolier_url': PRODUIT_PETROLIER_URL,
        'off_enable': OFF_ENABLE,
        'off_timeout': OFF_TIMEOUT,
        'off_min_score': OFF_MIN_SCORE
    }

def print_config() -> None:
    """Affiche la configuration actuelle."""
    import json
    config = get_config()
    print("Configuration actuelle :")
    print(json.dumps(config, indent=2, ensure_ascii=False))
