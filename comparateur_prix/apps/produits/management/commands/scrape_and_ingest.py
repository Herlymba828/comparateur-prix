from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone
from typing import Any
import logging
import os

from apps.produits.models import Produit, Prix, HistoriquePrix

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Scrape les données (interne) et les enregistre en base de façon idempotente."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--limit', type=int, default=None, help='Limiter le nombre d\'éléments à traiter')
        parser.add_argument('--dry-run', action='store_true', help='N\'écrit pas en base, journalise seulement')
        parser.add_argument('--source', type=str, default=os.getenv('SCRAPER_SOURCE', 'local'), help='Source des données: local|autre')

    def handle(self, *args: Any, **options: Any) -> None:
        limit = options.get('limit')
        dry_run = options.get('dry_run', False)
        source = options.get('source')

        self.stdout.write(self.style.NOTICE(f"[INGEST] Démarrage - source={source} limit={limit} dry_run={dry_run}"))

        # 1) Récupérer les données via votre scraper interne (à remplacer par votre implémentation réelle)
        items = self.fetch_scraped_data(limit=limit, source=source)
        self.stdout.write(self.style.NOTICE(f"[INGEST] {len(items)} éléments à traiter"))

        created_prod = updated_prod = created_price = updated_price = 0

        with transaction.atomic():
            for it in items:
                # Exemple attendu: {'code_barre': '...', 'nom': '...', 'categorie_id': 1, 'marque_id': 2, 'prix': 1200, 'magasin_id': 3}
                data = self.normalize(it)
                if not data:
                    continue

                produit, prod_created = Produit.objects.update_or_create(
                    code_barre=data['code_barre'],
                    defaults={
                        'nom': data['nom'],
                        'categorie_id': data.get('categorie_id'),
                        'marque_id': data.get('marque_id'),
                        'est_actif': True,
                    }
                )
                created_prod += int(prod_created)
                updated_prod += int(not prod_created)

                prix_obj, price_created = Prix.objects.update_or_create(
                    produit=produit, magasin_id=data['magasin_id'],
                    defaults={
                        'prix_actuel': data['prix'],
                        'est_disponible': True,
                    }
                )
                if not price_created and prix_obj.prix_actuel != data['prix']:
                    # Historiser la variation
                    HistoriquePrix.objects.create(
                        prix=prix_obj,
                        ancien_prix=prix_obj.prix_actuel,
                        nouveau_prix=data['prix'],
                        raison='scrape',
                    )
                    prix_obj.prix_actuel = data['prix']
                    prix_obj.save(update_fields=['prix_actuel', 'date_modification'])
                    updated_price += 1
                else:
                    created_price += int(price_created)

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            f"[INGEST] Produits créés={created_prod}, maj={updated_prod}; Prix créés={created_price}, maj={updated_price}"
        ))

    # --- Implémentations à remplacer par votre scraper interne ---
    def fetch_scraped_data(self, limit: int | None, source: str):
        # TODO: remplacez par l'appel à votre code Python local de scraping
        # Mock minimal pour squelette
        sample = []
        return sample[:limit] if limit else sample

    def normalize(self, item: dict) -> dict | None:
        try:
            return {
                'code_barre': str(item['code_barre']).strip(),
                'nom': str(item['nom']).strip(),
                'categorie_id': item.get('categorie_id'),
                'marque_id': item.get('marque_id'),
                'magasin_id': item['magasin_id'],
                'prix': item['prix'],
            }
        except Exception:
            return None
