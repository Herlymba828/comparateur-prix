import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.produits.models import HomologationProduit

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Unifie tous les produits DGCCRF (HomologationProduit) dans la table Produit principale"

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limiter le nombre de produits à unifier'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la création même si un produit existe déjà'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        force = options.get('force', False)
        
        self.stdout.write(self.style.SUCCESS('Démarrage de l\'unification des produits DGCCRF...'))
        
        # Vérifier si la colonne produit_id existe
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='produits_homologationproduit' 
                AND column_name='produit_id'
            """)
            column_exists = cursor.fetchone() is not None
        
        if not column_exists:
            self.stdout.write(
                self.style.ERROR(
                    'La colonne produit_id n\'existe pas encore dans la table produits_homologationproduit.\n'
                    'Veuillez d\'abord appliquer la migration:\n'
                    'python manage.py migrate produits 0012'
                )
            )
            return
        
        # Récupérer tous les HomologationProduit sans produit associé
        # Utiliser une requête SQL brute si nécessaire pour éviter les erreurs
        try:
            queryset = HomologationProduit.objects.filter(produit__isnull=True)
        except Exception as e:
            # Si la relation ne fonctionne pas, utiliser une requête SQL brute
            self.stdout.write(
                self.style.WARNING(
                    f'Erreur avec la requête ORM, utilisation d\'une requête SQL brute: {e}'
                )
            )
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT id FROM produits_homologationproduit 
                    WHERE produit_id IS NULL
                    ORDER BY id
                """)
                ids = [row[0] for row in cursor.fetchall()]
                queryset = HomologationProduit.objects.filter(id__in=ids)
        
        if limit:
            queryset = queryset[:limit]
        
        total = queryset.count()
        self.stdout.write(f"Nombre de produits à unifier: {total}")
        
        created = 0
        errors = 0
        
        for homologation in queryset:
            try:
                with transaction.atomic():
                    if force and homologation.produit:
                        # Si force et produit existe, recréer
                        homologation.produit = None
                        homologation.save(update_fields=['produit'])
                    
                    produit_unifie = homologation.creer_produit_unifie()
                    created += 1
                    
                    if created % 100 == 0:
                        self.stdout.write(f"Progression: {created}/{total} produits unifiés...")
                        
            except Exception as e:
                errors += 1
                logger.error(f"Erreur lors de l'unification de HomologationProduit {homologation.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f"Erreur pour {homologation.nom}: {str(e)}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nUnification terminée: {created} produits créés, {errors} erreurs'
            )
        )

