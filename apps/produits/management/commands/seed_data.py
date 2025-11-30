"""
Commande Django pour remplir la base de données avec des données de test.

Usage:
    python manage.py seed_data
    python manage.py seed_data --produits 50 --magasins 10
    python manage.py seed_data --clear
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta

from apps.produits.models import (
    Categorie, Marque, UniteMesure, Produit, Prix
)
from apps.magasins.models import Magasin, Ville, Region


class Command(BaseCommand):
    help = "Remplit la base de données avec des données de test"

    def add_arguments(self, parser):
        parser.add_argument(
            '--produits',
            type=int,
            default=100,
            help='Nombre de produits à créer (défaut: 100)'
        )
        parser.add_argument(
            '--magasins',
            type=int,
            default=5,
            help='Nombre de magasins à créer (défaut: 5)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer toutes les données existantes avant de créer'
        )
        parser.add_argument(
            '--prix-par-produit',
            type=int,
            default=3,
            help='Nombre de prix à créer par produit (défaut: 3)'
        )
        parser.add_argument(
            '--skip-elasticsearch',
            action='store_true',
            help='Désactiver l\'indexation Elasticsearch pendant le seed (utile si ES n\'est pas disponible)'
        )

    def handle(self, *args, **options):
        nb_produits = options['produits']
        nb_magasins = options['magasins']
        clear = options['clear']
        prix_par_produit = options['prix_par_produit']
        skip_elasticsearch = options.get('skip_elasticsearch', False)
        
        # Désactiver temporairement l'indexation Elasticsearch si demandé
        original_env_value = None
        if skip_elasticsearch:
            import os
            original_env_value = os.environ.get('SEARCH_INDEX_ENABLED')
            os.environ['SEARCH_INDEX_ENABLED'] = 'false'
            self.stdout.write(self.style.WARNING('⚠️  Indexation Elasticsearch désactivée pendant le seed'))
        
        try:
            self.stdout.write(self.style.SUCCESS('🌱 Démarrage du seed de données...'))
        
        if clear:
            self.stdout.write(self.style.WARNING('⚠️  Suppression des données existantes...'))
            Prix.objects.all().delete()
            Produit.objects.all().delete()
            Magasin.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ Données supprimées'))
        
        with transaction.atomic():
            # 1. Créer les catégories si elles n'existent pas
            categories = self.create_categories()
            self.stdout.write(self.style.SUCCESS(f'✓ {len(categories)} catégories disponibles'))
            
            # 2. Créer les marques si elles n'existent pas
            marques = self.create_marques()
            self.stdout.write(self.style.SUCCESS(f'✓ {len(marques)} marques disponibles'))
            
            # 3. Créer les unités de mesure si elles n'existent pas
            unites = self.create_unites_mesure()
            self.stdout.write(self.style.SUCCESS(f'✓ {len(unites)} unités de mesure disponibles'))
            
            # 4. Créer une ville si elle n'existe pas
            ville = self.create_ville()
            self.stdout.write(self.style.SUCCESS(f'✓ Ville créée/récupérée: {ville.nom}'))
            
            # 5. Créer les magasins
            magasins = self.create_magasins(nb_magasins, ville)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(magasins)} magasins créés'))
            
            # 6. Récupérer ou créer les produits (priorité aux produits scrappés)
            produits = self.get_or_create_produits(nb_produits, categories, marques, unites)
            self.stdout.write(self.style.SUCCESS(f'✓ {len(produits)} produits disponibles'))
            
            # 7. Créer les prix pour les produits
            prix_crees = self.create_prix(produits, magasins, prix_par_produit)
            self.stdout.write(self.style.SUCCESS(f'✓ {prix_crees} prix créés'))
        
            self.stdout.write(self.style.SUCCESS('\n✅ Seed terminé avec succès!'))
            self.stdout.write(self.style.SUCCESS(f'📊 Résumé:'))
            self.stdout.write(self.style.SUCCESS(f'   - Catégories: {Categorie.objects.count()}'))
            self.stdout.write(self.style.SUCCESS(f'   - Marques: {Marque.objects.count()}'))
            self.stdout.write(self.style.SUCCESS(f'   - Magasins: {Magasin.objects.count()}'))
            self.stdout.write(self.style.SUCCESS(f'   - Produits: {Produit.objects.count()}'))
            self.stdout.write(self.style.SUCCESS(f'   - Prix: {Prix.objects.count()}'))
        finally:
            # Restaurer la valeur originale de SEARCH_INDEX_ENABLED
            if skip_elasticsearch:
                import os
                if original_env_value is not None:
                    os.environ['SEARCH_INDEX_ENABLED'] = original_env_value
                elif 'SEARCH_INDEX_ENABLED' in os.environ:
                    del os.environ['SEARCH_INDEX_ENABLED']
                self.stdout.write(self.style.SUCCESS('✓ Indexation Elasticsearch réactivée'))
    
    def create_categories(self):
        """Crée les catégories de base si elles n'existent pas"""
        categories_data = [
            {'nom': 'Alimentation', 'description': 'Produits alimentaires'},
            {'nom': 'Boissons', 'description': 'Boissons et jus'},
            {'nom': 'Hygiène', 'description': 'Produits d\'hygiène et beauté'},
            {'nom': 'Entretien', 'description': 'Produits d\'entretien'},
            {'nom': 'Électronique', 'description': 'Appareils électroniques'},
        ]
        
        categories = []
        for cat_data in categories_data:
            cat, created = Categorie.objects.get_or_create(
                slug=slugify(cat_data['nom']),
                defaults={
                    'nom': cat_data['nom'],
                    'description': cat_data['description'],
                }
            )
            categories.append(cat)
        
        return categories
    
    def create_marques(self):
        """Crée les marques de base si elles n'existent pas"""
        marques_noms = [
            'Coca-Cola', 'Pepsi', 'Nestlé', 'Danone', 'Candia',
            'Dove', 'Nivea', 'Garnier', 'L\'Oréal', 'Head & Shoulders',
            'Ariel', 'Persil', 'Skip', 'Mr. Propre', 'Ajax',
            'Samsung', 'LG', 'Sony', 'Panasonic', 'Philips',
        ]
        
        marques = []
        for nom in marques_noms:
            marque, created = Marque.objects.get_or_create(
                slug=slugify(nom),
                defaults={'nom': nom}
            )
            marques.append(marque)
        
        return marques
    
    def create_unites_mesure(self):
        """Crée les unités de mesure de base si elles n'existent pas"""
        unites_data = [
            {'nom': 'Kilogramme', 'symbole': 'kg'},
            {'nom': 'Gramme', 'symbole': 'g'},
            {'nom': 'Litre', 'symbole': 'L'},
            {'nom': 'Millilitre', 'symbole': 'ml'},
            {'nom': 'Unité', 'symbole': 'unité'},
        ]
        
        unites = []
        for unite_data in unites_data:
            # Utiliser nom comme clé de recherche (contrainte unique sur nom)
            unite, created = UniteMesure.objects.get_or_create(
                nom=unite_data['nom'],
                defaults={'symbole': unite_data['symbole']}
            )
            unites.append(unite)
        
        return unites
    
    def create_ville(self):
        """Crée une ville de test si elle n'existe pas"""
        # Créer ou récupérer la région d'abord
        region, _ = Region.objects.get_or_create(
            nom='Estuaire',
            defaults={}
        )
        
        # Créer ou récupérer la ville
        ville, created = Ville.objects.get_or_create(
            nom='Libreville',
            region=region,
            defaults={}
        )
        return ville
    
    def create_magasins(self, nb_magasins, ville):
        """Crée des magasins de test"""
        magasins_noms = [
            'Super Marché Central', 'Marché du Centre', 'Super U',
            'Carrefour Market', 'Intermarché', 'Leclerc',
            'Casino', 'Monoprix', 'Franprix', 'Simply Market',
        ]
        
        # Types de magasins disponibles
        types_magasins = ['supermarche', 'marche', 'boutique', 'en_ligne']
        
        magasins = []
        for i in range(nb_magasins):
            nom = magasins_noms[i % len(magasins_noms)]
            if nb_magasins > len(magasins_noms):
                nom = f"{nom} {i // len(magasins_noms) + 1}"
            
            # Générer un slug unique
            base_slug = slugify(nom)
            slug = base_slug
            counter = 1
            while Magasin.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            magasin, created = Magasin.objects.get_or_create(
                slug=slug,
                defaults={
                    'nom': nom,
                    'adresse': f'Rue {i+1}, Libreville',
                    'type': types_magasins[i % len(types_magasins)],
                    'ville': ville,
                    'actif': True,
                }
            )
            magasins.append(magasin)
        
        return magasins
    
    def get_or_create_produits(self, nb_produits, categories, marques, unites):
        """Récupère les produits scrappés existants ou crée des produits de test"""
        # D'abord, récupérer les produits existants (scrappés)
        produits_existants = list(Produit.objects.filter(est_actif=True)[:nb_produits])
        
        self.stdout.write(self.style.NOTICE(f'📦 Produits existants trouvés: {len(produits_existants)}'))
        
        # Si on n'a pas assez de produits, créer des produits de test
        if len(produits_existants) < nb_produits:
            nb_a_creer = nb_produits - len(produits_existants)
            self.stdout.write(self.style.NOTICE(f'➕ Création de {nb_a_creer} produits supplémentaires...'))
            produits_crees = self.create_produits(nb_a_creer, categories, marques, unites)
            produits_existants.extend(produits_crees)
        
        return produits_existants[:nb_produits]
    
    def create_produits(self, nb_produits, categories, marques, unites):
        """Crée des produits de test"""
        produits_noms = [
            'Riz', 'Sucre', 'Farine', 'Huile', 'Pâtes',
            'Lait', 'Yaourt', 'Fromage', 'Beurre', 'Œufs',
            'Pain', 'Biscuits', 'Chocolat', 'Café', 'Thé',
            'Jus d\'orange', 'Soda', 'Eau minérale', 'Limonade', 'Sirop',
            'Shampooing', 'Savon', 'Dentifrice', 'Déodorant', 'Crème',
            'Lessive', 'Détergent', 'Eau de javel', 'Nettoyant', 'Balai',
        ]
        
        produits = []
        for i in range(nb_produits):
            nom_base = produits_noms[i % len(produits_noms)]
            marque = random.choice(marques)
            nom = f"{marque.nom} {nom_base}"
            
            # Générer un code-barres unique
            code_barre = f"{random.randint(1000000000000, 9999999999999)}"
            
            # Vérifier que le code-barres n'existe pas déjà
            while Produit.objects.filter(code_barre=code_barre).exists():
                code_barre = f"{random.randint(1000000000000, 9999999999999)}"
            
            produit, created = Produit.objects.get_or_create(
                code_barre=code_barre,
                defaults={
                    'nom': nom,
                    'slug': slugify(f"{nom}-{i}"),
                    'categorie': random.choice(categories),
                    'marque': marque,
                    'unite_mesure': random.choice(unites),
                    'quantite_unite': Decimal(str(random.choice([0.5, 1, 1.5, 2, 2.5]))),
                    'description': f'Description du produit {nom}',
                    'est_actif': True,
                }
            )
            produits.append(produit)
        
        return produits
    
    def create_prix(self, produits, magasins, prix_par_produit):
        """Crée des prix pour les produits"""
        prix_crees = 0
        
        for produit in produits:
            # Sélectionner aléatoirement des magasins pour ce produit
            magasins_produit = random.sample(magasins, min(prix_par_produit, len(magasins)))
            
            # Prix de base selon la catégorie
            prix_base = Decimal(str(random.randint(500, 10000)))  # 500 à 10000 FCFA
            
            for magasin in magasins_produit:
                # Variation de prix entre magasins (±20%)
                variation = Decimal(str(random.uniform(0.8, 1.2)))
                prix_actuel = (prix_base * variation).quantize(Decimal('0.01'))
                
                prix, created = Prix.objects.get_or_create(
                    produit=produit,
                    magasin=magasin,
                    defaults={
                        'prix_actuel': prix_actuel,
                        'prix_origine': prix_actuel,  # Utiliser prix_origine au lieu de prix_initial
                        'est_disponible': True,
                        'confiance_prix': Decimal(str(random.choice([0.8, 0.9, 0.95, 1.0]))),
                    }
                )
                
                if created:
                    prix_crees += 1
        
        return prix_crees

