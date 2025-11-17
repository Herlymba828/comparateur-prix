"""
Module pour la sauvegarde automatisée des données du scraper DGCCRF.

Fournit des méthodes pour sauvegarder les données dans différents formats (JSON, CSV, Excel).
"""

import json
import csv
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import pandas as pd

logger = logging.getLogger(__name__)


class DataSaver:
    """Classe pour gérer la sauvegarde des données du scraper.
    
    Cette classe fournit des méthodes pour sauvegarder les données dans différents formats
    (JSON, CSV, Excel) avec rotation des fichiers et gestion des erreurs.
    """
    
    def __init__(
        self,
        output_dir: str = "data",
        max_backups: int = 5,
        compress_old: bool = True
    ) -> None:
        """Initialise le DataSaver.
        
        Args:
            output_dir: Répertoire de sortie pour les sauvegardes
            max_backups: Nombre maximum de sauvegardes à conserver
            compress_old: Si True, compresse les anciennes sauvegardes
        """
        self.output_dir = Path(output_dir)
        self.max_backups = max(max_backups, 1)  # Au moins 1 sauvegarde
        self.compress_old = compress_old
        self._ensure_directory()
    
    def _ensure_directory(self) -> None:
        """S'assure que le répertoire de sortie existe."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            logger.debug("Répertoire de sortie configuré: %s", self.output_dir.absolute())
        except OSError as e:
            logger.error("Impossible de créer le répertoire de sortie: %s", str(e))
            raise
    
    def _get_timestamp(self) -> str:
        """Retourne un timestamp pour les noms de fichiers."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _clean_filename(self, name: str) -> str:
        """Nettoie un nom de fichier pour qu'il soit valide."""
        # Remplace les caractères non valides par des underscores
        invalid = '<>:"/\\|?*' + ''.join(chr(i) for i in range(32))
        for char in invalid:
            name = name.replace(char, '_')
        return name.strip()
    
    def _rotate_backups(self, base_name: str, extension: str) -> None:
        """Effectue une rotation des sauvegardes existantes.
        
        Args:
            base_name: Nom de base des fichiers de sauvegarde
            extension: Extension des fichiers (sans le point)
        """
        try:
            # Liste tous les fichiers correspondant au motif
            pattern = f"{base_name}_*.{extension}"
            files = sorted(self.output_dir.glob(pattern), key=os.path.getmtime)
            
            # Supprime les anciennes sauvegardes si nécessaire
            while len(files) >= self.max_backups:
                old_file = files.pop(0)
                try:
                    old_file.unlink()
                    logger.debug("Ancienne sauvegarde supprimée: %s", old_file.name)
                except OSError as e:
                    logger.error("Impossible de supprimer l'ancienne sauvegarde %s: %s", 
                                old_file, str(e))
        except Exception as e:
            logger.error("Erreur lors de la rotation des sauvegardes: %s", str(e))
    
    def save_json(
        self,
        data: Union[Dict, List],
        filename: str,
        indent: int = 2,
        ensure_ascii: bool = False
    ) -> Optional[Path]:
        """Sauvegarde des données au format JSON.
        
        Args:
            data: Données à sauvegarder (doivent être sérialisables en JSON)
            filename: Nom du fichier (sans extension)
            indent: Indentation pour le formatage JSON
            ensure_ascii: Si False, permet les caractères Unicode
            
        Returns:
            Path: Chemin du fichier sauvegardé ou None en cas d'erreur
        """
        filename = self._clean_filename(filename)
        timestamp = self._get_timestamp()
        filepath = self.output_dir / f"{filename}_{timestamp}.json"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            
            logger.info("Données sauvegardées au format JSON: %s", filepath.name)
            self._rotate_backups(filename, 'json')
            return filepath
            
        except (IOError, TypeError, ValueError) as e:
            logger.error("Erreur lors de la sauvegarde en JSON: %s", str(e))
            return None
    
    def save_csv(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        delimiter: str = ',',
        quotechar: str = '"',
        quoting: int = csv.QUOTE_MINIMAL
    ) -> Optional[Path]:
        """Sauvegarde des données au format CSV.
        
        Args:
            data: Liste de dictionnaires à sauvegarder
            filename: Nom du fichier (sans extension)
            delimiter: Caractère délimiteur
            quotechar: Caractère d'encadrement
            quoting: Niveau de citation CSV
            
        Returns:
            Path: Chemin du fichier sauvegardé ou None en cas d'erreur
        """
        if not data:
            logger.warning("Aucune donnée à sauvegarder au format CSV")
            return None
            
        filename = self._clean_filename(filename)
        timestamp = self._get_timestamp()
        filepath = self.output_dir / f"{filename}_{timestamp}.csv"
        
        try:
            # Extraction des en-têtes à partir des clés du premier élément
            fieldnames = list(data[0].keys())
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=fieldnames,
                    delimiter=delimiter,
                    quotechar=quotechar,
                    quoting=quoting
                )
                writer.writeheader()
                writer.writerows(data)
            
            logger.info("Données sauvegardées au format CSV: %s", filepath.name)
            self._rotate_backups(filename, 'csv')
            return filepath
            
        except (IOError, csv.Error, IndexError) as e:
            logger.error("Erreur lors de la sauvegarde en CSV: %s", str(e))
            return None
    
    def save_excel(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        sheet_name: str = "Données"
    ) -> Optional[Path]:
        """Sauvegarde des données au format Excel.
        
        Args:
            data: Liste de dictionnaires à sauvegarder
            filename: Nom du fichier (sans extension)
            sheet_name: Nom de l'onglet Excel
            
        Returns:
            Path: Chemin du fichier sauvegardé ou None en cas d'erreur
        """
        if not data:
            logger.warning("Aucune donnée à sauvegarder au format Excel")
            return None
            
        try:
            import pandas as pd
        except ImportError:
            logger.error("La bibliothèque pandas est requise pour l'export Excel")
            return None
            
        filename = self._clean_filename(filename)
        timestamp = self._get_timestamp()
        filepath = self.output_dir / f"{filename}_{timestamp}.xlsx"
        
        try:
            df = pd.DataFrame(data)
            df.to_excel(filepath, sheet_name=sheet_name, index=False, engine='openpyxl')
            
            logger.info("Données sauvegardées au format Excel: %s", filepath.name)
            self._rotate_backups(filename, 'xlsx')
            return filepath
            
        except Exception as e:
            logger.error("Erreur lors de la sauvegarde en Excel: %s", str(e))
            return None


# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Création d'une instance de DataSaver
    saver = DataSaver(output_dir="data/export", max_backups=3)
    
    # Données de test
    test_data = [
        {"id": 1, "nom": "Produit A", "prix": 10.99, "disponible": True},
        {"id": 2, "nom": "Produit B", "prix": 24.50, "disponible": False},
        {"id": 3, "nom": "Produit C", "prix": 15.75, "disponible": True},
    ]
    
    # Sauvegarde des données dans différents formats
    saver.save_json(test_data, "test_export")
    saver.save_csv(test_data, "test_export")
    saver.save_excel(test_data, "test_export")
