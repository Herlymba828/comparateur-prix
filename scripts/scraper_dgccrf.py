#!/usr/bin/env python
import os
import re
import time
import json
import argparse
import logging
import hashlib
import pathlib
from typing import Iterator, Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser
from datetime import datetime, timezone

DEFAULT_BASE_URL = os.getenv('DGCCRF_BASE_URL', 'https://www.dgccrf.ga/')
DEFAULT_USER_AGENT = os.getenv('DGCCRF_USER_AGENT', 'ComparateurPrixBot/1.0 (+contact@example.com)')
REQUEST_DELAY_SEC = float(os.getenv('DGCCRF_REQUEST_DELAY', '1.0'))  # throttle between requests
REQUEST_TIMEOUT = float(os.getenv('DGCCRF_TIMEOUT', '30'))
MAX_RETRIES = int(os.getenv('DGCCRF_MAX_RETRIES', '3'))
BACKOFF_SEC = float(os.getenv('DGCCRF_BACKOFF', '1.5'))
HTTP_PROXY = os.getenv('DGCCRF_PROXY', '')
LOG_FILE = os.getenv('DGCCRF_LOG_FILE', '')
STATE_FILE = os.getenv('DGCCRF_STATE_FILE', '.dgccrf_state.json')
CHECKPOINT_PATH = os.getenv('DGCCRF_CHECKPOINT_PATH', '.dgccrf_checkpoint.json')
SAVE_TO_DB = os.getenv('DGCCRF_SAVE_TO_DB', 'false').lower() == 'true'
PRIX_HOMOLOGUE_URL = os.getenv('DGCCRF_PRIX_HOMOLOGUE_URL', 'https://www.dgccrf.ga/echo-prix-homologue')
LISTE_PRODUIT_URL = os.getenv('DGCCRF_LISTE_PRODUIT_URL', 'https://www.dgccrf.ga/echo-liste-produit')
PRODUIT_PETROLIER_URL = os.getenv('DGCCRF_PRODUIT_PETROLIER_URL', 'https://www.dgccrf.ga/echo-produit-petrolier')
RESPECT_ROBOTS = os.getenv('DGCCRF_RESPECT_ROBOTS', 'true').lower() == 'true'
RAW_DIR = os.getenv('DGCCRF_RAW_DIR', '')
DEFAULT_REPORT_OUT = os.getenv('DGCCRF_REPORT_OUT', 'data/dgccrf_report.json')
SKIP_UNCHANGED = os.getenv('DGCCRF_SKIP_UNCHANGED', 'false').lower() == 'true'
OFF_ENABLE = os.getenv('DGCCRF_OFF_ENABLE', 'false').lower() == 'true'
OFF_TIMEOUT = float(os.getenv('DGCCRF_OFF_TIMEOUT', '5'))
OFF_MIN_SCORE = float(os.getenv('DGCCRF_OFF_MIN_SCORE', '0.6'))

logger = logging.getLogger('dgccrf_scraper')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    if LOG_FILE:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


class DgccrfScraper:
    """Scraper basique et respectueux pour récupérer les prix homologués DGCCRF/EDIG.

    Le site/source exacte devra être adaptée: ce scraper prévoit un endpoint JSON/CSV.
    Configurez:
      - DGCCRF_BASE_URL (base URL)
      - DGCCRF_USER_AGENT (User-Agent explicite)
      - DGCCRF_REQUEST_DELAY (throttle en secondes)
    """

    def __init__(self, base_url: Optional[str] = None, user_agent: Optional[str] = None, request_delay: Optional[float] = None, timeout: Optional[float] = None):
        self.base_url = base_url or DEFAULT_BASE_URL
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self.request_delay = request_delay if request_delay is not None else REQUEST_DELAY_SEC
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/csv, text/plain, */*'
        })
        if HTTP_PROXY:
            self.session.proxies.update({
                'http': HTTP_PROXY,
                'https': HTTP_PROXY,
            })
        self.timeout = timeout if timeout is not None else REQUEST_TIMEOUT

    def _get(self, path: str) -> requests.Response:
        url = urljoin(self.base_url, path)
        return self._request_with_retry(url)

    def _get_absolute(self, url: str) -> requests.Response:
        return self._request_with_retry(url)

    def _request_with_retry(self, url: str) -> requests.Response:
        attempt = 0
        last_exc: Optional[Exception] = None
        while attempt < MAX_RETRIES:
            try:
                logger.info(f"GET {url} (try {attempt+1}/{MAX_RETRIES})")
                resp = self.session.get(url, timeout=self.timeout)
                time.sleep(self.request_delay)
                resp.raise_for_status()
                # Sauvegarder brut pour audit si demandé
                if RAW_DIR:
                    try:
                        os.makedirs(RAW_DIR, exist_ok=True)
                        safe = hashlib.sha1(url.encode('utf-8')).hexdigest()
                        ts = int(time.time())
                        p = pathlib.Path(RAW_DIR) / f"{ts}_{safe}.html"
                        p.write_text(resp.text, encoding='utf-8')
                    except Exception:
                        pass
                return resp
            except RequestException as exc:
                last_exc = exc
                sleep_for = BACKOFF_SEC * (2 ** attempt)
                logger.warning(f"Erreur requête: {exc}. Backoff {sleep_for:.1f}s")
                time.sleep(sleep_for)
                attempt += 1
        raise last_exc or RuntimeError("Échec de requête après retries")

    def _is_allowed_by_robots(self, url: str) -> bool:
        if not RESPECT_ROBOTS:
            return True
        try:
            rp = robotparser.RobotFileParser()
            rp.set_url(urljoin(self.base_url, '/robots.txt'))
            rp.read()
            return rp.can_fetch(self.user_agent, url)
        except Exception:
            return True

    @staticmethod
    def _clean_text(t: str) -> str:
        if t is None:
            return ''
        # Remplacer espaces insécables et multiples espaces
        t = t.replace('\xa0', ' ').replace('\u202f', ' ')
        t = re.sub(r"\s+", " ", t)
        return t.strip()

    @staticmethod
    def _hash_content(text: str) -> str:
        return hashlib.sha256(text.encode('utf-8', errors='ignore')).hexdigest()

    @staticmethod
    def _hash_item(d: Dict[str, Any]) -> str:
        # Hash stable basé sur principaux champs
        keys = ['nom','categorie','sous_categorie','format','marque','prix_unitaire','unite','prix_detail','prix_par_kilo','zone','type_prix']
        payload = '|'.join(str(d.get(k, '')) for k in keys)
        return hashlib.sha1(payload.encode('utf-8', errors='ignore')).hexdigest()

    def _load_state(self) -> Dict[str, Any]:
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_state(self, state: Dict[str, Any]) -> None:
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(f"Impossible d'enregistrer l'état: {exc}")

    def _load_checkpoint(self) -> Dict[str, Any]:
        try:
            with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_checkpoint(self, ckpt: Dict[str, Any]) -> None:
        try:
            with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
                json.dump(ckpt, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.warning(f"Impossible d'enregistrer le checkpoint: {exc}")

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

    @staticmethod
    def extract_origin_and_clean_name(name: str) -> Dict[str, Optional[str]]:
        if not name:
            return {'nom': name, 'origine': None}
        m = re.search(r"\(([^)]+)\)\s*$", name)
        if m:
            origine = m.group(1).strip()
            nom = name[:m.start()].strip()
            return {'nom': nom, 'origine': origine}
        return {'nom': name.strip(), 'origine': None}

    @staticmethod
    def parse_conditionnement(text: str) -> Dict[str, Any]:
        """Détecte formats du type '125g x 50', '6 x 1L', '3x500 ml'."""
        if not text:
            return {}
        t = text.lower().replace('×', 'x')
        m = re.search(r"(\d+)\s*x\s*(\d+(?:[\.,]\d+)?)\s*(kg|g|mg|l|cl|ml|unite|pi[eè]ce)s?", t)
        if m:
            n = int(m.group(1))
            qty = float(m.group(2).replace(',', '.'))
            unit = m.group(3)
            total = qty * n
            return {'nombre_unites': n, 'quantite_unite': qty, 'unite': unit, 'quantite_totale': total}
        # Single unit style
        m2 = re.search(r"(\d+(?:[\.,]\d+)?)\s*(kg|g|mg|l|cl|ml)", t)
        if m2:
            qty = float(m2.group(1).replace(',', '.'))
            unit = m2.group(2)
            return {'nombre_unites': 1, 'quantite_unite': qty, 'unite': unit, 'quantite_totale': qty}
        return {}

    @staticmethod
    def _detect_unit(text: str) -> str:
        if not text:
            return ''
        t = text.lower()
        # Ordre important pour éviter collisions (ex: 'kg' avant 'g')
        if re.search(r"\bkg\b", t):
            return 'kg'
        if re.search(r"\bg\b", t):
            return 'g'
        if re.search(r"\blitre?s?\b|\bl\b", t):
            return 'L'
        if re.search(r"\bcl\b|centilitre?s?\b", t):
            return 'cl'
        if re.search(r"\bml\b", t):
            return 'ml'
        if re.search(r"\bmg\b|milligramme?s?\b", t):
            return 'mg'
        if re.search(r"\bunite\b|\bpi[eè]ce\b", t):
            return 'unite'
        return ''

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
        if not self._is_allowed_by_robots(target):
            logger.warning(f"Bloqué par robots.txt: {target}")
            return iter(())
        resp = self._get_absolute(target)
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Détection de changement (hash + entêtes)
        state = self._load_state()
        key = f"hash::{target}"
        new_hash = self._hash_content(resp.text)
        if state.get(key) == new_hash:
            logger.info("Aucun changement détecté sur la page prix homologués, on peut skipper si souhaité.")
        state[key] = new_hash
        state[f"etag::{target}"] = resp.headers.get('ETag')
        state[f"lm::{target}"] = resp.headers.get('Last-Modified')
        self._save_state(state)

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
                    'zone': 'Libreville' if p_lib is not None else ('Province' if p_prov is not None else ''),
                    'devise': 'FCFA',
                    'type_prix': 'detail',
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
                # Mapping étendu
                header_map = {
                    'designation': ['designation','libelle','produit','desi','designations'],
                    'prix_detail': ['prix_detail','prix_detal','detail','prix_au_detail'],
                    'prix_gros': ['prix_gros','gros'],
                    'prix_demi_gros': ['prix_demi_gros','demi_gros','prix_demi'],
                }
                # Remappe headers connus
                remapped = {}
                for idx, h in enumerate(headers):
                    key = h
                    for target, aliases in header_map.items():
                        if h in aliases:
                            key = target
                            break
                    remapped[idx] = key
                for tr in tbl.find_all('tr'):
                    tds = tr.find_all('td')
                    if not tds:
                        continue
                    cells = [self._clean_text(td.get_text()) for td in tr.find_all(['td', 'th'])]
                    if not cells or (len(cells) == 1 and not cells[0]):
                        continue
                    if headers and len(headers) == len(cells):
                        raw = dict(zip(range(len(headers)), cells))
                        row = {remapped[i]: v for i, v in raw.items()}
                    else:
                        row = {'cols': cells}

                    # Reconnaître les entêtes spécifiques: DESIGNATION, PRIX_GROS, PRIX_DEMI_GROS, PRIX_DETAIL
                    designation = row.get('designation') or row.get('libelle') or row.get('produit') or (cells[1] if len(cells) > 1 else (cells[0] if cells else None))
                    origin_info = self.extract_origin_and_clean_name(designation or '')
                    designation_clean = origin_info['nom'] or designation
                    prix_detail_txt = row.get('prix_detail') or row.get('prix_detal') or ''
                    prix_gros_txt = row.get('prix_gros') or ''
                    prix_demi_gros_txt = row.get('prix_demi_gros') or ''

                    prix_detail_val = self._parse_price_fcfa(prix_detail_txt)
                    prix_gros_val = self._parse_price_fcfa(prix_gros_txt)
                    prix_demi_gros_val = self._parse_price_fcfa(prix_demi_gros_txt)

                    # Fallbacks prix si prix_detail absent
                    prix_val = prix_detail_val
                    type_prix = 'detail'
                    if prix_val is None and prix_gros_val is not None:
                        prix_val = prix_gros_val
                        type_prix = 'gros'
                    if prix_val is None and prix_demi_gros_val is not None:
                        prix_val = prix_demi_gros_val
                        type_prix = 'demi_gros'

                    unit_detected = self._detect_unit(' '.join([designation_clean or '', ' '.join(cells)]))
                    cond = self.parse_conditionnement(' '.join(cells))
                    item = {
                        'nom': designation_clean or 'Produit',
                        'categorie': 'Produits défiscalisés',
                        'sous_categorie': '',
                        'format': cond.get('quantite_totale') and f"{cond.get('quantite_totale')}{cond.get('unite')}" or '',
                        'marque': '',
                        # On alimente prix_unitaire avec fallback si besoin
                        'prix_unitaire': prix_val,
                        'unite': unit_detected,
                        'prix_detail': prix_detail_val,
                        'prix_par_kilo': None,
                        'date_publication': None,
                        'periode_debut': None,
                        'periode_fin': None,
                        'reference_titre': 'Produits défiscalisés',
                        'reference_numero': '',
                        'reference_url': target,
                        'description': ' | '.join(cells),
                        'zone': '',
                        'devise': 'FCFA',
                        'type_prix': type_prix,
                    }
                    # Ajouter valeurs de gros/demi-gros dans une clé extra si utile
                    if prix_gros_val is not None or prix_demi_gros_val is not None:
                        item['extra'] = {
                            'prix_gros': prix_gros_val,
                            'prix_demi_gros': prix_demi_gros_val,
                            'origine': origin_info['origine'],
                            'conditionnement': cond,
                        }
                    # Open Food Facts (optionnel)
                    if OFF_ENABLE and designation_clean and len(designation_clean.split()) >= 2:
                        code = self._maybe_fetch_off_barcode(designation_clean)
                        if code:
                            item['code_barres'] = code
                    # Ne retourner que les lignes avec une désignation
                    if item['nom']:
                        # Item-level diff
                        if SKIP_UNCHANGED:
                            it_hash = self._hash_item(item)
                            seen = state.get(f"seen::{target}", [])
                            if it_hash in seen:
                                continue
                            seen.append(it_hash)
                            state[f"seen::{target}"] = seen
                            self._save_state(state)
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
                unit_detected = self._detect_unit(txt)
                yield {
                    'nom': txt.split(' ')[0],
                    'categorie': 'Produits défiscalisés',
                    'sous_categorie': '',
                    'format': '',
                    'marque': '',
                    'prix_unitaire': None,
                    'unite': unit_detected,
                    'prix_detail': None,
                    'prix_par_kilo': None,
                    'date_publication': None,
                    'periode_debut': None,
                    'periode_fin': None,
                    'reference_titre': 'Produits défiscalisés',
                    'reference_numero': '',
                    'reference_url': target,
                    'description': txt,
                    'zone': '',
                    'devise': 'FCFA',
                    'type_prix': 'detail',
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
            'zone': row.get('zone', ''),
            'devise': row.get('devise', 'FCFA'),
            'type_prix': row.get('type_prix', 'detail'),
        }
        return normalized

    # -------------------
    # Détection de type de page et extraction adaptative
    # -------------------
    def detect_page_type(self, url: str, text: str) -> str:
        t = text.lower()
        if url.endswith('.json') or t.strip().startswith('{') or '"records"' in t:
            return 'json'
        if url.endswith('.csv') or ',' in t.splitlines()[0:1][0] if t.splitlines() else False:
            return 'csv'
        if 'prix-homologue' in url or 'echo-prix-homologue' in url:
            return 'prix_homologue'
        if 'liste-produit' in url or 'echo-liste-produit' in url:
            return 'liste_produit'
        if 'produit-petrolier' in url or 'echo-produit-petrolier' in url:
            return 'produit_petrolier'
        # fallback HTML
        return 'html'

    def iter_auto(self, url: str) -> Iterator[Dict[str, Any]]:
        resp = self._get_absolute(url)
        kind = self.detect_page_type(url, resp.text)
        logger.info(f"Type détecté: {kind}")
        if kind == 'json':
            try:
                data = resp.json()
                rows = data.get('records', []) if isinstance(data, dict) else data
            except Exception:
                rows = []
            for r in rows:
                n = self._normalize_row(r)
                if n:
                    yield n
            return
        if kind == 'csv':
            rows = self._parse_csv(resp.text)
            for r in rows:
                n = self._normalize_row(r)
                if n:
                    yield n
            return
        if kind == 'prix_homologue':
            yield from self.iter_from_prix_homologue_page(url)
            return
        if kind == 'liste_produit':
            yield from self.iter_from_liste_produit_page(url)
            return
        if kind == 'produit_petrolier':
            yield from self.iter_from_produit_petrolier_page(url)
            return
        # fallback: extraire comme liste_produit
        yield from self.iter_from_liste_produit_page(url)

    def iter_from_produit_petrolier_page(self, url: Optional[str] = None) -> Iterator[Dict[str, Any]]:
        """Scrape la page des produits pétroliers (prix carburants).
        Heuristique tables: colonnes peuvent contenir libellé, volume, prix (Libreville/Province) ou prix unique.
        """
        target = url or PRODUIT_PETROLIER_URL
        if not self._is_allowed_by_robots(target):
            logger.warning(f"Bloqué par robots.txt: {target}")
            return iter(())
        resp = self._get_absolute(target)
        soup = BeautifulSoup(resp.text, 'html.parser')
        state = self._load_state()
        key = f"hash::{target}"
        new_hash = self._hash_content(resp.text)
        if state.get(key) == new_hash:
            logger.info("Aucun changement détecté sur la page produits pétroliers.")
        state[key] = new_hash
        state[f"etag::{target}"] = resp.headers.get('ETag')
        state[f"lm::{target}"] = resp.headers.get('Last-Modified')
        self._save_state(state)

        tables = soup.find_all('table')
        for tbl in tables:
            headers = [self._clean_text(th.get_text()).lower() for th in tbl.find_all('th')]
            for tr in tbl.find_all('tr'):
                cells = [self._clean_text(td.get_text()) for td in tr.find_all(['td','th'])]
                if not cells or (len(cells) == 1 and not cells[0]):
                    continue
                row = dict(zip(headers, cells)) if headers and len(headers) == len(cells) else {'cols': cells}

                # Heuristiques de colonnes
                designation = row.get('designation') or row.get('produit') or row.get('libelle') or (cells[0] if cells else '')
                volume = row.get('volume') or ''
                matiere = row.get('matiere') or ''
                type_carburant = row.get('type') or ''
                prix_lb_txt = row.get('libreville') or ''
                prix_prov_txt = row.get('province') or ''
                prix_txt = row.get('prix') or ''

                prix_lb = self._parse_price_fcfa(prix_lb_txt)
                prix_prov = self._parse_price_fcfa(prix_prov_txt)
                prix_unique = self._parse_price_fcfa(prix_txt)

                unit_detected = self._detect_unit(' '.join(cells + [volume or '', designation or '']))
                base = {
                    'nom': designation or 'Carburant',
                    'categorie': 'Produits pétroliers',
                    'sous_categorie': type_carburant or '',
                    'format': volume or '',
                    'marque': '',
                    'prix_unitaire': prix_unique,
                    'unite': unit_detected,
                    'prix_detail': prix_unique,
                    'prix_par_kilo': None,
                    'date_publication': None,
                    'periode_debut': None,
                    'periode_fin': None,
                    'reference_titre': 'Produits pétroliers',
                    'reference_numero': '',
                    'reference_url': target,
                    'description': ' | '.join(cells),
                    'zone': '',
                    'devise': 'FCFA',
                    'type_prix': 'homologué',
                }
                # Générer items séparés pour LB/Province si disponibles
                if prix_lb is not None:
                    it = dict(base)
                    it['prix_unitaire'] = prix_lb
                    it['prix_detail'] = prix_lb
                    it['zone'] = 'Libreville'
                    yield it
                if prix_prov is not None:
                    it = dict(base)
                    it['prix_unitaire'] = prix_prov
                    it['prix_detail'] = prix_prov
                    it['zone'] = 'Province'
                    yield it
                if prix_lb is None and prix_prov is None and (prix_unique is not None):
                    yield base

    # --------- Open Food Facts Lookup ---------
    def _maybe_fetch_off_barcode(self, query: str) -> Optional[str]:
        try:
            params = {
                'search_terms': query,
                'search_simple': 1,
                'action': 'process',
                'json': 1,
                'page_size': 1,
            }
            r = requests.get('https://world.openfoodfacts.org/cgi/search.pl', params=params, timeout=OFF_TIMEOUT, headers={'User-Agent': self.user_agent})
            r.raise_for_status()
            data = r.json()
            prods = data.get('products') or []
            if not prods:
                return None
            p = prods[0]
            # Score simplifié: présence code + nom
            code = p.get('code') or p.get('_id')
            pname = p.get('product_name') or ''
            score = 1.0 if code and pname else 0.0
            return code if score >= OFF_MIN_SCORE else None
        except Exception:
            return None

    # --------- Unification de sortie ---------
    def build_unified(self, it: Dict[str, Any]) -> Dict[str, Any]:
        now_iso = datetime.now(timezone.utc).isoformat()
        prix_entries = []
        if it.get('prix_unitaire') is not None:
            prix_entries.append({
                'zone': it.get('zone') or '',
                'valeur': it.get('prix_unitaire'),
                'devise': it.get('devise', 'FCFA'),
                'date_maj': it.get('date_publication') or it.get('periode_fin') or now_iso[:10],
                'type_prix': it.get('type_prix', 'detail'),
            })
        return {
            'source': 'DGCCRF Gabon',
            'categorie': it.get('categorie') or 'Non classé',
            'sous_categorie': it.get('sous_categorie') or '',
            'produit': it.get('nom') or '',
            'marque_editeur': it.get('marque') or '',
            'prix': prix_entries,
            'caracteristiques': {
                'volume': it.get('format') or '',
            },
            'metadata': {
                'url_source': it.get('reference_url') or '',
                'date_extraction': now_iso,
                'statut': 'actif',
                'confiance': 0.9,
            }
        }

    # -------------------
    # Persistance ORM optionnelle
    # -------------------
    def _init_django(self) -> bool:
        try:
            # S'assurer que la racine du projet est sur sys.path (scripts/ est un sous-dossier)
            import sys
            import pathlib as _pl
            project_root = _pl.Path(__file__).resolve().parents[1]
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            import django  # noqa
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
            django.setup()
            return True
        except Exception as exc:
            logger.error(f"Impossible d'initialiser Django: {exc}")
            return False

    def persist_items(self, items: List[Dict[str, Any]]) -> Tuple[int, int]:
        try:
            from apps.produits.models import Produit, Prix, Categorie, UniteMesure, Marque, HomologationProduit, PrixHomologue
            from apps.magasins.models import Magasin, Ville, Region
            from django.utils.text import slugify
            from decimal import Decimal
        except Exception as exc:
            logger.error(f"Dépendances Django indisponibles: {exc}")
            return (0, 0)

        created_prod = 0
        created_prix = 0

        # Valeurs par défaut pour rattachement magasin
        region, _ = Region.objects.get_or_create(nom='Estuaire')
        ville, _ = Ville.objects.get_or_create(nom='Libreville', region=region)

        for it in items:
            nom = (it.get('nom') or '').strip()
            if not nom:
                continue
            cat_nom = (it.get('categorie') or 'Non classé').strip() or 'Non classé'
            cat_slug = slugify(cat_nom)[:100] or 'non-classe'
            categorie, _ = Categorie.objects.get_or_create(slug=cat_slug, defaults={'nom': cat_nom})
            # Sous-catégorie hiérarchique (optionnelle)
            sous_cat_nom = (it.get('sous_categorie') or '').strip()
            sous_cat_obj = None
            if sous_cat_nom:
                sous_slug = slugify(sous_cat_nom)[:100] or None
                if sous_slug:
                    try:
                        sous_cat_obj, _ = Categorie.objects.get_or_create(
                            slug=sous_slug,
                            defaults={'nom': sous_cat_nom, 'parent': categorie}
                        )
                        # Si la sous-catégorie existe déjà mais sans parent, essayer de définir le parent si absent
                        if getattr(sous_cat_obj, 'parent_id', None) in (None, 0) and sous_cat_obj.parent_id != categorie.id:
                            sous_cat_obj.parent = categorie
                            try:
                                sous_cat_obj.save(update_fields=['parent'])
                            except Exception:
                                pass
                    except Exception:
                        sous_cat_obj = None

            code_barre = (it.get('code_barres') or it.get('code_barre') or '').strip() or None
            unit_txt = (it.get('unite') or '').strip().lower()
            # Normalisation étendue des unités
            if unit_txt in ('unité', 'unite', 'piece', 'pièce', 'pieces', 'pièces', 'pc', 'pcs', 'u'):
                symbol = 'u'
            elif unit_txt in ('l', 'lt', 'litre', 'litres', 'liter', 'liters'):
                symbol = 'L'
            elif unit_txt in ('cl', 'centilitre', 'centilitres'):
                symbol = 'cl'
            elif unit_txt in ('ml', 'millilitre', 'millilitres'):
                symbol = 'ml'
            elif unit_txt in ('kg', 'kilogramme', 'kilogrammes'):
                symbol = 'kg'
            elif unit_txt in ('g', 'gramme', 'grammes'):
                symbol = 'g'
            elif unit_txt in ('mg', 'milligramme', 'milligrammes'):
                symbol = 'mg'
            else:
                symbol = 'u'

            um_names = {
                'u': 'Unité',
                'kg': 'Kilogramme',
                'g': 'Gramme',
                'mg': 'Milligramme',
                'L': 'Litre',
                'cl': 'Centilitre',
                'ml': 'Millilitre',
            }
            unite_mesure, _ = UniteMesure.objects.get_or_create(symbole=symbol, defaults={'nom': um_names.get(symbol, 'Unité')})

            cond = (it.get('extra') or {}).get('conditionnement') or {}
            q_unit = cond.get('quantite_unite')
            q_total = cond.get('quantite_totale')
            try:
                quantite_unite = Decimal(str(q_unit)) if q_unit is not None else Decimal('1')
            except Exception:
                quantite_unite = Decimal('1')

            poids = None
            volume = None
            try:
                if symbol in ('kg', 'g', 'mg'):
                    base = Decimal(str(q_total if q_total is not None else q_unit if q_unit is not None else '0'))
                    if base > 0:
                        if symbol == 'g':
                            poids = base / Decimal('1000')
                        elif symbol == 'mg':
                            poids = base / Decimal('1000000')
                        else:
                            poids = base
                elif symbol in ('L', 'ml', 'cl'):
                    base = Decimal(str(q_total if q_total is not None else q_unit if q_unit is not None else '0'))
                    if base > 0:
                        if symbol == 'ml':
                            volume = base / Decimal('1000')
                        elif symbol == 'cl':
                            volume = base / Decimal('100')
                        else:
                            volume = base
            except Exception:
                pass

            # Utiliser la sous-catégorie si disponible pour affecter la catégorie produit
            categorie_produit = sous_cat_obj or categorie

            prod_slug = slugify(nom)[:200]
            # code_barre max_length=20: générer un identifiant court et stable si absent
            safe_cb = code_barre
            if not safe_cb:
                try:
                    h = hashlib.sha1(prod_slug.encode('utf-8')).hexdigest()[:12]
                    safe_cb = f"AUTO-{h}"  # 17 caractères
                except Exception:
                    safe_cb = "AUTO-000000000000"
            produit, created = Produit.objects.get_or_create(
                slug=prod_slug,
                defaults={
                    'nom': nom,
                    'code_barre': safe_cb,
                    'categorie': categorie_produit,
                    'description': it.get('description', ''),
                    'unite_mesure': unite_mesure,
                    'quantite_unite': quantite_unite,
                    **({'poids': poids} if poids is not None else {}),
                    **({'volume': volume} if volume is not None else {}),
                }
            )
            if created:
                created_prod += 1
            else:
                updates = {}
                # Mettre à jour la catégorie si le produit était rattaché à une catégorie générique
                if getattr(produit, 'categorie_id', None) and categorie_produit and produit.categorie_id != categorie_produit.id:
                    updates['categorie'] = categorie_produit
                if not getattr(produit, 'unite_mesure_id', None):
                    updates['unite_mesure'] = unite_mesure
                if not getattr(produit, 'quantite_unite', None):
                    updates['quantite_unite'] = quantite_unite
                if poids is not None and getattr(produit, 'poids', None) in (None, 0):
                    updates['poids'] = poids
                if volume is not None and getattr(produit, 'volume', None) in (None, 0):
                    updates['volume'] = volume
                if updates:
                    for k, v in updates.items():
                        setattr(produit, k, v)
                    try:
                        produit.save(update_fields=list(updates.keys()))
                    except Exception:
                        pass

            marque_nom = (it.get('marque') or '').strip()
            # Fallback: utiliser l'origine détectée si marque vide
            if not marque_nom:
                origine = (it.get('extra') or {}).get('origine')
                if origine:
                    marque_nom = str(origine).strip()
            if marque_nom:
                marque_slug = slugify(marque_nom)[:100]
                marque, _ = Marque.objects.get_or_create(slug=marque_slug, defaults={'nom': marque_nom})
                if getattr(produit, 'marque_id', None) is None:
                    try:
                        produit.marque = marque
                        produit.save(update_fields=['marque'])
                    except Exception:
                        pass

            # Référentiels Prix Homologués (si champs présents)
            ref_titre = (it.get('reference_titre') or '').strip()
            ref_num = (it.get('reference_numero') or '').strip()
            ref_url = (it.get('reference_url') or '').strip()
            # On crée un HomologationProduit quand l'item provient du flux "prix homologués" ou contient des métadonnées de référence
            if ref_titre or 'prix_homolog' in (ref_titre or '').lower() or it.get('prix_libreville') is not None or it.get('prix_province') is not None:
                hp_defaults = {
                    'format': (it.get('format') or '').strip(),
                    'marque': (it.get('marque') or '').strip(),
                    'categorie': cat_nom,
                    'sous_categorie': (it.get('sous_categorie') or '').strip(),
                    **({'sous_categorie_fk': sous_cat_obj} if sous_cat_obj else {}),
                    'reference_titre': ref_titre,
                    'reference_numero': ref_num,
                    'reference_url': ref_url,
                }
                # Chercher un enregistrement proche pour éviter les doublons évidents
                hp, created_hp = HomologationProduit.objects.get_or_create(
                    nom=nom,
                    marque=hp_defaults['marque'],
                    format=hp_defaults['format'],
                    defaults=hp_defaults,
                )
                if not created_hp and sous_cat_obj and getattr(hp, 'sous_categorie_fk_id', None) is None:
                    try:
                        hp.sous_categorie_fk = sous_cat_obj
                        hp.save(update_fields=['sous_categorie_fk'])
                    except Exception:
                        pass
                # Créer des entrées PrixHomologue par zone si disponibles
                unite_hp = unit_txt or symbol or ''
                try:
                    # Libreville
                    if it.get('prix_libreville') is not None:
                        PrixHomologue.objects.create(
                            produit=hp,
                            date_publication=None,
                            unite=unite_hp,
                            prix_unitaire=it.get('prix_libreville'),
                            prix_detail=it.get('prix_detail') if it.get('prix_detail') is not None else None,
                            prix_par_kilo=it.get('prix_par_kilo') if it.get('prix_par_kilo') is not None else None,
                            prix_gros=(it.get('extra') or {}).get('prix_gros'),
                            prix_demi_gros=(it.get('extra') or {}).get('prix_demi_gros'),
                            localisation='Libreville',
                            source='DGCCRF',
                        )
                    # Province
                    if it.get('prix_province') is not None:
                        PrixHomologue.objects.create(
                            produit=hp,
                            date_publication=None,
                            unite=unite_hp,
                            prix_unitaire=it.get('prix_province'),
                            prix_detail=it.get('prix_detail') if it.get('prix_detail') is not None else None,
                            prix_par_kilo=it.get('prix_par_kilo') if it.get('prix_par_kilo') is not None else None,
                            prix_gros=(it.get('extra') or {}).get('prix_gros'),
                            prix_demi_gros=(it.get('extra') or {}).get('prix_demi_gros'),
                            localisation='Province',
                            source='DGCCRF',
                        )
                    # Fallback: si pas de LB/Province dédiés mais une zone générique et un prix
                    if it.get('prix_libreville') is None and it.get('prix_province') is None:
                        val = it.get('prix_unitaire') or it.get('prix_detail')
                        if val is not None:
                            PrixHomologue.objects.create(
                                produit=hp,
                                date_publication=None,
                                unite=unite_hp,
                                prix_unitaire=val,
                                prix_detail=it.get('prix_detail') if it.get('prix_detail') is not None else None,
                                prix_par_kilo=it.get('prix_par_kilo') if it.get('prix_par_kilo') is not None else None,
                                prix_gros=(it.get('extra') or {}).get('prix_gros'),
                                prix_demi_gros=(it.get('extra') or {}).get('prix_demi_gros'),
                                localisation=(it.get('zone') or '').strip(),
                                source='DGCCRF',
                            )
                except Exception:
                    # On ignore silencieusement une erreur sur référentiel pour ne pas bloquer l'import principal
                    pass

            # Magasin synthétique basé sur zone
            zone = (it.get('zone') or '').strip() or 'N/A'
            mag_nom = f"DGCCRF {zone}".strip()
            mag_slug = slugify(mag_nom)[:220]
            magasin, _ = Magasin.objects.get_or_create(
                slug=mag_slug,
                defaults={
                    'nom': mag_nom,
                    'type': 'en_ligne',
                    'type_magasin': 'en_ligne',
                    'ville': ville,
                    'localisation': zone,
                    'zone': zone,
                    # Adresse synthétique pour améliorer le géocodage
                    'adresse': f"{zone}, {ville.nom}, {region.nom}, Gabon",
                }
            )

            # Créer/mettre à jour prix
            valeur = it.get('prix_unitaire') or it.get('prix_detail')
            if valeur is not None:
                p, created_price = Prix.objects.update_or_create(
                    produit=produit,
                    magasin=magasin,
                    defaults={
                        'prix_actuel': valeur,
                        'devise': it.get('devise', 'FCFA'),
                        'type_prix': it.get('type_prix', 'detail'),
                        'zone': zone,
                        'source_prix': 'dgccrf',
                        'est_disponible': True,
                    }
                )
                if created_price:
                    created_prix += 1

        return (created_prod, created_prix)


def run_scrape(out: Optional[str] = None, limit: Optional[int] = None, sources: Optional[List[str]] = None, save: bool = SAVE_TO_DB, checkpoint: Optional[str] = None, auto_urls: Optional[List[str]] = None, unified: bool = False, csv_out: Optional[str] = None, sql_out: Optional[str] = None, report_out: Optional[str] = None, only_changed: Optional[bool] = None) -> int:
    scraper = DgccrfScraper()
    items: List[Dict[str, Any]] = []
    total = 0
    started_at = time.time()
    source_counts: Dict[str, int] = {}

    sources = sources or ['auto', 'prix_homologue', 'liste_produit', 'produit_petrolier']
    # Only changed (item-level) flag
    global SKIP_UNCHANGED
    if only_changed is not None:
        SKIP_UNCHANGED = bool(only_changed)

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
            source_counts['auto'] = count
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
        source_counts['prix_homologue'] = count

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
        source_counts['liste_produit'] = count

    # 3b) Produits pétroliers (HTML)
    if 'produit_petrolier' in sources and not maybe_stop():
        count = 0
        for item in scraper.iter_from_produit_petrolier_page():
            items.append(item)
            count += 1
            if maybe_stop():
                break
        logger.info(f"[PRODUIT_PETROLIER] {count} éléments")
        total += count
        source_counts['produit_petrolier'] = count

    # 4) URLs explicites en mode auto adaptatif (si fournis)
    if auto_urls and not maybe_stop():
        for u in auto_urls:
            count = 0
            for item in scraper.iter_auto(u):
                items.append(item)
                count += 1
                if maybe_stop():
                    break
            logger.info(f"[AUTO {u}] {count} éléments")
            total += count

    logger.info(f"Traitement terminé, total {total} éléments.")

    # Checkpointing simple
    if checkpoint:
        ckpt = {'total': total, 'saved': False}
        try:
            with open(checkpoint, 'w', encoding='utf-8') as f:
                json.dump(ckpt, f)
        except Exception:
            pass

    created_prod = 0
    created_prix = 0
    if save:
        # Initialiser Django et persister
        if scraper._init_django():
            created_prod, created_prix = scraper.persist_items(items)
            logger.info(f"Persisté en DB: {created_prod} produits, {created_prix} prix")
            if checkpoint:
                try:
                    with open(checkpoint, 'r+', encoding='utf-8') as f:
                        d = json.load(f)
                        d['saved'] = True
                        f.seek(0)
                        json.dump(d, f, ensure_ascii=False, indent=2)
                        f.truncate()
                except Exception:
                    pass

    # Option: transformer en format unifié
    export_items = [scraper.build_unified(it) for it in items] if unified else items

    # Exports
    if csv_out:
        try:
            import csv
            os.makedirs(os.path.dirname(csv_out) or '.', exist_ok=True)
            with open(csv_out, 'w', newline='', encoding='utf-8') as f:
                if unified:
                    # Aplatir prix[0] pour CSV rapide
                    fieldnames = ['source','categorie','sous_categorie','produit','marque_editeur','zone','valeur','devise','date_maj','type_prix','url_source','date_extraction','statut','confiance']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for e in export_items:
                        if e.get('prix'):
                            for p in e['prix']:
                                writer.writerow({
                                    'source': e['source'],
                                    'categorie': e['categorie'],
                                    'sous_categorie': e['sous_categorie'],
                                    'produit': e['produit'],
                                    'marque_editeur': e['marque_editeur'],
                                    'zone': p.get('zone',''),
                                    'valeur': p.get('valeur'),
                                    'devise': p.get('devise','FCFA'),
                                    'date_maj': p.get('date_maj',''),
                                    'type_prix': p.get('type_prix',''),
                                    'url_source': e['metadata'].get('url_source',''),
                                    'date_extraction': e['metadata'].get('date_extraction',''),
                                    'statut': e['metadata'].get('statut',''),
                                    'confiance': e['metadata'].get('confiance',''),
                                })
                        else:
                            writer.writerow({k: '' for k in fieldnames})
                else:
                    # CSV brut des items
                    fieldnames = sorted({k for it in export_items for k in it.keys()})
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for it in export_items:
                        writer.writerow(it)
            logger.info(f"Export CSV écrit: {csv_out}")
        except Exception as exc:
            logger.error(f"Échec export CSV: {exc}")

    if sql_out:
        try:
            os.makedirs(os.path.dirname(sql_out) or '.', exist_ok=True)
            with open(sql_out, 'w', encoding='utf-8') as f:
                for e in export_items if unified else items:
                    if unified and e.get('prix'):
                        for p in e['prix']:
                            produit_name = str(e.get('produit') or '')
                            source = str(e.get('source') or '').replace("'", "''")
                            categorie = str(e.get('categorie') or '').replace("'", "''")
                            sous_categorie = str(e.get('sous_categorie') or '').replace("'", "''")
                            produit = produit_name.replace("'", "''")
                            marque = str(e.get('marque_editeur') or '').replace("'", "''")
                            zone = str(p.get('zone') or '').replace("'", "''")
                            valeur = p.get('valeur')
                            devise = str(p.get('devise') or 'FCFA').replace("'", "''")
                            type_prix = str(p.get('type_prix') or '').replace("'", "''")
                            date_maj = str(p.get('date_maj') or '').replace("'", "''")
                            url_source = str((e.get('metadata') or {}).get('url_source') or '').replace("'", "''")
                            f.write(f"-- {produit_name}\n")
                            insert_line = (
                                "INSERT INTO produits_temp (source,categorie,sous_categorie,produit,marque,zone,valeur,devise,type_prix,date_maj,url_source) VALUES ("
                                f"'{source}',"
                                f"'{categorie}',"
                                f"'{sous_categorie}',"
                                f"'{produit}',"
                                f"'{marque}',"
                                f"'{zone}',"
                                f"{valeur if valeur is not None else 'NULL'},"
                                f"'{devise}',"
                                f"'{type_prix}',"
                                f"'{date_maj}',"
                                f"'{url_source}'"
                                ");\n"
                            )
                            f.write(insert_line)
                    else:
                        f.write(f"-- Item brut\n{json.dumps(e, ensure_ascii=False)}\n")
            logger.info(f"Export SQL écrit: {sql_out}")
        except Exception as exc:
            logger.error(f"Échec export SQL: {exc}")

    if out:
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(export_items, f, ensure_ascii=False, indent=2)
        logger.info(f"Export JSON écrit: {out} ({len(export_items)} items)")
    else:
        # Affiche un aperçu si pas d'output demandé
        for i, it in enumerate(items[:5]):
            logger.info(f"APERÇU[{i}]: {it}")
    # Rapport
    ended_at = time.time()
    report = {
        'source': 'DGCCRF',
        'total_items': total,
        'source_counts': source_counts,
        'duration_sec': round(ended_at - started_at, 3),
        'saved_products': created_prod,
        'saved_prices': created_prix,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'config': {
            'delay_sec': REQUEST_DELAY_SEC,
            'timeout_sec': REQUEST_TIMEOUT,
            'retries': MAX_RETRIES,
            'backoff': BACKOFF_SEC,
            'respect_robots': RESPECT_ROBOTS,
        }
    }
    target_report = report_out or DEFAULT_REPORT_OUT
    try:
        os.makedirs(os.path.dirname(target_report) or '.', exist_ok=True)
        with open(target_report, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"Rapport écrit: {target_report}")
    except Exception as exc:
        logger.warning(f"Impossible d'écrire le rapport: {exc}")

    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Scraper DGCCRF (JSON/CSV/HTML)')
    p.add_argument('--out', help='Chemin de sortie JSON (ex: data/dgccrf_export.json)')
    p.add_argument('--limit', type=int, default=None, help='Limiter le nombre total d\'items collectés')
    p.add_argument('--sources', default='auto,prix_homologue,liste_produit,produit_petrolier', help='Sources à activer, séparées par des virgules')
    p.add_argument('--save', action='store_true', help='Persister en base via Django (Produit/Magasin/Prix)')
    p.add_argument('--checkpoint', default=CHECKPOINT_PATH, help='Fichier checkpoint pour reprise')
    p.add_argument('--auto-url', action='append', help='URL(s) à traiter en mode auto (peut être multiple)')
    p.add_argument('--unified', action='store_true', help='Exporter au format JSON unifié')
    p.add_argument('--csv', dest='csv_out', help='Chemin de sortie CSV')
    p.add_argument('--sql', dest='sql_out', help='Chemin de sortie SQL (INSERT)')
    p.add_argument('--report', dest='report_out', help='Chemin du rapport JSON (statistiques, erreurs, perfs)')
    p.add_argument('--only-changed', action='store_true', help='Skipper les items identiques à la dernière extraction (diff par hash)')
    return p.parse_args()


if __name__ == '__main__':
    args = parse_args()
    srcs = [s.strip() for s in (args.sources or '').split(',') if s.strip()]
    auto_urls = args.auto_url or None
    raise SystemExit(run_scrape(
        out=args.out,
        limit=args.limit,
        sources=srcs,
        save=args.save,
        checkpoint=args.checkpoint,
        auto_urls=auto_urls,
        unified=args.unified,
        csv_out=args.csv_out,
        sql_out=args.sql_out,
        report_out=args.report_out,
        only_changed=args.only_changed,
    ))
