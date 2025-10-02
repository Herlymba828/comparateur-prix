import csv
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, Iterable, List, Tuple, Optional

from django.core.management.base import BaseCommand, CommandParser
from django.conf import settings
from unidecode import unidecode

from apps.produits.models import Produit, Categorie
from apps.magasins.models import Magasin


def normalize_text(s: str) -> str:
    if s is None:
        return ''
    s = unidecode(str(s)).lower().strip()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


DGCCRF_CODE_PATTERN = re.compile(r"#G(1[5-9]|2[0-1])\b", re.IGNORECASE)
SUBCAT_PATTERN = re.compile(r"\bmt-\d+\b", re.IGNORECASE)


def extract_dgccrf_code(row: Dict[str, Any]) -> Optional[str]:
    """Cherche un code DGCCRF de type #G15..#G21 dans différents champs et retourne 'G15'... s'il est trouvé."""
    fields = ['categorie', 'category', 'nom', 'name', 'description', 'titre', 'title']
    for k in fields:
        v = row.get(k)
        if not v:
            continue
        m = DGCCRF_CODE_PATTERN.search(str(v))
        if m:
            return m.group(0).lstrip('#').upper()  # e.g. 'G15'
    return None


def extract_subcategory(row: Dict[str, Any]) -> Optional[str]:
    """Détecte un token de sous-catégorie du type 'mt-3' dans les champs texte."""
    fields = ['categorie', 'category', 'nom', 'name', 'description', 'titre', 'title']
    for k in fields:
        v = row.get(k)
        if not v:
            continue
        m = SUBCAT_PATTERN.search(str(v))
        if m:
            return m.group(0).lower()  # e.g. 'mt-3'
    return None


def normalize_brand(b: str) -> str:
    s = normalize_text(b)
    s = s.replace('&', 'and')
    return s


def load_rows(path: str, limit: int | None = None) -> List[Dict[str, Any]]:
    ext = os.path.splitext(path)[1].lower()
    rows: List[Dict[str, Any]] = []
    if ext in ('.json', '.ndjson'):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'items' in data:
                data = data['items']
            if not isinstance(data, list):
                raise ValueError('Le fichier JSON doit contenir une liste ou une clé items')
            rows = data
    elif ext in ('.csv',):
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    else:
        raise ValueError('Format non supporté (utilisez .json ou .csv)')
    if limit:
        rows = rows[:limit]
    return rows


def get_first(row: Dict[str, Any], keys: list[str]) -> str:
    for k in keys:
        if k in row and row[k] not in (None, ''):
            return str(row[k])
    return ''


def try_match_product(row: Dict[str, Any]) -> Tuple[str, Any]:
    """
    Tentative de match simple:
    - 1) EAN/GTIN exact (si présent)
    - 2) Nom+Marque normalisés exacts
    Retourne (strategy, produit|None)
    """
    ean_keys = ['ean', 'gtin', 'barcode']
    ean_val = None
    for k in ean_keys:
        v = row.get(k)
        if v:
            ean_val = str(v).strip()
            break
    if ean_val:
        p = Produit.objects.filter(code_barre__iexact=ean_val).first()
        if p:
            return ('ean', p)
    nom = normalize_text(row.get('nom') or row.get('name') or '')
    marque = normalize_brand(row.get('marque') or row.get('brand') or '')
    dgccrf_code = extract_dgccrf_code(row)  # e.g. 'G15'
    if not nom:
        return ('none', None)
    qs = Produit.objects.all()
    if hasattr(Produit, 'marque'):
        qs = qs.filter(marque__isnull=False)
    candidats = list(qs[:5000])
    for p in candidats:
        p_nom = normalize_text(getattr(p, 'nom', ''))
        p_marque = normalize_brand(getattr(p.marque, 'nom', '') if p.marque_id else '')
        if nom == p_nom and (not marque or marque == p_marque):
            return ('exact', p)
    return ('none', None)


class Command(BaseCommand):
    help = "Analyse un fichier DGCCRF (json/csv) et rapporte les correspondances avec la BDD (sans insertion)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--file', required=True, help='Chemin du fichier scrap DGCCRF (.json ou .csv)')
        parser.add_argument('--limit', type=int, default=None, help='Limiter le nombre de lignes analysées')
        parser.add_argument('--out', default=None, help='Chemin de sortie du rapport CSV (défaut: media/import_logs/...)')

    def handle(self, *args, **options):
        path: str = options['file']
        limit: int | None = options.get('limit')
        out: str | None = options.get('out')

        rows = load_rows(path, limit)
        total = len(rows)
        matched_ean = 0
        matched_exact = 0
        unmatched = 0

        now = datetime.now().strftime('%Y%m%d_%H%M%S')
        out_dir = os.path.join(settings.MEDIA_ROOT, 'import_logs')
        os.makedirs(out_dir, exist_ok=True)
        out_path = out or os.path.join(out_dir, f'dgccrf_analysis_{now}.csv')

        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'source_id', 'nom', 'marque', 'categorie', 'prix', 'devise', 'ean',
                'dgccrf_code', 'subcat',
                'DESIGNATION', 'PRIX_GROS', 'PRIX_DEMI_GROS', 'DETAIL',
                'match_strategy', 'produit_id', 'produit_nom', 'produit_marque'
            ])
            for r in rows:
                strat, prod = try_match_product(r)
                if strat == 'ean':
                    matched_ean += 1
                elif strat == 'exact':
                    matched_exact += 1
                else:
                    unmatched += 1
                subcat = extract_subcategory(r)
                designation = (r.get('nom') or r.get('name') or '')
                prix_gros = get_first(r, ['PRIX GROSPRIX', 'PRIX_GROS', 'prix_gros', 'grosprix', 'prix gros'])
                prix_demi_gros = get_first(r, ['DEMI GROSPRIX', 'DEMI_GROS', 'demi_gros', 'demi gros'])
                detail = get_first(r, ['DETAIL', 'detail', 'Description', 'description'])
                writer.writerow([
                    r.get('id') or r.get('source_product_id') or '',
                    r.get('nom') or r.get('name') or '',
                    r.get('marque') or r.get('brand') or '',
                    r.get('categorie') or r.get('category') or '',
                    r.get('prix') or r.get('price') or '',
                    r.get('devise') or r.get('currency') or '',
                    r.get('ean') or r.get('gtin') or r.get('barcode') or '',
                    extract_dgccrf_code(r) or '',
                    subcat or '',
                    designation,
                    prix_gros,
                    prix_demi_gros,
                    detail,
                    strat,
                    getattr(prod, 'id', '') if prod else '',
                    getattr(prod, 'nom', '') if prod else '',
                    getattr(prod.marque, 'nom', '') if prod and prod.marque_id else '',
                ])

        self.stdout.write(self.style.SUCCESS(
            f"Analyse terminée: total={total}, ean={matched_ean}, exact={matched_exact}, unmatched={unmatched}\nRapport: {out_path}"
        ))
