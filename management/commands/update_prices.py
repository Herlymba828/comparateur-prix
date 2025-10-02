from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Met à jour les prix/produits depuis les sources configurées (squelette)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Exécuter sans modifier la base de données",
        )

    def handle(self, *args, **options):
        dry_run = bool(options.get("dry_run"))
        if dry_run:
            logger.info("[update_prices] Mode dry-run: aucune écriture en base.")
        # Squelette no-op pour éviter les erreurs d'appel depuis scripts/mise_a_jour_produits.py
        logger.info("[update_prices] Commande exécutée (squelette). Implémentez la logique de scraping ici.")
        self.stdout.write(self.style.SUCCESS("update_prices terminé (squelette)"))
