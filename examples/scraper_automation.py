#!/usr/bin/env python
"""
Exemple d'utilisation du système de sauvegarde automatisé du scraper DGCCRF.

Ce script montre comment utiliser le système de sauvegarde intégré pour exporter
les données dans différents formats (JSON, CSV, Excel) avec rotation des fichiers.
"""

import os
import sys
import logging
from datetime import datetime

# Ajout du répertoire parent au chemin pour importer le module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.scraper_dgccrf import DgccrfScraper
from scripts.config import DEFAULT_BASE_URL

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper_automation.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Fonction principale pour démontrer l'utilisation du système de sauvegarde."""
    logger.info("Démarrage du script d'automatisation du scraper DGCCRF")
    
    try:
        # Initialisation du scraper avec configuration personnalisée
        scraper = DgccrfScraper(
            base_url=DEFAULT_BASE_URL,
            output_dir="data/exports",  # Répertoire de sortie personnalisé
            max_backups=3,             # Conserver les 3 dernières sauvegardes
            request_delay=1,           # 1 seconde entre les requêtes
            timeout=30,                # 30 secondes de timeout
            max_retries=3              # 3 tentatives maximum
        )
        
        logger.info("Scraper initialisé avec succès")
        
        # Exécution du scraping avec sauvegarde dans tous les formats
        result = scraper.scrape(
            save_format='all',  # Sauvegarder dans tous les formats disponibles
            output_filename=f"dgccrf_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if result['success']:
            logger.info(
                "Scraping terminé avec succès! %d produits trouvés.",
                result['stats']['total_products']
            )
            
            # Afficher les fichiers sauvegardés
            if result['stats']['saved_files']:
                logger.info("Fichiers sauvegardés:")
                for file_path in result['stats']['saved_files']:
                    logger.info("  - %s", file_path)
            else:
                logger.warning("Aucun fichier n'a été sauvegardé.")
                
            # Afficher les statistiques
            logger.info("Statistiques du scraping:")
            logger.info("  - Temps de traitement: %.2f secondes", 
                      result['stats']['processing_time'])
            logger.info("  - URL source: %s", result['metadata']['url'])
            
        else:
            logger.error(
                "Erreur lors du scraping: %s",
                result.get('error', 'Raison inconnue')
            )
            
    except Exception as e:
        logger.critical("Erreur critique lors de l'exécution du script: %s", str(e), exc_info=True)
        return 1
    
    logger.info("Script terminé avec succès")
    return 0

if __name__ == "__main__":
    sys.exit(main())
