"""
Management command pour peupler la base de données
Usage: python manage.py populate_db
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify
from decimal import Decimal
import random

from apps.produits.models import Produit, Categorie, Prix, Marque, UniteMesure
from apps.magasins.models import Magasin, Ville, Region


class Command(BaseCommand):
    help = 'Peuple la base de données avec des données de test'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Peuplement de la base de données...\n')
        
        try:
            with transaction.atomic():
                # Régions et villes
                self.stdout.write('🌍 Création des régions et villes...')
                region, _ = Region.objects.get_or_create(nom="Île-de-France")
                
                villes_data = ["Paris", "Versailles", "Nanterre", "Créteil"]
                villes = []
                for nom in villes_data:
                    ville, _ = Ville.objects.get_or_create(nom=nom, region=region)
                    villes.append(ville)
                
                self.stdout.write(f'   ✅ {len(villes)} villes créées')
                
                # Magasins
                self.stdout.write('🏪 Création des magasins...')
                enseignes = ["Carrefour", "Auchan", "Leclerc", "Intermarché", "Super U",
                            "Monoprix", "Franprix", "Lidl", "Aldi", "Leader Price"]
                
                magasins_count = 0
                for enseigne in enseignes:
                    for ville in villes[:3]:
                        nom_magasin = f"{enseigne} {ville.nom}"
                        magasin, created = Magasin.objects.get_or_create(
                            nom=nom_magasin,
                            ville=ville,
                            defaults={
                                'slug': slugify(nom_magasin),
                                'adresse': f"123 Avenue de {ville.nom}",
                                'latitude': 48.8566 + random.uniform(-0.1, 0.1),
                                'longitude': 2.3522 + random.uniform(-0.1, 0.1),
                                'type': 'supermarche',
                                'type_magasin': 'supermarche',
                                'actif': True,
                            }
                        )
                        if created:
                            magasins_count += 1
                
                self.stdout.write(f'   ✅ {magasins_count} magasins créés')
                
                # Catégories
                self.stdout.write('📂 Création des catégories...')
                categories_data = {
                    "Alimentation": ["Fruits et Légumes", "Viandes et Poissons", "Produits Laitiers", 
                                    "Épicerie Salée", "Épicerie Sucrée", "Boissons"],
                    "Hygiène et Beauté": ["Soins du Corps", "Soins du Visage", "Hygiène Bucco-dentaire"],
                    "Entretien": ["Lessive et Entretien du Linge", "Nettoyage de la Maison", "Vaisselle"],
                }
                
                categories_count = 0
                for parent_nom, sous_cats in categories_data.items():
                    parent, created = Categorie.objects.get_or_create(
                        nom=parent_nom,
                        defaults={'slug': slugify(parent_nom), 'description': f"Catégorie {parent_nom}"}
                    )
                    if created:
                        categories_count += 1
                    
                    for sous_cat_nom in sous_cats:
                        sous_cat, created = Categorie.objects.get_or_create(
                            nom=sous_cat_nom,
                            parent=parent,
                            defaults={'slug': slugify(sous_cat_nom), 'description': f"Sous-catégorie {sous_cat_nom}"}
                        )
                        if created:
                            categories_count += 1
                
                self.stdout.write(f'   ✅ {categories_count} catégories créées')
                
                # Marques
                self.stdout.write('🏷️  Création des marques...')
                marques_data = ["Danone", "Nestlé", "Coca-Cola", "Pepsi", "Ferrero", "Unilever", 
                               "L'Oréal", "Carrefour", "Auchan", "U", "Leclerc", "Président", "Yoplait", "Lu"]
                
                marques_count = 0
                for nom in marques_data:
                    marque, created = Marque.objects.get_or_create(
                        nom=nom,
                        defaults={'slug': slugify(nom), 'description': f"Marque {nom}"}
                    )
                    if created:
                        marques_count += 1
                
                self.stdout.write(f'   ✅ {marques_count} marques créées')
                
                # Unités de mesure
                self.stdout.write('📏 Création des unités de mesure...')
                unites_data = [("Kilogramme", "kg"), ("Gramme", "g"), ("Litre", "L"), 
                              ("Millilitre", "mL"), ("Unité", "u")]
                
                unites_count = 0
                for nom, symbole in unites_data:
                    unite, created = UniteMesure.objects.get_or_create(nom=nom, symbole=symbole)
                    if created:
                        unites_count += 1
                
                self.stdout.write(f'   ✅ {unites_count} unités créées')
                
                # Produits
                self.stdout.write('📦 Création des produits...')
                produits_data = [
                    ("Pommes Golden", "Fruits et Légumes", "Carrefour", 1.0, "kg"),
                    ("Bananes", "Fruits et Légumes", "Auchan", 1.0, "kg"),
                    ("Tomates", "Fruits et Légumes", "Leclerc", 1.0, "kg"),
                    ("Lait Demi-Écrémé", "Produits Laitiers", "Président", 1.0, "L"),
                    ("Yaourt Nature", "Produits Laitiers", "Danone", 1.0, "kg"),
                    ("Beurre Doux", "Produits Laitiers", "Président", 250.0, "g"),
                    ("Pâtes Spaghetti", "Épicerie Salée", "Carrefour", 500.0, "g"),
                    ("Riz Basmati", "Épicerie Salée", "U", 1.0, "kg"),
                    ("Sucre Blanc", "Épicerie Sucrée", "Carrefour", 1.0, "kg"),
                    ("Chocolat au Lait", "Épicerie Sucrée", "Nestlé", 200.0, "g"),
                    ("Eau Minérale", "Boissons", "Carrefour", 1.5, "L"),
                    ("Coca-Cola", "Boissons", "Coca-Cola", 1.5, "L"),
                ]
                
                produits_count = 0
                for nom, cat_nom, marque_nom, quantite, unite_sym in produits_data:
                    categorie = Categorie.objects.filter(nom=cat_nom).first()
                    marque = Marque.objects.filter(nom=marque_nom).first()
                    unite = UniteMesure.objects.filter(symbole=unite_sym).first()
                    
                    if categorie and marque and unite:
                        produit, created = Produit.objects.get_or_create(
                            nom=nom,
                            defaults={
                                'slug': slugify(nom),
                                'description': f"Description de {nom}",
                                'categorie': categorie,
                                'marque': marque,
                                'code_barre': f"3{random.randint(100000000000, 999999999999)}",
                                'quantite_unite': quantite,
                                'unite_mesure': unite,
                                'est_actif': True,
                            }
                        )
                        if created:
                            produits_count += 1
                
                self.stdout.write(f'   ✅ {produits_count} produits créés')
                
                # Prix
                self.stdout.write('💰 Création des prix...')
                prix_count = 0
                all_magasins = list(Magasin.objects.all())
                for produit in Produit.objects.all():
                    prix_base = Decimal(random.uniform(2.0, 15.0))
                    
                    for magasin in random.sample(all_magasins, min(len(all_magasins), 8)):
                        variation = Decimal(random.uniform(0.9, 1.1))
                        prix_actuel = (prix_base * variation).quantize(Decimal('0.01'))
                        
                        prix, created = Prix.objects.get_or_create(
                            produit=produit,
                            magasin=magasin,
                            defaults={
                                'prix_actuel': prix_actuel,
                                'est_disponible': True,
                            }
                        )
                        if created:
                            prix_count += 1
                
                self.stdout.write(f'   ✅ {prix_count} prix créés')
            
            # Résumé
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('✅ PEUPLEMENT TERMINÉ AVEC SUCCÈS !'))
            self.stdout.write('='*60)
            self.stdout.write(f'\n📊 Données en base :')
            self.stdout.write(f'   - Régions : {Region.objects.count()}')
            self.stdout.write(f'   - Villes : {Ville.objects.count()}')
            self.stdout.write(f'   - Magasins : {Magasin.objects.count()}')
            self.stdout.write(f'   - Catégories : {Categorie.objects.count()}')
            self.stdout.write(f'   - Marques : {Marque.objects.count()}')
            self.stdout.write(f'   - Produits : {Produit.objects.count()}')
            self.stdout.write(f'   - Prix : {Prix.objects.count()}')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ ERREUR : {e}'))
            raise
