"""
Commande pour initialiser les catégories de produits standard
Usage: python manage.py init_categories
"""
from django.core.management.base import BaseCommand
from apps.produits.models import Categorie
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Initialise les catégories de produits standard'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la création même si des catégories existent déjà',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprime toutes les catégories existantes avant de créer les nouvelles',
        )

    def handle(self, *args, **options):
        force = options['force']
        clear = options['clear']
        
        # Structure des catégories standard
        categories_data = [
            {
                'nom': 'Alimentation',
                'description': 'Produits alimentaires et denrées',
                'ordre': 1,
                'sous_categories': [
                    {'nom': 'Fruits et légumes', 'ordre': 1},
                    {'nom': 'Viandes et poissons', 'ordre': 2},
                    {'nom': 'Produits laitiers', 'ordre': 3},
                    {'nom': 'Épicerie salée', 'ordre': 4},
                    {'nom': 'Épicerie sucrée', 'ordre': 5},
                    {'nom': 'Boulangerie et pâtisserie', 'ordre': 6},
                    {'nom': 'Surgelés', 'ordre': 7},
                    {'nom': 'Conserves', 'ordre': 8},
                ]
            },
            {
                'nom': 'Boissons',
                'description': 'Boissons alcoolisées et non alcoolisées',
                'ordre': 2,
                'sous_categories': [
                    {'nom': 'Eaux', 'ordre': 1},
                    {'nom': 'Sodas et boissons gazeuses', 'ordre': 2},
                    {'nom': 'Jus de fruits', 'ordre': 3},
                    {'nom': 'Boissons chaudes', 'ordre': 4},
                    {'nom': 'Vins et spiritueux', 'ordre': 5},
                    {'nom': 'Bières', 'ordre': 6},
                ]
            },
            {
                'nom': 'Hygiène et beauté',
                'description': 'Produits d\'hygiène et de beauté',
                'ordre': 3,
                'sous_categories': [
                    {'nom': 'Soins du corps', 'ordre': 1},
                    {'nom': 'Soins du visage', 'ordre': 2},
                    {'nom': 'Soins des cheveux', 'ordre': 3},
                    {'nom': 'Hygiène bucco-dentaire', 'ordre': 4},
                    {'nom': 'Parfums', 'ordre': 5},
                    {'nom': 'Produits pour bébé', 'ordre': 6},
                ]
            },
            {
                'nom': 'Entretien et nettoyage',
                'description': 'Produits d\'entretien de la maison',
                'ordre': 4,
                'sous_categories': [
                    {'nom': 'Nettoyage multi-surfaces', 'ordre': 1},
                    {'nom': 'Lessive et adoucissant', 'ordre': 2},
                    {'nom': 'Produits vaisselle', 'ordre': 3},
                    {'nom': 'Désodorisants', 'ordre': 4},
                    {'nom': 'Papiers et essuie-tout', 'ordre': 5},
                ]
            },
            {
                'nom': 'Bébé et enfant',
                'description': 'Produits pour bébés et enfants',
                'ordre': 5,
                'sous_categories': [
                    {'nom': 'Alimentation bébé', 'ordre': 1},
                    {'nom': 'Couches et changes', 'ordre': 2},
                    {'nom': 'Soins bébé', 'ordre': 3},
                    {'nom': 'Accessoires bébé', 'ordre': 4},
                ]
            },
            {
                'nom': 'Animalerie',
                'description': 'Produits pour animaux de compagnie',
                'ordre': 6,
                'sous_categories': [
                    {'nom': 'Alimentation chien', 'ordre': 1},
                    {'nom': 'Alimentation chat', 'ordre': 2},
                    {'nom': 'Accessoires animaux', 'ordre': 3},
                    {'nom': 'Hygiène animaux', 'ordre': 4},
                ]
            },
            {
                'nom': 'Bio et équitable',
                'description': 'Produits biologiques et équitables',
                'ordre': 7,
                'sous_categories': [
                    {'nom': 'Alimentation bio', 'ordre': 1},
                    {'nom': 'Cosmétiques bio', 'ordre': 2},
                    {'nom': 'Produits équitables', 'ordre': 3},
                ]
            },
        ]
        
        # Supprimer uniquement les catégories non utilisées si demandé
        if clear:
            from apps.produits.models import Produit
            # Récupérer les IDs des catégories utilisées
            used_cat_ids = Produit.objects.values_list('categorie_id', flat=True).distinct()
            # Supprimer uniquement les catégories non utilisées
            unused = Categorie.objects.exclude(id__in=used_cat_ids)
            count = unused.count()
            unused.delete()
            self.stdout.write(
                self.style.WARNING(
                    f'Suppression de {count} catégories non utilisées '
                    f'({Categorie.objects.count()} catégories conservées car utilisées)'
                )
            )
        
        # Vérifier si des catégories existent déjà
        existing_count = Categorie.objects.count()
        if existing_count > 0 and not force and not clear:
            self.stdout.write(
                self.style.WARNING(
                    f'Il existe déjà {existing_count} catégories. '
                    'Utilisez --force pour forcer la création ou --clear pour tout supprimer.'
                )
            )
            return
        
        # Créer les catégories
        created_count = 0
        for cat_data in categories_data:
            # Créer la catégorie parente
            parent, created = Categorie.objects.get_or_create(
                slug=slugify(cat_data['nom']),
                defaults={
                    'nom': cat_data['nom'],
                    'description': cat_data.get('description', ''),
                    'ordre': cat_data['ordre'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Catégorie créée: {parent.nom}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'→ Catégorie existante: {parent.nom}')
                )
            
            # Créer les sous-catégories
            for subcat_data in cat_data.get('sous_categories', []):
                subcat, sub_created = Categorie.objects.get_or_create(
                    slug=slugify(subcat_data['nom']),
                    defaults={
                        'nom': subcat_data['nom'],
                        'parent': parent,
                        'ordre': subcat_data['ordre'],
                    }
                )
                
                if sub_created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  └─ Sous-catégorie créée: {subcat.nom}')
                    )
                else:
                    # Mettre à jour le parent si nécessaire
                    if subcat.parent != parent:
                        subcat.parent = parent
                        subcat.save()
                        self.stdout.write(
                            self.style.WARNING(f'  └─ Sous-catégorie mise à jour: {subcat.nom}')
                        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Initialisation terminée: {created_count} catégorie(s) créée(s)'
            )
        )
        self.stdout.write(
            f'Total de catégories dans la base: {Categorie.objects.count()}'
        )

