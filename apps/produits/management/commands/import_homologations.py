import os
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from apps.produits.models import HomologationProduit, PrixHomologue
from scripts.scraper_dgccrf import DgccrfScraper

logger = logging.getLogger(__name__)


def _to_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError):
        return None


def _to_date(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    return None


class Command(BaseCommand):
    help = "Importer les prix homologués depuis DGCCRF/EDIG et historiser en base."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--limit", type=int, default=None, help="Limiter le nombre d'entrées importées")
        parser.add_argument("--since-date", type=str, default=None, help="Ne prendre que les publications depuis cette date (YYYY-MM-DD)")
        parser.add_argument("--dry-run", action="store_true", help="Ne pas écrire en base")
        parser.add_argument("--verbose", action="store_true", help="Logs détaillés")

    def handle(self, *args, **options):
        if options.get("verbose"):
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        base_url = os.getenv("DGCCRF_BASE_URL")
        user_agent = os.getenv("DGCCRF_USER_AGENT")
        request_delay = float(os.getenv("DGCCRF_REQUEST_DELAY", "1.0"))

        self.stdout.write(self.style.MIGRATE_HEADING("Import des prix homologués (DGCCRF/EDIG)"))
        logger.info("BASE_URL=%s UA=%s delay=%.2fs", base_url, user_agent, request_delay)

        scraper = DgccrfScraper(base_url=base_url, user_agent=user_agent, request_delay=request_delay)
        limit = options.get("limit")
        since_date = _to_date(options.get("since_date")) if options.get("since_date") else None
        dry_run = options.get("dry_run", False)

        created_products = 0
        updated_products = 0
        created_prices = 0
        skipped_by_date = 0
        processed = 0

        items_iter = scraper.iter_homologations()
        try:
            with transaction.atomic():
                for item in items_iter:
                    if limit and processed >= limit:
                        break

                    dp = _to_date(item.get("date_publication"))
                    if since_date and dp and dp < since_date:
                        skipped_by_date += 1
                        continue

                    produit, created = HomologationProduit.objects.get_or_create(
                        nom=(item.get("nom") or "").strip(),
                        format=(item.get("format") or "").strip(),
                        marque=(item.get("marque") or "").strip(),
                        categorie=(item.get("categorie") or "Non classé").strip(),
                        defaults={
                            "sous_categorie": (item.get("sous_categorie") or "").strip(),
                            "reference_titre": (item.get("reference_titre") or "").strip(),
                            "reference_numero": (item.get("reference_numero") or "").strip(),
                            "reference_url": (item.get("reference_url") or "").strip(),
                        }
                    )
                    if created:
                        created_products += 1
                    else:
                        # Mettre à jour les références si fournies
                        changed = False
                        for field in ("sous_categorie", "reference_titre", "reference_numero", "reference_url"):
                            new_val = (item.get(field) or "").strip()
                            if getattr(produit, field) != new_val and new_val:
                                setattr(produit, field, new_val)
                                changed = True
                        if changed:
                            produit.save(update_fields=["sous_categorie", "reference_titre", "reference_numero", "reference_url", "date_modification"])
                            updated_products += 1

                    prix_unitaire = _to_decimal(item.get("prix_unitaire"))
                    unite = (item.get("unite") or "").strip()
                    prix_detail = _to_decimal(item.get("prix_detail"))
                    prix_par_kilo = _to_decimal(item.get("prix_par_kilo"))

                    # Déduplication par (produit, date_publication, unite, prix_unitaire)
                    prix_obj, created_price = PrixHomologue.objects.get_or_create(
                        produit=produit,
                        date_publication=dp,
                        unite=unite,
                        prix_unitaire=prix_unitaire if prix_unitaire is not None else Decimal("0"),
                        defaults={
                            "prix_detail": prix_detail,
                            "prix_par_kilo": prix_par_kilo,
                            "periode_debut": _to_date(item.get("periode_debut")),
                            "periode_fin": _to_date(item.get("periode_fin")),
                        }
                    )
                    if created_price:
                        created_prices += 1
                    else:
                        # Mettre à jour les valeurs si elles diffèrent
                        fields_to_update = []
                        if prix_detail is not None and prix_obj.prix_detail != prix_detail:
                            prix_obj.prix_detail = prix_detail
                            fields_to_update.append("prix_detail")
                        if prix_par_kilo is not None and prix_obj.prix_par_kilo != prix_par_kilo:
                            prix_obj.prix_par_kilo = prix_par_kilo
                            fields_to_update.append("prix_par_kilo")
                        pd = _to_date(item.get("periode_debut"))
                        pf = _to_date(item.get("periode_fin"))
                        if pd and prix_obj.periode_debut != pd:
                            prix_obj.periode_debut = pd
                            fields_to_update.append("periode_debut")
                        if pf and prix_obj.periode_fin != pf:
                            prix_obj.periode_fin = pf
                            fields_to_update.append("periode_fin")
                        if fields_to_update:
                            prix_obj.save(update_fields=fields_to_update + ["date_creation"])  # date_creation non modifiée mais OK

                    processed += 1

                if dry_run:
                    logger.info("Mode dry-run activé: rollback des écritures")
                    raise transaction.TransactionManagementError("Dry run - rollback")
        except transaction.TransactionManagementError:
            # dry run rollback
            pass

        self.stdout.write(self.style.SUCCESS(
            f"Import terminé: processed={processed}, produits+={created_products}/{updated_products} created/updated, prix+={created_prices}, skipped_by_date={skipped_by_date}"
        ))
