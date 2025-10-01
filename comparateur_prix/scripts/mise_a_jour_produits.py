#!/usr/bin/env python
import os
import sys
import argparse
import logging
import time
from datetime import datetime
import django

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from apps.produits.models import Produit, Categorie
from scripts.data_mining.utils import get_logger


def _recuperer_urls_scraping() -> tuple[list[str], list[str]]:
    """Récupère les URLs de scraping depuis l'environnement (.env)."""
    urls_ministeres = os.getenv('SCRAPER_MINISTERE_URLS', '')
    urls_super = os.getenv('SCRAPER_SUPERMARCHES_URLS', '')
    urls_hyper = os.getenv('SCRAPER_HYPERMARCHES_URLS', '')
    ministeres = [u.strip() for u in urls_ministeres.split(',') if u.strip()]
    supermarches = [u.strip() for u in urls_super.split(',') if u.strip()]
    hypermarches = [u.strip() for u in urls_hyper.split(',') if u.strip()]
    return ministeres, supermarches, hypermarches


def mettre_a_jour_produits(*, dry_run: bool = False, categorie_defaut: str = "Divers", verbose: bool = False) -> int:
    """Met à jour des produits et catégories.

    - Crée une catégorie par défaut si manquante
    - Exemple d'extension: intégrer scrapers et mapping produits
    """
    logger = get_logger()
    if verbose:
        logger.setLevel(logging.DEBUG)
    logger.info("Début de la mise à jour des produits...")

    categorie, _ = Categorie.objects.get_or_create(
        nom=categorie_defaut,
        defaults={'description': 'Produits divers'}
    )
    logger.info(f"Catégorie par défaut: {categorie.nom}")

    # Récupérer les cibles de scraping pour visibilité
    urls_ministeres, urls_supermarches, urls_hypermarches = _recuperer_urls_scraping()
    logger.info(
        "Cibles scraping -> ministeres: %d URL(s), supermarchés: %d URL(s), hypermarchés: %d URL(s)",
        len(urls_ministeres), len(urls_supermarches), len(urls_hypermarches)
    )

    # Exemple d'opération dry-run
    if dry_run:
        logger.info("Mode dry-run: aucune écriture en base effectuée")
        if urls_supermarches:
            logger.info("[dry-run] Scraperait %d URL(s) supermarchés", len(urls_supermarches))
        if urls_hypermarches:
            logger.info("[dry-run] Scraperait %d URL(s) hypermarchés", len(urls_hypermarches))
        logger.info("[dry-run] Validerait/mapperait les produits vers la catégorie '%s'", categorie_defaut)
        logger.info("Simulation terminée.")
        return 0

    # Déclencher le scraping/configuration via la management command dédiée
    try:
        debut = time.perf_counter()
        logger.info("Lancement du scraping via la commande 'update_prices' (configuration via .env)")
        call_command('update_prices')
        duree = time.perf_counter() - debut
        logger.info("Scraping terminé en %.2f s", duree)
    except Exception as exc:
        logger.error(f"Erreur lors du scraping: {exc}")
        # On n'arrête pas le processus complet pour autant

    # Exemple minimal de logique d'enrichissement (à étendre selon besoin):
    # Ici vous pouvez ajouter du mapping produit -> catégorie, marque, etc.
    # Pour l'instant, on se contente de valider l'existence de la catégorie par défaut.
    logger.info("Mise à jour des produits terminée.")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Mettre à jour les produits")
    parser.add_argument('--dry-run', action='store_true', help='Exécuter sans écrire')
    parser.add_argument('--categorie-defaut', default='Divers', help='Nom de la catégorie par défaut')
    parser.add_argument('--verbose', action='store_true', help='Logs détaillés')
    return parser.parse_args(argv)


if __name__ == '__main__':
    args = parse_args()
    sys.exit(mettre_a_jour_produits(dry_run=args.dry_run, categorie_defaut=args.categorie_defaut, verbose=args.verbose))