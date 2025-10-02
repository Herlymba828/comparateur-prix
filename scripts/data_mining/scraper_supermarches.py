#!/usr/bin/env python
import requests
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import formater_prix_xaf, normaliser_nom_produit, get_logger, get_session, safe_get

class ScraperSupermarches:
    def __init__(self):
        self.session = get_session(timeout=20, retries=3, backoff=0.5)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.logger = get_logger()
    
    def scraper_carrefour(self):
        """Exemple de scraper pour Carrefour"""
        self.logger.info("Scraping Carrefour...")
        items = []
        # Exemple fictif
        # resp = safe_get(self.session, 'https://www.carrefour.fr/courses', headers=self.headers, timeout=20)
        # soup = BeautifulSoup(resp.text, 'html.parser')
        # for card in soup.select('.product-card'):
        #     nom = normaliser_nom_produit(card.select_one('.title').get_text())
        #     prix = formater_prix(card.select_one('.price').get_text())
        #     if prix is not None:
        #         items.append({'nom': nom, 'prix': prix, 'source': 'carrefour'})
        time.sleep(0.2)
        return items
    
    def scraper_auchan(self):
        """Exemple de scraper pour Auchan"""
        self.logger.info("Scraping Auchan...")
        items = []
        # Idem, exemple fictif
        time.sleep(0.2)
        return items

    def scrape_many(self, urls: list[str], max_workers: int = 4):
        self.logger.info(f"Scraping {len(urls)} pages avec {max_workers} workers")
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(safe_get, self.session, u, timeout=20, headers=self.headers): u for u in urls}
            for fut in as_completed(futures):
                url = futures[fut]
                try:
                    resp = fut.result()
                    if resp and resp.ok:
                        results.append((url, resp.status_code))
                    else:
                        results.append((url, getattr(resp, 'status_code', 'ERR')))
                except Exception as exc:
                    results.append((url, f"EXC:{exc.__class__.__name__}"))
        return results

if __name__ == '__main__':
    scraper = ScraperSupermarches()
    scraper.scraper_carrefour()