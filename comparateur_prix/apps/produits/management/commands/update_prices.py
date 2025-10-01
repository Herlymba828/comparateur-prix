from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone
from typing import Any

from apps.produits.models import (
    HomologationProduit, PrixHomologue,
)

# Placeholders de normalisation (adaptez selon vos utilitaires existants)

def normalize_text(s: str) -> str:
    import unicodedata, re
    if not s:
        return ""
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"\s+", " ", s.strip()).lower()
    return s


def normalize_format(s: str) -> str:
    import re
    if not s:
        return ""
    s = s.strip().lower().replace(',', '.')
    # Normalisations simples : espaces, x en *, etc.
    s = re.sub(r"\s+", " ", s)
    s = s.replace(' x ', 'x').replace('×', 'x')
    return s


class Command(BaseCommand):
    help = "Met à jour/normalise les références homologation (champs *_norm) et peut importer de nouveaux prix homologués."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--dry-run', action='store_true', help='N’effectue aucune écriture.')
        parser.add_argument('--only-normalize', action='store_true', help='Ne fait que normaliser les champs *_norm.')

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = options.get('dry_run', False)
        only_normalize = options.get('only_normalize', False)

        self.stdout.write(self.style.MIGRATE_HEADING('==> Mise à jour des champs normalisés sur HomologationProduit'))
        updated = 0
        qs = HomologationProduit.objects.all().only('id', 'nom', 'marque', 'format', 'categorie')

        with transaction.atomic():
            for hp in qs:
                nom_norm = normalize_text(hp.nom)
                marque_norm = normalize_text(hp.marque)
                format_norm = normalize_format(hp.format)

                if hp.nom_norm != nom_norm or hp.marque_norm != marque_norm or hp.format_norm != format_norm:
                    hp.nom_norm = nom_norm
                    hp.marque_norm = marque_norm
                    hp.format_norm = format_norm
                    if not dry_run:
                        hp.save(update_fields=['nom_norm', 'marque_norm', 'format_norm'])
                    updated += 1

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(f'Champs normalisés mis à jour pour {updated} homologations.'))

        if only_normalize:
            return

        # Espace réservé pour l’import/rafraîchissement des PrixHomologue
        # À compléter selon votre source de données (CSV, API, etc.)
        self.stdout.write(self.style.NOTICE('Aucun import de PrixHomologue exécuté (section à compléter).'))
