"""
Scraper DGCCRF Version 2 - Amélioré et robuste.
Supporte plusieurs sources de données et formats.
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import hashlib
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class DGCCRFScraperV2:
    """Scraper amélioré pour les données DGCCRF."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialiser le scraper.
        
        Args:
            config: Configuration personnalisée
        """
        self.config = config or self._get_default_config()
        self.session = self._create_session()
        self.cache = {}
        self.stats = {
            'requests': 0,
            'success': 0,
            'errors': 0,
            'cached': 0
        }
    
    def _get_default_config(self) -> Dict:
        """Configuration par défaut."""
        import os
        return {
            'base_url': os.getenv('DGCCRF_BASE_URL', 'https://www.dgccrf.ga/'),
            'endpoints': {
                'prix_homologue': os.getenv('DGCCRF_PRIX_HOMOLOGUE_URL', 'echo-prix-homologue'),
                'liste_produit': os.getenv('DGCCRF_LISTE_PRODUIT_URL', 'echo-liste-produit'),
                'produit_petrolier': os.getenv('DGCCRF_PRODUIT_PETROLIER_URL', 'echo-produit-petrolier'),
            },
            'timeout': 30,
            'max_retries': 3,
            'backoff_factor': 1.5,
            'delay_between_requests': 1.0,
            'user_agent': 'ComparateurPrixBot/2.0 (+contact@example.com)',
            'cache_enabled': True,
            'cache_ttl': 3600,  # 1 heure
        }
    
    def _create_session(self) -> requests.Session:
        """Créer une session HTTP avec retry automatique."""
        session = requests.Session()
        
        # Configuration du retry
        retry_strategy = Retry(
            total=self.config['max_retries'],
            backoff_factor=self.config['backoff_factor'],
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Headers
        session.headers.update({
            'User-Agent': self.config['user_agent'],
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
        })
        
        return session
    
    def _get_cache_key(self, url: str, params: Optional[Dict] = None) -> str:
        """Générer une clé de cache."""
        cache_str = f"{url}:{json.dumps(params or {}, sort_keys=True)}"
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Vérifier si le cache est valide."""
        if not self.config['cache_enabled']:
            return False
        
        if cache_key not in self.cache:
            return False
        
        cached_data = self.cache[cache_key]
        age = time.time() - cached_data['timestamp']
        
        return age < self.config['cache_ttl']
    
    def fetch_url(self, url: str, params: Optional[Dict] = None, method: str = 'GET') -> Optional[Dict]:
        """
        Récupérer des données depuis une URL avec cache et retry.
        
        Args:
            url: URL à récupérer
            params: Paramètres de requête
            method: Méthode HTTP
        
        Returns:
            Données JSON ou None en cas d'erreur
        """
        cache_key = self._get_cache_key(url, params)
        
        # Vérifier le cache
        if self._is_cache_valid(cache_key):
            self.stats['cached'] += 1
            logger.debug(f"Cache hit pour {url}")
            return self.cache[cache_key]['data']
        
        # Faire la requête
        self.stats['requests'] += 1
        
        try:
            logger.info(f"Requête {method} vers {url}")
            
            if method == 'GET':
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config['timeout']
                )
            elif method == 'POST':
                response = self.session.post(
                    url,
                    json=params,
                    timeout=self.config['timeout']
                )
            else:
                raise ValueError(f"Méthode non supportée: {method}")
            
            response.raise_for_status()
            
            # Parser la réponse
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                data = response.json()
            elif 'text/html' in content_type:
                # Parser le HTML
                data = self._parse_html(response.text, url)
            else:
                data = {'raw': response.text}
            
            # Mettre en cache
            if self.config['cache_enabled']:
                self.cache[cache_key] = {
                    'data': data,
                    'timestamp': time.time()
                }
            
            self.stats['success'] += 1
            
            # Délai entre les requêtes
            time.sleep(self.config['delay_between_requests'])
            
            return data
        
        except requests.exceptions.RequestException as e:
            self.stats['errors'] += 1
            logger.error(f"Erreur lors de la requête vers {url}: {e}")
            return None
    
    def _parse_html(self, html: str, url: str) -> Dict:
        """
        Parser le HTML pour extraire les données.
        
        Args:
            html: Contenu HTML
            url: URL source
        
        Returns:
            Données extraites
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        data = {
            'url': url,
            'title': soup.title.string if soup.title else None,
            'timestamp': datetime.now().isoformat(),
        }
        
        # Extraire les tableaux de données
        tables = soup.find_all('table')
        if tables:
            data['tables'] = []
            for table in tables:
                table_data = self._parse_table(table)
                if table_data:
                    data['tables'].append(table_data)
        
        # Extraire les listes
        lists = soup.find_all(['ul', 'ol'])
        if lists:
            data['lists'] = []
            for lst in lists:
                items = [li.get_text(strip=True) for li in lst.find_all('li')]
                if items:
                    data['lists'].append(items)
        
        # Extraire les données JSON embarquées
        scripts = soup.find_all('script', type='application/json')
        if scripts:
            data['embedded_json'] = []
            for script in scripts:
                try:
                    json_data = json.loads(script.string)
                    data['embedded_json'].append(json_data)
                except json.JSONDecodeError:
                    pass
        
        return data
    
    def _parse_table(self, table) -> Optional[Dict]:
        """Parser un tableau HTML."""
        headers = []
        rows = []
        
        # Extraire les en-têtes
        thead = table.find('thead')
        if thead:
            header_cells = thead.find_all(['th', 'td'])
            headers = [cell.get_text(strip=True) for cell in header_cells]
        
        # Extraire les lignes
        tbody = table.find('tbody') or table
        for tr in tbody.find_all('tr'):
            cells = tr.find_all(['td', 'th'])
            if cells:
                row = [cell.get_text(strip=True) for cell in cells]
                rows.append(row)
        
        if not rows:
            return None
        
        return {
            'headers': headers,
            'rows': rows
        }
    
    def scrape_prix_homologues(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Scraper les prix homologués.
        
        Args:
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des prix homologués
        """
        url = f"{self.config['base_url']}{self.config['endpoints']['prix_homologue']}"
        
        logger.info(f"Scraping des prix homologués depuis {url}")
        
        data = self.fetch_url(url)
        
        if not data:
            logger.warning("Aucune donnée récupérée pour les prix homologués")
            return []
        
        # Extraire les prix depuis les données
        prix_list = self._extract_prix_from_data(data)
        
        if limit:
            prix_list = prix_list[:limit]
        
        logger.info(f"{len(prix_list)} prix homologués récupérés")
        
        return prix_list
    
    def scrape_liste_produits(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Scraper la liste des produits.
        
        Args:
            limit: Nombre maximum de résultats
        
        Returns:
            Liste des produits
        """
        url = f"{self.config['base_url']}{self.config['endpoints']['liste_produit']}"
        
        logger.info(f"Scraping de la liste des produits depuis {url}")
        
        data = self.fetch_url(url)
        
        if not data:
            logger.warning("Aucune donnée récupérée pour la liste des produits")
            return []
        
        # Extraire les produits depuis les données
        produits_list = self._extract_produits_from_data(data)
        
        if limit:
            produits_list = produits_list[:limit]
        
        logger.info(f"{len(produits_list)} produits récupérés")
        
        return produits_list
    
    def _extract_prix_from_data(self, data: Dict) -> List[Dict]:
        """Extraire les prix depuis les données."""
        prix_list = []
        
        # Si c'est déjà une liste
        if isinstance(data, list):
            return data
        
        # Si c'est un dict avec une clé 'results' ou 'data'
        if isinstance(data, dict):
            if 'results' in data:
                return data['results']
            if 'data' in data:
                return data['data']
            if 'prix' in data:
                return data['prix']
            
            # Si c'est des tables HTML parsées
            if 'tables' in data:
                for table in data['tables']:
                    prix_list.extend(self._table_to_prix(table))
        
        return prix_list
    
    def _extract_produits_from_data(self, data: Dict) -> List[Dict]:
        """Extraire les produits depuis les données."""
        produits_list = []
        
        # Si c'est déjà une liste
        if isinstance(data, list):
            return data
        
        # Si c'est un dict avec une clé 'results' ou 'data'
        if isinstance(data, dict):
            if 'results' in data:
                return data['results']
            if 'data' in data:
                return data['data']
            if 'produits' in data:
                return data['produits']
            
            # Si c'est des tables HTML parsées
            if 'tables' in data:
                for table in data['tables']:
                    produits_list.extend(self._table_to_produits(table))
        
        return produits_list
    
    def _table_to_prix(self, table: Dict) -> List[Dict]:
        """Convertir un tableau HTML en liste de prix."""
        prix_list = []
        headers = table.get('headers', [])
        rows = table.get('rows', [])
        
        for row in rows:
            if len(row) >= 2:
                prix = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        prix[headers[i]] = value
                    else:
                        prix[f'col_{i}'] = value
                prix_list.append(prix)
        
        return prix_list
    
    def _table_to_produits(self, table: Dict) -> List[Dict]:
        """Convertir un tableau HTML en liste de produits."""
        return self._table_to_prix(table)  # Même logique
    
    def get_stats(self) -> Dict:
        """Obtenir les statistiques du scraper."""
        return {
            **self.stats,
            'cache_size': len(self.cache),
            'success_rate': (self.stats['success'] / self.stats['requests'] * 100) if self.stats['requests'] > 0 else 0
        }
    
    def clear_cache(self):
        """Vider le cache."""
        self.cache.clear()
        logger.info("Cache vidé")


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scraper DGCCRF V2')
    parser.add_argument('--source', choices=['prix', 'produits', 'all'], default='all', help='Source à scraper')
    parser.add_argument('--limit', type=int, help='Nombre maximum de résultats')
    parser.add_argument('--output', help='Fichier de sortie JSON')
    parser.add_argument('--no-cache', action='store_true', help='Désactiver le cache')
    args = parser.parse_args()
    
    # Configuration
    config = None
    if args.no_cache:
        config = {'cache_enabled': False}
    
    # Créer le scraper
    scraper = DGCCRFScraperV2(config)
    
    results = {}
    
    # Scraper selon la source
    if args.source in ['prix', 'all']:
        results['prix_homologues'] = scraper.scrape_prix_homologues(limit=args.limit)
    
    if args.source in ['produits', 'all']:
        results['produits'] = scraper.scrape_liste_produits(limit=args.limit)
    
    # Afficher les stats
    stats = scraper.get_stats()
    print(f"\n📊 Statistiques:")
    print(f"   Requêtes: {stats['requests']}")
    print(f"   Succès: {stats['success']}")
    print(f"   Erreurs: {stats['errors']}")
    print(f"   Cache hits: {stats['cached']}")
    print(f"   Taux de succès: {stats['success_rate']:.1f}%")
    
    # Sauvegarder les résultats
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Résultats sauvegardés dans {args.output}")
    else:
        print(f"\n📦 Résultats:")
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
