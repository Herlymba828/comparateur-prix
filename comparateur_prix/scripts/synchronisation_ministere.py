#!/usr/bin/env python
import os
import django
import sys
import argparse
import requests
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from scripts.data_mining.utils import get_logger, get_session, safe_get


def synchroniser_donnees_ministere(*, endpoint: str, token: str | None = None, timeout: int = 30, output: str | None = None) -> int:
    """Synchronise les données avec une API ministérielle (exemple générique)."""
    logger = get_logger()
    logger.info("Début de la synchronisation avec les données du ministère...")
    headers = {'Accept': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    session = get_session(timeout=timeout, retries=3, backoff=0.5)
    resp = safe_get(session, endpoint, timeout=timeout, headers=headers, retries=3)
    if not resp or not resp.ok:
        logger.error(f"Erreur de requête: HTTP {getattr(resp, 'status_code', 'NA')}")
        return 1

    # Exemple: afficher la taille du payload
    try:
        data = resp.json()
    except ValueError:
        logger.error("Réponse non JSON")
        return 1

    logger.info(f"Données reçues: {len(data) if hasattr(data, '__len__') else 'n/a'} éléments")

    if output:
        try:
            with open(output, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Export JSON: {output}")
        except Exception as exc:
            logger.error(f"Échec export JSON: {exc}")

    logger.info("Synchronisation terminée.")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Synchronisation ministère")
    parser.add_argument('--endpoint', required=True, help='URL de l\'API à interroger')
    parser.add_argument('--token', help='Jeton d\'authentification (optionnel)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout en secondes')
    parser.add_argument('--output', help='Chemin de sortie JSON (optionnel)')
    return parser.parse_args(argv)


if __name__ == '__main__':
    args = parse_args()
    sys.exit(synchroniser_donnees_ministere(endpoint=args.endpoint, token=args.token, timeout=args.timeout, output=args.output))