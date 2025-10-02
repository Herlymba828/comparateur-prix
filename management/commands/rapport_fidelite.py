from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.utilisateurs.services import ServiceFidelite
from apps.utilisateurs.utils import GenerateurRapport
import json

class Command(BaseCommand):
    """Commande pour générer un rapport de fidélité"""
    
    help = 'Génère un rapport détaillé du système de fidélité'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--periode',
            type=int,
            default=30,
            help='Période du rapport en jours (défaut: 30)',
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Fichier de sortie pour le rapport JSON',
        )
    
    def handle(self, *args, **options):
        periode_jours = options['periode']
        fichier_sortie = options['output']
        
        date_fin = timezone.now()
        date_debut = date_fin - timedelta(days=periode_jours)
        
        self.stdout.write(
            f'Génération du rapport de fidélité pour la période '
            f'du {date_debut.strftime("%d/%m/%Y")} au {date_fin.strftime("%d/%m/%Y")}'
        )
        
        # Générer le rapport
        from apps.utilisateurs.models import Utilisateur
        utilisateurs = Utilisateur.objects.all()
        rapport = GenerateurRapport.generer_rapport_utilisateurs(
            utilisateurs, date_debut, date_fin
        )
        
        # Afficher le rapport
        self.stdout.write("\n" + "="*50)
        self.stdout.write("RAPPORT DE FIDÉLITÉ")
        self.stdout.write("="*50)
        
        stats = rapport['statistiques_generales']
        self.stdout.write(f"Utilisateurs totaux: {stats['total_utilisateurs']}")
        self.stdout.write(f"Nouveaux utilisateurs: {stats['nouveaux_utilisateurs']}")
        self.stdout.write(f"Utilisateurs actifs: {stats['utilisateurs_actifs']}")
        
        self.stdout.write("\nRépartition par niveau de fidélité:")
        for niveau, count in rapport['repartition_niveau_fidelite'].items():
            self.stdout.write(f"  {niveau}: {count} utilisateurs")
        
        # Sauvegarder dans un fichier si demandé
        if fichier_sortie:
            with open(fichier_sortie, 'w', encoding='utf-8') as f:
                json.dump(rapport, f, indent=2, ensure_ascii=False)
            self.stdout.write(f"\nRapport sauvegardé dans: {fichier_sortie}")
        
        self.stdout.write(self.style.SUCCESS('\nRapport généré avec succès!'))