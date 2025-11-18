"""
Commande Django pour créer un backup de la base de données.

Usage:
    python manage.py backup_database
    python manage.py backup_database --format json
    python manage.py backup_database --output backups/
    python manage.py backup_database --compress
"""
import os
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Crée un backup de la base de données (PostgreSQL dump ou export JSON)"

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            type=str,
            choices=['sql', 'json', 'both'],
            default='sql',
            help="Format du backup (sql, json, ou both)"
        )
        parser.add_argument(
            '--output',
            type=str,
            default='backups',
            help="Répertoire de sortie pour les backups"
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            help="Compresser le backup (gzip pour SQL, pas pour JSON)"
        )
        parser.add_argument(
            '--keep',
            type=int,
            default=7,
            help="Nombre de backups à conserver (par défaut: 7)"
        )

    def handle(self, *args, **options):
        format_type = options.get('format', 'sql')
        output_dir = Path(options.get('output', 'backups'))
        compress = options.get('compress', False)
        keep_backups = options.get('keep', 7)
        
        # Créer le répertoire de backup
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.stdout.write(self.style.SUCCESS(f"Création du backup (format: {format_type})..."))
        
        try:
            # Backup SQL (PostgreSQL dump)
            if format_type in ('sql', 'both'):
                sql_file = self.create_sql_backup(output_dir, timestamp, compress)
                if sql_file:
                    self.stdout.write(self.style.SUCCESS(f"✓ Backup SQL créé: {sql_file}"))
                    self.cleanup_old_backups(output_dir, 'sql', keep_backups)
            
            # Backup JSON (export des données)
            if format_type in ('json', 'both'):
                json_file = self.create_json_backup(output_dir, timestamp)
                if json_file:
                    self.stdout.write(self.style.SUCCESS(f"✓ Backup JSON créé: {json_file}"))
                    self.cleanup_old_backups(output_dir, 'json', keep_backups)
            
            self.stdout.write(self.style.SUCCESS("✓ Backup terminé avec succès!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur lors du backup: {e}"))
            logger.exception("Erreur lors du backup de la base de données")
            raise
    
    def create_sql_backup(self, output_dir: Path, timestamp: str, compress: bool) -> Path:
        """Crée un backup SQL de la base de données."""
        db_settings = settings.DATABASES['default']
        db_name = db_settings.get('NAME')
        db_user = db_settings.get('USER', 'postgres')
        db_host = db_settings.get('HOST', 'localhost')
        db_port = db_settings.get('PORT', '5432')
        db_password = db_settings.get('PASSWORD', '')
        
        # Nom du fichier
        sql_file = output_dir / f'backup_{timestamp}.sql'
        if compress:
            sql_file = output_dir / f'backup_{timestamp}.sql.gz'
        
        try:
            # Utiliser pg_dump pour PostgreSQL
            env = os.environ.copy()
            if db_password:
                env['PGPASSWORD'] = db_password
            
            # Utiliser format plain pour pouvoir compresser avec gzip après
            cmd = [
                'pg_dump',
                '-h', str(db_host),
                '-p', str(db_port),
                '-U', str(db_user),
                '-d', str(db_name),
                '--no-owner',
                '--no-acl',
                '-F', 'p',  # Format plain (toujours)
            ]
            
            if compress:
                # Utiliser gzip pour la compression
                import gzip
                with gzip.open(sql_file, 'wb') as f:
                    result = subprocess.run(
                        cmd,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        env=env,
                        check=True
                    )
            else:
                with open(sql_file, 'wb') as f:
                    result = subprocess.run(
                        cmd,
                        stdout=f,
                        stderr=subprocess.PIPE,
                        env=env,
                        check=True
                    )
            
            logger.info(f"Backup SQL créé: {sql_file}")
            return sql_file
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erreur pg_dump: {e.stderr.decode() if e.stderr else str(e)}")
            # Fallback: utiliser Django dumpdata
            return self.create_django_dump(output_dir, timestamp)
        except FileNotFoundError:
            # pg_dump n'est pas disponible, utiliser Django dumpdata
            self.stdout.write(self.style.WARNING("pg_dump non disponible, utilisation de Django dumpdata"))
            return self.create_django_dump(output_dir, timestamp)
    
    def create_django_dump(self, output_dir: Path, timestamp: str) -> Path:
        """Crée un backup en utilisant Django dumpdata."""
        json_file = output_dir / f'backup_django_{timestamp}.json'
        
        try:
            from django.core.management import call_command
            from io import StringIO
            
            output = StringIO()
            call_command('dumpdata', '--natural-foreign', '--natural-primary', stdout=output)
            
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(output.getvalue())
            
            logger.info(f"Backup Django créé: {json_file}")
            return json_file
            
        except Exception as e:
            logger.error(f"Erreur lors du dump Django: {e}")
            raise
    
    def create_json_backup(self, output_dir: Path, timestamp: str) -> Path:
        """Crée un backup JSON des données principales."""
        json_file = output_dir / f'backup_data_{timestamp}.json'
        
        try:
            from django.core.management import call_command
            from io import StringIO
            
            # Exporter les données principales
            apps_to_backup = [
                'produits',
                'magasins',
                'utilisateurs',
            ]
            
            output = StringIO()
            call_command(
                'dumpdata',
                *apps_to_backup,
                '--natural-foreign',
                '--natural-primary',
                '--indent', '2',
                stdout=output
            )
            
            with open(json_file, 'w', encoding='utf-8') as f:
                f.write(output.getvalue())
            
            logger.info(f"Backup JSON créé: {json_file}")
            return json_file
            
        except Exception as e:
            logger.error(f"Erreur lors du backup JSON: {e}")
            raise
    
    def cleanup_old_backups(self, output_dir: Path, extension: str, keep: int):
        """Supprime les anciens backups, ne garde que les N plus récents."""
        try:
            # Trouver tous les fichiers de backup avec l'extension
            pattern = f'backup*.{extension}'
            if extension == 'sql':
                pattern = 'backup*.sql*'  # Inclure .sql.gz
            
            backups = sorted(
                output_dir.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            # Supprimer les anciens backups
            if len(backups) > keep:
                for old_backup in backups[keep:]:
                    old_backup.unlink()
                    logger.info(f"Ancien backup supprimé: {old_backup.name}")
                    self.stdout.write(self.style.WARNING(f"  - Supprimé: {old_backup.name}"))
        
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage des anciens backups: {e}")

