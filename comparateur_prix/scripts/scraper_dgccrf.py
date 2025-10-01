#!/usr/bin/env python
import os
import re
import time
import json
import argparse
import logging
from typing import Iterator, Dict, Any, List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

DEFAULT_BASE_URL = os.getenv('DGCCRF_BASE_URL', 'https://www.dgccrf.ga/')
DEFAULT_USER_AGENT = os.getenv('DGCCRF_USER_AGENT', 'ComparateurPrixBot/1.0 (+contact@example.com)')
REQUEST_DELAY_SEC = float(os.getenv('DGCCRF_REQUEST_DELAY', '1.0'))  # throttle between requests
PRIX_HOMOLOGUE_URL = os.getenv('DGCCRF_PRIX_HOMOLOGUE_URL', 'https://www.dgccrf.ga/echo-prix-homologue')
LISTE_PRODUIT_URL = os.getenv('DGCCRF_LISTE_PRODUIT_URL', 'https://www.dgccrf.ga/echo-liste-produit')

logger = logging.getLogger('dgccrf_scraper')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class DgccrfScraper:
    """Scraper basique et respectueux pour récupérer les prix homologués DGCCRF/EDIG.

    Le site/source exacte devra être adaptée: ce scraper prévoit un endpoint JSON/CSV.
    Configurez:
      - DGCCRF_BASE_URL (base URL)
      - DGCCRF_USER_AGENT (User-Agent explicite)
      - DGCCRF_REQUEST_DELAY (throttle en secondes)
    """

    def __init__(self, base_url: Optional[str] = None, user_agent: Optional[str] = None, request_delay: Optional[float] = None):
        self.base_url = base_url or DEFAULT_BASE_URL
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.request_delay = request_delay if request_delay is not None else REQUEST_DELAY_SEC
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/csv, text/plain, */*'
        })

    def _get(self, path: str) -> requests.Response:
        url = urljoin(self.base_url, path)
        logger.info(f"GET {url}")
        resp = self.session.get(url, timeout=30)
        time.sleep(self.request_delay)
        resp.raise_for_status()
        return resp

    def _get_absolute(self, url: str) -> requests.Response:
        logger.info(f"GET {url}")
        resp = self.session.get(url, timeout=30)
        time.sleep(self.request_delay)
        resp.raise_for_status()
        return resp

    @staticmethod
    def _clean_text(t: str) -> str:
        if t is None:
            return ''
        # Remplacer espaces insécables et multiples espaces
        t = t.replace('\xa0', ' ').replace('\u202f', ' ')
        t = re.sub(r"\s+", " ", t)
        return t.strip()

    @staticmethod
    def _parse_price_fcfa(t: str) -> Optional[float]:
        """Extrait un nombre depuis une chaîne du type '2 500 FCFA' ou '2530 FCFA'."""
        if not t:
            return None
        t = t.upper()
        # retirer 'FCFA' et espaces
        t = t.replace('FCFA', '')
        t = t.replace('F CFA', '')
        t = t.replace('F', ' ')
        t = re.sub(r"[^0-9.,]", "", t)
        t = t.replace(',', '.')
        try:
            # garder uniquement les chiffres et le point
            m = re.search(r"\d+(?:\.\d+)?", t)
            if not m:
                return None
            return float(m.group(0))
        except Exception:
            return None

    def iter_homologations(self) -> Iterator[Dict[str, Any]]:
        """Itérer des entrées d'homologation. À adapter selon la source réelle.

        Sortie attendue par item (champs principaux):
          - nom, categorie, sous_categorie, format, marque
          - prix_unitaire, unite (ex: L, kg, g, ml)
          - prix_detail (optionnel), prix_par_kilo (optionnel)
          - date_publication (YYYY-MM-DD), periode_debut (opt), periode_fin (opt)
          - reference_titre, reference_numero, reference_url
        """
        # EXEMPLE: endpoint JSON "homologations.json" sous la base. À ajuster.
        try:
            resp = self._get('homologations.json')
            data = resp.json()
            if isinstance(data, dict):
                records = data.get('records', [])
            else:
                records = data
        except Exception as exc:
            logger.warning(f"JSON non disponible ({exc}), tentative CSV ...")
            resp = self._get('homologations.csv')
            text = resp.text
            records = self._parse_csv(text)

        for row in records:
            try:
                normalized = self._normalize_row(row)
                if normalized:
                    yield normalized
            except Exception as exc:
                logger.error(f"Ligne ignorée (erreur de parsing): {exc}")

    # -------------------
    # Scraping HTML pages
    # -------------------
    def iter_from_prix_homologue_page(self, url: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Scrape la page 'echo-prix-homologue' (ex: manuels scolaires/prix EDIG).

        Heuristique:
        - Extraire tous les blocs de texte principaux.
        - Détecter les occurrences de prix (Libreville / Province) par lignes successives.
        - Associer le nom produit + éditeur si possible.
        """
        target = url or PRIX_HOMOLOGUE_URL
        resp = self._get_absolute(target)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Collecter textes dans le contenu principal
        main = soup
        text_lines: List[str] = []
        for el in main.find_all(text=True):
            t = self._clean_text(str(el))
            if t:
                text_lines.append(t)

        # Heuristique simple: regrouper par blocs où deux prix consécutifs apparaissent
        # On cherche p1 (Libreville) et p2 (Province)
        price_pattern = re.compile(r"\b\d[\d\s.,]*\s*(?:FCFA|F CFA|F)\b", re.IGNORECASE)

        i = 0
        last_header: Optional[str] = None
        while i < len(text_lines):
            line = text_lines[i]
            # mémoriser dernier header (sections PRE-PRIMAIRE, PRIMAIRE, etc.)
            if line.isupper() and len(line) > 3 and len(line) < 40:
                last_header = line
            m1 = price_pattern.search(line)
            if m1 and i + 1 < len(text_lines):
                # Essayer d’identifier la ligne précédente comme nom/éditeur
                name = None
                editor = None
                # Nom probable = la ou les lignes précédentes non vides
                j = i - 1
                context: List[str] = []
                while j >= 0 and len(context) < 3:
                    prev = text_lines[j]
                    if prev and not price_pattern.search(prev):
                        context.append(prev)
                    else:
                        break
                    j -= 1
                context = list(reversed(context))
                if context:
                    name = context[0]
                    if len(context) > 1:
                        editor = context[1]

                p_lib = self._parse_price_fcfa(m1.group(0))
                # Chercher prix province sur les lignes suivantes
                p_prov = None
                k = i + 1
                while k < len(text_lines):
                    m2 = price_pattern.search(text_lines[k])
                    if m2:
                        p_prov = self._parse_price_fcfa(m2.group(0))
                        i = k  # avancer l’index
                        break
                    # Arrêter si on rencontre un autre header ou une coupure
                    if text_lines[k].isupper() and len(text_lines[k]) > 3 and len(text_lines[k]) < 40:
                        break
                    k += 1

                item = {
                    'nom': name or 'Produit (EDIG)',
                    'categorie': last_header or 'Manuels scolaires',
                    'sous_categorie': '',
                    'format': '',
                    'marque': editor or 'EDIG/EDICEF/IPN',
                    'prix_unitaire': p_lib,
                    'unite': 'unité',
                    'prix_detail': None,
                    'prix_par_kilo': None,
                    'date_publication': None,
                    'periode_debut': None,
                    'periode_fin': None,
                    'reference_titre': "Prix homologués EDIG",
                    'reference_numero': '',
                    'reference_url': target,
                    'description': '',
                    'prix_libreville': p_lib,
                    'prix_province': p_prov,
                }
                # Yield si on a au moins un prix
                if p_lib is not None or p_prov is not None:
                    yield item
            i += 1

    def iter_from_liste_produit_page(self, url: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Scrape la page 'echo-liste-produit' (ex: produits défiscalisés).

        Heuristique:
        - Récupère sections et points listés (liens, titres) comme entrées produits.
        - Si la page contient des tableaux, extraire cellules.
        """
        target = url or LISTE_PRODUIT_URL
        resp = self._get_absolute(target)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Tenter d’extraire les tables
        tables = soup.find_all('table')
        if tables:
            def norm_header(h: str) -> str:
                h = self._clean_text(h).lower()
                h = h.replace('é', 'e').replace('è', 'e').replace('ê', 'e').replace('à', 'a').replace('î','i').replace('ï','i')
                h = h.replace(' ', '_')
                return h

            for tbl in tables:
                headers_raw = [self._clean_text(th.get_text()) for th in tbl.find_all('th')]
                headers = [norm_header(h) for h in headers_raw]
                for tr in tbl.find_all('tr'):
                    tds = tr.find_all('td')
                    if not tds:
                        continue
                    cells = [self._clean_text(td.get_text()) for td in tr.find_all(['td', 'th'])]
                    if not cells or (len(cells) == 1 and not cells[0]):
                        continue
                    row = dict(zip(headers, cells)) if headers and len(headers) == len(cells) else {'cols': cells}

                    # Reconnaître les entêtes spécifiques: DESIGNATION, PRIX_GROS, PRIX_DEMI_GROS, PRIX_DETAIL
                    designation = row.get('designation') or row.get('libelle') or row.get('produit') or (cells[1] if len(cells) > 1 else (cells[0] if cells else None))
                    prix_detail_txt = row.get('prix_detail') or row.get('prix_detal') or ''
                    prix_gros_txt = row.get('prix_gros') or ''
                    prix_demi_gros_txt = row.get('prix_demi_gros') or ''

                    prix_detail_val = self._parse_price_fcfa(prix_detail_txt)
                    prix_gros_val = self._parse_price_fcfa(prix_gros_txt)
                    prix_demi_gros_val = self._parse_price_fcfa(prix_demi_gros_txt)

                    item = {
                        'nom': designation or 'Produit',
                        'categorie': 'Produits défiscalisés',
                        'sous_categorie': '',
                        'format': '',
                        'marque': '',
                        # On alimente prix_unitaire avec le prix détail (consommateur)
                        'prix_unitaire': prix_detail_val,
                        'unite': '',  # non spécifié
                        'prix_detail': prix_detail_val,
                        'prix_par_kilo': None,
                        'date_publication': None,
                        'periode_debut': None,
                        'periode_fin': None,
                        'reference_titre': 'Produits défiscalisés',
                        'reference_numero': '',
                        'reference_url': target,
                        'description': ' | '.join(cells),
                    }
                    # Ajouter valeurs de gros/demi-gros dans une clé extra si utile
                    if prix_gros_val is not None or prix_demi_gros_val is not None:
                        item['extra'] = {
                            'prix_gros': prix_gros_val,
                            'prix_demi_gros': prix_demi_gros_val,
                        }
                    # Ne retourner que les lignes avec une désignation
                    if item['nom']:
                        yield item
        else:
            # Pas de tables: fallback texte (liens/listes)
            items = []
            for li in soup.find_all('li'):
                txt = self._clean_text(li.get_text(" "))
                if txt:
                    items.append(txt)
            for p in soup.find_all('p'):
                txt = self._clean_text(p.get_text(" "))
                if txt and len(txt) > 5:
                    items.append(txt)
            for txt in items:
                yield {
                    'nom': txt.split(' ')[0],
                    'categorie': 'Produits défiscalisés',
                    'sous_categorie': '',
                    'format': '',
                    'marque': '',
                    'prix_unitaire': None,
                    'unite': '',
                    'prix_detail': None,
                    'prix_par_kilo': None,
                    'date_publication': None,
                    'periode_debut': None,
                    'periode_fin': None,
                    'reference_titre': 'Produits défiscalisés',
                    'reference_numero': '',
                    'reference_url': target,
                    'description': txt,
                }

    @staticmethod
    def _parse_csv(text: str) -> List[Dict[str, Any]]:
        import csv
        from io import StringIO
        f = StringIO(text)
        reader = csv.DictReader(f)
        return [dict(r) for r in reader]

    @staticmethod
    def _normalize_row(row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Normaliser les champs de sortie.
        Adaptez les clés d'entrée selon le jeu de données réel.
        """
        # Map de clés possibles -> clés normalisées
        map_keys = {
            'nom': ['nom', 'product_name', 'libelle'],
            'categorie': ['categorie', 'category'],
            'sous_categorie': ['sous_categorie', 'subcategory'],
            'format': ['format', 'emballage', 'quantite'],
            'marque': ['marque', 'brand', 'fournisseur'],
            'prix_unitaire': ['prix_unitaire', 'price_unit'],
            'unite': ['unite', 'unit'],
            'prix_detail': ['prix_detail', 'retail_price'],
            'prix_par_kilo': ['prix_par_kilo', 'price_per_kg'],
            'date_publication': ['date_publication', 'publication_date'],
            'periode_debut': ['periode_debut', 'valid_from'],
            'periode_fin': ['periode_fin', 'valid_to'],
            'reference_titre': ['reference_titre', 'legal_title'],
            'reference_numero': ['reference_numero', 'legal_number'],
            'reference_url': ['reference_url', 'legal_url'],
            'description': ['description', 'desc', 'libelle_long'],
        }

        def pick(d: Dict[str, Any], keys: List[str]) -> Any:
            for k in keys:
                if k in d and d[k] not in (None, ''):
                    return d[k]
            return None

        nom = pick(row, map_keys['nom'])
        categorie = pick(row, map_keys['categorie'])
        if not nom:
            return None  # requis

        normalized = {
            'nom': nom,
            'categorie': categorie or 'Non classé',
            'sous_categorie': pick(row, map_keys['sous_categorie']) or '',
            'format': pick(row, map_keys['format']) or '',
            'marque': pick(row, map_keys['marque']) or '',
            'prix_unitaire': pick(row, map_keys['prix_unitaire']),
            'unite': pick(row, map_keys['unite']) or '',
            'prix_detail': pick(row, map_keys['prix_detail']),
            'prix_par_kilo': pick(row, map_keys['prix_par_kilo']),
            'date_publication': pick(row, map_keys['date_publication']),
            'periode_debut': pick(row, map_keys['periode_debut']),
            'periode_fin': pick(row, map_keys['periode_fin']),
            'reference_titre': pick(row, map_keys['reference_titre']) or '',
            'reference_numero': pick(row, map_keys['reference_numero']) or '',
            'reference_url': pick(row, map_keys['reference_url']) or '',
            'description': pick(row, map_keys['description']) or '',
        }
        return normalized


def run_scrape(out: Optional[str] = None, limit: Optional[int] = None, sources: Optional[List[str]] = None) -> int:
    scraper = DgccrfScraper()
    items: List[Dict[str, Any]] = []
    total = 0

    sources = sources or ['auto', 'prix_homologue', 'liste_produit']

    # 1) JSON/CSV si disponible
    if 'auto' in sources:
        try:
            count = 0
            for item in scraper.iter_homologations():
                items.append(item)
                count += 1
                if limit and len(items) >= limit:
                    break
            logger.info(f"[JSON/CSV] {count} éléments")
            total += count
        except Exception as exc:
            logger.warning(f"Source JSON/CSV non disponible: {exc}")

    def maybe_stop() -> bool:
        return bool(limit and len(items) >= limit)

    # 2) Page prix homologués (HTML)
    if 'prix_homologue' in sources and not maybe_stop():
        count = 0
        for item in scraper.iter_from_prix_homologue_page():
            items.append(item)
            count += 1
            if maybe_stop():
                break
        logger.info(f"[PRIX_HOMOLOGUE] {count} éléments")
        total += count

    # 3) Page liste de produits (HTML)
    if 'liste_produit' in sources and not maybe_stop():
        count = 0
        for item in scraper.iter_from_liste_produit_page():
            items.append(item)
            count += 1
            if maybe_stop():
                break
        logger.info(f"[LISTE_PRODUIT] {count} éléments")
        total += count

    logger.info(f"Traitement terminé, total {total} éléments.")

    if out:
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(items, f, ensure_ascii=False, indent=2)
        logger.info(f"Export écrit: {out} ({len(items)} items)")
    else:
        # Affiche un aperçu si pas d'output demandé
        for i, it in enumerate(items[:5]):
            logger.info(f"APERÇU[{i}]: {it}")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Scraper DGCCRF (JSON/CSV/HTML)')
    p.add_argument('--out', help='Chemin de sortie JSON (ex: data/dgccrf_export.json)')
    p.add_argument('--limit', type=int, default=None, help='Limiter le nombre total d\'items collectés')
    p.add_argument('--sources', default='auto,prix_homologue,liste_produit', help='Sources à activer, séparées par des virgules')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    srcs = [s.strip() for s in (args.sources or '').split(',') if s.strip()]
    raise SystemExit(run_scrape(out=args.out, limit=args.limit, sources=srcs))
