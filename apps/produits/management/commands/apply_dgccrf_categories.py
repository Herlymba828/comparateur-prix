import csv
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from unidecode import unidecode

from apps.produits.models import Produit, Categorie, Marque

DGCCRF_CODE_PATTERN = re.compile(r"#G(1[5-9]|2[0-1])\b", re.IGNORECASE)
SUBCAT_PATTERN = re.compile(r"\bmt-\d+\b", re.IGNORECASE)


def normalize_text(s: str) -> str:
    if s is None:
        return ''
    s = unidecode(str(s)).lower().strip()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_brand(b: str) -> str:
    s = normalize_text(b)
    s = s.replace('&', 'and')
    return s


def extract_dgccrf_code(row: Dict[str, Any]) -> Optional[str]:
    fields = ['categorie', 'category', 'nom', 'name', 'description', 'titre', 'title']
    for k in fields:
        v = row.get(k)
        if not v:
            continue
        m = DGCCRF_CODE_PATTERN.search(str(v))
        if m:
            return m.group(0).lstrip('#').upper()
    return None


def extract_subcategory(row: Dict[str, Any]) -> Optional[str]:
    fields = ['categorie', 'category', 'nom', 'name', 'description', 'titre', 'title']
    for k in fields:
        v = row.get(k)
        if not v:
            continue
        m = SUBCAT_PATTERN.search(str(v))
        if m:
            return m.group(0).lower()
    return None


def load_rows(path: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
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


def get_or_create_category_for_codes(g_code: str, subcat: Optional[str]) -> Categorie:
    parent, _ = Categorie.objects.get_or_create(
        nom=g_code,
        defaults={
            'slug': g_code.lower(),
            'description': f"Catégorie DGCCRF {g_code}",
        },
    )
    if subcat:
        child, _ = Categorie.objects.get_or_create(
            nom=subcat,
            defaults={
                'slug': subcat,
                'description': f"Sous-catégorie DGCCRF {subcat}",
                'parent': parent,
            },
        )
        if child.parent_id is None:
            child.parent = parent
            child.save(update_fields=['parent'])
        return child
    return parent


def try_match_product(row: Dict[str, Any]) -> Tuple[str, Optional[Produit]]:
    for key in ('ean', 'gtin', 'barcode', 'code_barre', 'codebarre'):
        v = row.get(key)
        if v:
            p = Produit.objects.filter(code_barre__iexact=str(v).strip()).first()
            if p:
                return ('ean', p)
            break
    nom = normalize_text(row.get('nom') or row.get('name') or '')
    brand = normalize_brand(row.get('marque') or row.get('brand') or '')
    if not nom:
        return ('none', None)
    candidats = Produit.objects.select_related('marque').all()[:10000]
    for p in candidats:
        p_nom = normalize_text(p.nom)
        p_brand = normalize_brand(p.marque.nom) if p.marque_id else ''
        if nom == p_nom and (not brand or brand == p_brand):
            return ('exact', p)
    return ('none', None)


class Command(BaseCommand):
    help = "Applique les catégories DGCCRF (#G15..#G21) et sous-catégories (mt-*) aux Produits en base, à partir d’un fichier scrappé."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--file', required=True, help='Chemin du fichier DGCCRF (.json ou .csv)')
        parser.add_argument('--limit', type=int, default=None, help='Limiter le nombre de lignes traitées')
        parser.add_argument('--dry-run', action='store_true', help='Simulation sans écriture DB')

    def handle(self, *args, **options):
        path: str = options['file']
        limit: Optional[int] = options.get('limit')
        dry_run: bool = options.get('dry_run', False)

        rows = load_rows(path, limit)
        total = len(rows)
        updated = 0
        matched = 0
        skipped_no_code = 0
        unmatched = 0

        self.stdout.write(f"Chargé {total} lignes depuis {path}")

        ctx = transaction.atomic() if not dry_run else None
        if ctx:
            ctx.__enter__()
        try:
            for r in rows:
                g_code = extract_dgccrf_code(r)
                subcat = extract_subcategory(r)
                if not g_code and not subcat:
                    skipped_no_code += 1
                    continue

                strat, prod = try_match_product(r)
                if not prod:
                    unmatched += 1
                    continue

                matched += 1
                target_cat: Optional[Categorie] = None
                if g_code:
                    target_cat = get_or_create_category_for_codes(g_code, subcat)
                elif subcat:
                    target_cat, _ = Categorie.objects.get_or_create(
                        nom=subcat,
                        defaults={'slug': subcat, 'description': f'Sous-catégorie DGCCRF {subcat}'},
                    )

                if target_cat and prod.categorie_id != target_cat.id:
                    if not dry_run:
                        prod.categorie = target_cat
                        prod.save(update_fields=['categorie'])
                    updated += 1
        finally:
            if ctx:
                ctx.__exit__(None, None, None)

        self.stdout.write(self.style.SUCCESS(
            f"Terminé. total={total}, matched={matched}, updated={updated}, skipped_no_code={skipped_no_code}, unmatched={unmatched}"
        ))
