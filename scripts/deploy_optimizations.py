"""
Script pour déployer les optimisations en production.
Usage: python scripts/deploy_optimizations.py [--dry-run]
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.management import call_command
from django.core.cache import cache
from django.db import connection


class DeploymentOptimizer:
    """Classe pour déployer les optimisations."""
    
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.steps_completed = []
        self.steps_failed = []
    
    def log(self, message, level='INFO'):
        """Logger un message."""
        prefix = {
            'INFO': '📝',
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
        }.get(level, '📝')
        
        print(f"{prefix} {message}")
    
    def step_1_clear_cache(self):
        """Étape 1: Vider le cache."""
        self.log("Étape 1: Vidage du cache...", 'INFO')
        
        if self.dry_run:
            self.log("Mode dry-run: cache non vidé", 'WARNING')
            return True
        
        try:
            cache.clear()
            self.log("Cache vidé avec succès", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Erreur lors du vidage du cache: {e}", 'ERROR')
            return False
    
    def step_2_run_migrations(self):
        """Étape 2: Appliquer les migrations."""
        self.log("Étape 2: Application des migrations...", 'INFO')
        
        if self.dry_run:
            self.log("Mode dry-run: migrations non appliquées", 'WARNING')
            return True
        
        try:
            call_command('migrate', '--noinput')
            self.log("Migrations appliquées avec succès", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Erreur lors des migrations: {e}", 'ERROR')
            return False
    
    def step_3_collect_static(self):
        """Étape 3: Collecter les fichiers statiques."""
        self.log("Étape 3: Collecte des fichiers statiques...", 'INFO')
        
        if self.dry_run:
            self.log("Mode dry-run: fichiers statiques non collectés", 'WARNING')
            return True
        
        try:
            call_command('collectstatic', '--noinput', '--clear')
            self.log("Fichiers statiques collectés avec succès", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Erreur lors de la collecte des fichiers statiques: {e}", 'ERROR')
            return False
    
    def step_4_create_indexes(self):
        """Étape 4: Créer les indexes manquants."""
        self.log("Étape 4: Création des indexes...", 'INFO')
        
        if self.dry_run:
            self.log("Mode dry-run: indexes non créés", 'WARNING')
            return True
        
        try:
            # Vérifier si PostgreSQL
            if 'postgresql' not in connection.settings_dict['ENGINE']:
                self.log("Indexes disponibles uniquement pour PostgreSQL", 'WARNING')
                return True
            
            with connection.cursor() as cursor:
                # Index pour les recherches de produits
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_produit_nom_trgm 
                    ON produits_produit USING gin(nom gin_trgm_ops);
                """)
                
                # Index pour les prix
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_prix_actuel 
                    ON produits_prix(prix_actuel) 
                    WHERE est_disponible = true;
                """)
                
                # Index pour les catégories
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_categorie_parent 
                    ON produits_categorie(parent_id) 
                    WHERE parent_id IS NOT NULL;
                """)
            
            self.log("Indexes créés avec succès", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Erreur lors de la création des indexes: {e}", 'ERROR')
            return False
    
    def step_5_warm_cache(self):
        """Étape 5: Préchauffer le cache."""
        self.log("Étape 5: Préchauffage du cache...", 'INFO')
        
        if self.dry_run:
            self.log("Mode dry-run: cache non préchauffé", 'WARNING')
            return True
        
        try:
            from apps.produits.models import Categorie, Produit
            from apps.api.cache_decorators import CacheManager
            
            # Cacher les catégories
            categories = list(Categorie.objects.all().values('id', 'nom', 'slug'))
            CacheManager.set(
                'categories:all',
                categories,
                CacheManager.TIMEOUTS['categories']
            )
            
            # Cacher les produits populaires (par date de création récente)
            produits_populaires = list(
                Produit.objects.filter(est_actif=True)
                .order_by('-date_creation')[:20]
                .values('id', 'nom', 'code_barre')
            )
            CacheManager.set(
                'produits:populaires',
                produits_populaires,
                CacheManager.TIMEOUTS['produits_list']
            )
            
            self.log("Cache préchauffé avec succès", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Erreur lors du préchauffage du cache: {e}", 'ERROR')
            return False
    
    def step_6_verify_optimizations(self):
        """Étape 6: Vérifier les optimisations."""
        self.log("Étape 6: Vérification des optimisations...", 'INFO')
        
        try:
            # Vérifier la connexion DB
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Vérifier le cache
            cache.set('test_key', 'test_value', 10)
            if cache.get('test_key') != 'test_value':
                raise Exception("Cache non fonctionnel")
            cache.delete('test_key')
            
            self.log("Optimisations vérifiées avec succès", 'SUCCESS')
            return True
        except Exception as e:
            self.log(f"Erreur lors de la vérification: {e}", 'ERROR')
            return False
    
    def deploy(self):
        """Déployer toutes les optimisations."""
        self.log("🚀 Démarrage du déploiement des optimisations...", 'INFO')
        
        if self.dry_run:
            self.log("Mode DRY-RUN activé - Aucune modification ne sera effectuée", 'WARNING')
        
        steps = [
            ('Vidage du cache', self.step_1_clear_cache),
            ('Migrations', self.step_2_run_migrations),
            ('Fichiers statiques', self.step_3_collect_static),
            ('Création des indexes', self.step_4_create_indexes),
            ('Préchauffage du cache', self.step_5_warm_cache),
            ('Vérification', self.step_6_verify_optimizations),
        ]
        
        for step_name, step_func in steps:
            try:
                if step_func():
                    self.steps_completed.append(step_name)
                else:
                    self.steps_failed.append(step_name)
            except Exception as e:
                self.log(f"Erreur inattendue dans {step_name}: {e}", 'ERROR')
                self.steps_failed.append(step_name)
        
        # Rapport final
        self.log("\n" + "="*60, 'INFO')
        self.log("📊 RAPPORT DE DÉPLOIEMENT", 'INFO')
        self.log("="*60, 'INFO')
        
        self.log(f"\n✅ Étapes réussies: {len(self.steps_completed)}/{len(steps)}", 'SUCCESS')
        for step in self.steps_completed:
            self.log(f"   - {step}", 'INFO')
        
        if self.steps_failed:
            self.log(f"\n❌ Étapes échouées: {len(self.steps_failed)}/{len(steps)}", 'ERROR')
            for step in self.steps_failed:
                self.log(f"   - {step}", 'ERROR')
        
        self.log("\n" + "="*60, 'INFO')
        
        return len(self.steps_failed) == 0


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Déployer les optimisations')
    parser.add_argument('--dry-run', action='store_true', help='Mode simulation (aucune modification)')
    args = parser.parse_args()
    
    optimizer = DeploymentOptimizer(dry_run=args.dry_run)
    success = optimizer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
