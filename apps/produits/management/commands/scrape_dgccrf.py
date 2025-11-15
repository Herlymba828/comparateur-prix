"""
Commande Django pour lancer le scraping DGCCRF et sauvegarder les données en base.

Usage:
    python manage.py scrape_dgccrf
    python manage.py scrape_dgccrf --limit 50
    python manage.py scrape_dgccrf --sources liste_produit
"""
import logging
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Lance le scraping DGCCRF et sauvegarde automatiquement les données en base de données. "
        "Les données sont sauvegardées dans Produit, Prix, HomologationProduit et PrixHomologue."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help="Limiter le nombre d'éléments à scraper"
        )
        parser.add_argument(
            '--sources',
            type=str,
            default='liste_produit',
            help="Sources à scraper, séparées par des virgules (ex: liste_produit,prix_homologue)"
        )
        parser.add_argument(
            '--no-save',
            action='store_true',
            help="Ne pas sauvegarder en base de données (test uniquement)"
        )
        parser.add_argument(
            '--only-changed',
            action='store_true',
            default=True,
            help="Ne scraper que les éléments modifiés depuis la dernière extraction (par défaut: True)"
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        sources_str = options.get('sources', 'liste_produit')
        # Sauvegarde activée par défaut (désactiver avec --no-save)
        save = not options.get('no_save', False)
        only_changed = options.get('only_changed', True)
        
        # Parser les sources
        sources = [s.strip() for s in sources_str.split(',') if s.strip()]
        
        self.stdout.write(self.style.SUCCESS(
            f"Démarrage du scraping DGCCRF (sources: {', '.join(sources)}, "
            f"save={save}, limit={limit}, only_changed={only_changed})"
        ))
        
        # Importer le module scraper
        import sys
        base_dir = Path(getattr(settings, 'BASE_DIR', Path(__file__).resolve().parents[4]))
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))
        
        # Import du scraper
        import importlib.util
        scraper_path = base_dir / 'scripts' / 'scraper_dgccrf.py'
        
        if not scraper_path.exists():
            self.stdout.write(self.style.ERROR(f"Fichier scraper introuvable: {scraper_path}"))
            return
        
        spec = importlib.util.spec_from_file_location("scraper_dgccrf", scraper_path)
        scraper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scraper_module)
        run_scrape = scraper_module.run_scrape
        
        # Préparer les chemins de sortie
        data_dir = base_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        
        report_path = data_dir / 'dgccrf_scrape_report.json'
        
        try:
            # Exécuter le scraping avec sauvegarde activée
            result = run_scrape(
                out=None,  # Pas de JSON de sortie par défaut
                limit=limit,
                sources=sources,
                save=True if save else False,  # Force explicitement la valeur
                unified=False,
                csv_out=None,
                sql_out=None,
                report_out=str(report_path),
                only_changed=only_changed,
            )
            
            # Lire le rapport pour afficher les statistiques
            if report_path.exists():
                import json
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                
                self.stdout.write(self.style.SUCCESS(
                    f"\n✓ Scraping terminé avec succès!\n"
                    f"  - Total items extraits: {report_data.get('total_items', 0)}\n"
                    f"  - Durée: {report_data.get('duration_sec', 0):.2f} secondes\n"
                    f"  - Rapport: {report_path}"
                ))
                
                if save:
                    self.stdout.write(self.style.SUCCESS(
                        f"  - Produits sauvegardés: {report_data.get('saved_products', 0)}\n"
                        f"  - Prix sauvegardés: {report_data.get('saved_prices', 0)}"
                    ))
            else:
                self.stdout.write(self.style.WARNING("Rapport non généré"))
            
            return result
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors du scraping: {e}"))
            logger.exception("Erreur scraping DGCCRF")
            raise

