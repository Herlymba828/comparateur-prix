import logging
from typing import Optional
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.produits.models import HomologationProduit, PrixHomologue
from scripts.scraper_dgccrf import DgccrfScraper

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Impor­te les données DGCCRF (pages HTML prix homologués et liste de produits) "
        "et les enregistre dans HomologationProduit / PrixHomologue."
    )

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Ne rien écrire en base')
        parser.add_argument('--limit', type=int, default=None, help="Limiter le nombre d'éléments traités")

    def handle(self, *args, **options):
        dry_run: bool = options['dry_run']
        limit: Optional[int] = options['limit']

        scraper = DgccrfScraper()
        total = 0

        def _persist_item(item: dict, source_hint: Optional[str] = None) -> None:
            """Persiste un enregistrement HomologationProduit + PrixHomologue.

            Mapping minimum:
              - HomologationProduit: (nom, format, marque, categorie, sous_categorie, references)
              - PrixHomologue: un enregistrement principal où prix_unitaire = prix_libreville (si disponible) sinon prix_province
                unite: laissé vide. On stocke l'autre prix dans prix_detail si pertinent.
            """
            nom = (item.get('nom') or '').strip()
            if not nom:
                return

            categorie = (item.get('categorie') or 'Non classé')[:120]
            sous_categorie = (item.get('sous_categorie') or '')[:120]
            format_txt = (item.get('format') or '')[:120]
            marque = (item.get('marque') or '')[:120]

            ref_titre = (item.get('reference_titre') or '')[:255]
            ref_numero = (item.get('reference_numero') or '')[:120]
            ref_url = (item.get('reference_url') or '')[:200]

            produit, _ = HomologationProduit.objects.get_or_create(
                nom=nom,
                format=format_txt,
                marque=marque,
                categorie=categorie,
                defaults={
                    'sous_categorie': sous_categorie,
                    'reference_titre': ref_titre,
                    'reference_numero': ref_numero,
                    'reference_url': ref_url,
                }
            )
            # Mettre à jour les refs si vides ou différentes
            updated = False
            if not produit.sous_categorie and sous_categorie:
                produit.sous_categorie = sous_categorie
                updated = True
            if ref_titre and produit.reference_titre != ref_titre:
                produit.reference_titre = ref_titre
                updated = True
            if ref_numero and produit.reference_numero != ref_numero:
                produit.reference_numero = ref_numero
                updated = True
            if ref_url and produit.reference_url != ref_url:
                produit.reference_url = ref_url
                updated = True
            if updated and not dry_run:
                produit.save()

            # Prix séparés par localisation
            prix_lib = item.get('prix_libreville')
            prix_prov = item.get('prix_province')
            prix_unitaire = item.get('prix_unitaire')
            unite = item.get('unite') or ''
            extra = item.get('extra') or {}
            prix_gros = extra.get('prix_gros')
            prix_demi_gros = extra.get('prix_demi_gros')

            # Dates si fournies
            def _parse_date(s: Optional[str]) -> Optional[datetime]:
                if not s:
                    return None
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
                    try:
                        return datetime.strptime(s, fmt)
                    except Exception:
                        pass
                return None

            date_publication = _parse_date(item.get('date_publication'))
            periode_debut = _parse_date(item.get('periode_debut'))
            periode_fin = _parse_date(item.get('periode_fin'))

            if dry_run:
                return

            def _create_unique(ph_kwargs: dict):
                """Créer/mettre à jour en respectant la contrainte d'unicité logique.
                Utilise update_or_create avec lookup = clés uniques et defaults = champs modifiables.
                """
                try:
                    lookup = {
                        'produit': ph_kwargs['produit'],
                        'prix_unitaire': ph_kwargs['prix_unitaire'],
                        'unite': ph_kwargs.get('unite') or '',
                        'date_publication': ph_kwargs.get('date_publication'),
                        'localisation': ph_kwargs.get('localisation') or '',
                    }
                    defaults = {
                        'prix_detail': ph_kwargs.get('prix_detail'),
                        'prix_par_kilo': ph_kwargs.get('prix_par_kilo'),
                        'prix_gros': ph_kwargs.get('prix_gros'),
                        'prix_demi_gros': ph_kwargs.get('prix_demi_gros'),
                        'periode_debut': ph_kwargs.get('periode_debut'),
                        'periode_fin': ph_kwargs.get('periode_fin'),
                        'source': ph_kwargs.get('source') or '',
                    }
                    PrixHomologue.objects.update_or_create(**lookup, defaults=defaults)
                except Exception as e:
                    logger.error(f"Echec update_or_create PrixHomologue: {e}")

            # 1) Si un prix_unitaire générique est fourni (sans localisation)
            if prix_unitaire is not None:
                _create_unique({
                    'produit': produit,
                    'prix_unitaire': prix_unitaire,
                    'unite': unite or '',
                    'prix_detail': item.get('prix_detail') or None,
                    'prix_par_kilo': item.get('prix_par_kilo') or None,
                    'prix_gros': prix_gros,
                    'prix_demi_gros': prix_demi_gros,
                    'date_publication': date_publication.date() if date_publication else None,
                    'periode_debut': periode_debut.date() if periode_debut else None,
                    'periode_fin': periode_fin.date() if periode_fin else None,
                    'localisation': '',
                    'source': source_hint or 'liste_produit',
                })

            # 2) Sinon, créer des enregistrements séparés pour Libreville et Province si présents
            if prix_lib is not None:
                _create_unique({
                    'produit': produit,
                    'prix_unitaire': prix_lib,
                    'unite': unite or '',
                    'prix_detail': None,
                    'prix_par_kilo': item.get('prix_par_kilo') or None,
                    'date_publication': date_publication.date() if date_publication else None,
                    'periode_debut': periode_debut.date() if periode_debut else None,
                    'periode_fin': periode_fin.date() if periode_fin else None,
                    'localisation': 'libreville',
                    'source': source_hint or 'prix_homologue',
                })
            if prix_prov is not None:
                _create_unique({
                    'produit': produit,
                    'prix_unitaire': prix_prov,
                    'unite': unite or '',
                    'prix_detail': None,
                    'prix_par_kilo': item.get('prix_par_kilo') or None,
                    'date_publication': date_publication.date() if date_publication else None,
                    'periode_debut': periode_debut.date() if periode_debut else None,
                    'periode_fin': periode_fin.date() if periode_fin else None,
                    'localisation': 'province',
                    'source': source_hint or 'prix_homologue',
                })

        # Traiter PRIX_HOMOLOGUE
        self.stdout.write(self.style.NOTICE("Scraping: prix homologués (page HTML)"))
        count = 0
        with transaction.atomic():
            for it in scraper.iter_from_prix_homologue_page():
                if limit and count >= limit:
                    break
                if dry_run:
                    logger.info(f"[DRY] {it}")
                else:
                    _persist_item(it, source_hint='prix_homologue')
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Prix homologués: {count} éléments traités"))
        total += count

        # Traiter LISTE_PRODUIT
        self.stdout.write(self.style.NOTICE("Scraping: liste produit (page HTML)"))
        count = 0
        with transaction.atomic():
            for it in scraper.iter_from_liste_produit_page():
                if limit and count >= limit:
                    break
                if dry_run:
                    logger.info(f"[DRY] {it}")
                else:
                    _persist_item(it, source_hint='liste_produit')
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Liste produit: {count} éléments traités"))
        total += count

        self.stdout.write(self.style.SUCCESS(f"Terminé. Total: {total}"))
