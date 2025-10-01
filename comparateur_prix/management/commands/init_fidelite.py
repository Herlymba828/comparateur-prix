from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.utilisateurs.models import Utilisateur
from apps.utilisateurs.services import ServiceFidelite

class Command(BaseCommand):
    """Commande pour initialiser le système de fidélité"""
    
    help = 'Initialise le système de fidélité pour tous les utilisateurs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forcer la réinitialisation des niveaux de fidélité',
        )
    
    def handle(self, *args, **options):
        force = options['force']
        
        self.stdout.write('Initialisation du système de fidélité...')
        
        utilisateurs = Utilisateur.objects.all()
        total = utilisateurs.count()
        
        self.stdout.write(f'Traitement de {total} utilisateurs...')
        
        for i, utilisateur in enumerate(utilisateurs, 1):
            if force or utilisateur.niveau_fidelite == 1:
                # Recalculer le niveau basé sur le total des achats
                nouveau_niveau = ServiceFidelite.calculer_niveau_fidelite(
                    utilisateur.total_achats
                )
                
                if nouveau_niveau != utilisateur.niveau_fidelite:
                    utilisateur.niveau_fidelite = nouveau_niveau
                    utilisateur.save(update_fields=['niveau_fidelite'])
                    
                    self.stdout.write(
                        f"{i}/{total}: {utilisateur.username} -> Niveau {nouveau_niveau}"
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Initialisation du système de fidélité terminée avec succès!')
        )