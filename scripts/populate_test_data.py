#!/usr/bin/env python
"""
Script pour peupler la base avec des données de test réalistes
Usage: railway run python scripts/populate_test_data.py
"""
import os
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta
import random

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from apps.produits.models import Produit, Categorie, Prix, Marque, UniteMesure
from apps.magasins.models import Magasin, Ville, Region
from django.contrib.auth import get_user_model

User = get_user_model()

def create_regions_and_cities():
    """Crée les régions et villes."""
    print("🌍 Création des régions et villes...")
    
    region, _ = Region.objects.get_or_create(
        nom="Île-de-France"
    )
    
    villes_data = ["Paris", "Versailles", "Nanterre", "Créteil"]
    
    villes = []
    for nom in villes_data:
        ville, _ = Ville.objects.get_or_create(
            nom=nom,
            region=region
        )
        villes.append(ville)
    
    print(f"   ✅ {len(villes)} villes créées")
    return villes

def create_stores(villes):
    """Crée les magasins."""
    print("🏪 Création des magasins...")
    
    enseignes = [
        ("Carrefour", "Hypermarché"),
        ("Auchan", "Hypermarché"),
        ("Leclerc", "Hypermarché"),
        ("Intermarché", "Supermarché"),
        ("Super U", "Supermarché"),
        ("Monoprix", "Supermarché"),
        ("Franprix", "Supermarché"),
        ("Lidl", "Discount"),
        ("Aldi", "Discount"),
        ("Leader Price", "Discount"),
    ]
    
    magasins = []
    for enseigne, type_mag in enseignes:
        for ville in villes[:3]:  # 3 premières villes
            from django.utils.text import slugify
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
                magasins.append(magasin)
    
    print(f"   ✅ {len(magasins)} magasins créés")
    return magasins

def create_categories():
    """Crée les catégories de produits."""
    print("📂 Création des catégories...")
    
    categories_data = {
        "Alimentation": [
            "Fruits et Légumes",
            "Viandes et Poissons",
            "Produits Laitiers",
            "Épicerie Salée",
            "Épicerie Sucrée",
            "Boissons",
            "Surgelés",
        ],
        "Hygiène et Beauté": [
            "Soins du Corps",
            "Soins du Visage",
            "Hygiène Bucco-dentaire",
            "Parfums",
        ],
        "Entretien": [
            "Lessive et Entretien du Linge",
            "Nettoyage de la Maison",
            "Vaisselle",
        ],
        "Bébé": [
            "Couches et Changes",
            "Alimentation Bébé",
            "Soins Bébé",
        ],
    }
    
    from django.utils.text import slugify
    
    categories = []
    for parent_nom, sous_cats in categories_data.items():
        parent, _ = Categorie.objects.get_or_create(
            nom=parent_nom,
            defaults={
                'slug': slugify(parent_nom),
                'description': f"Catégorie {parent_nom}"
            }
        )
        categories.append(parent)
        
        for sous_cat_nom in sous_cats:
            sous_cat, _ = Categorie.objects.get_or_create(
                nom=sous_cat_nom,
                parent=parent,
                defaults={
                    'slug': slugify(sous_cat_nom),
                    'description': f"Sous-catégorie {sous_cat_nom}"
                }
            )
            categories.append(sous_cat)
    
    print(f"   ✅ {len(categories)} catégories créées")
    return categories

def create_brands():
    """Crée les marques."""
    print("🏷️  Création des marques...")
    
    marques_data = [
        "Danone", "Nestlé", "Coca-Cola", "Pepsi", "Ferrero",
        "Unilever", "L'Oréal", "Procter & Gamble", "Henkel",
        "Carrefour", "Auchan", "U", "Leclerc", "Intermarché",
        "Président", "Yoplait", "Lu", "Bonne Maman", "Herta",
        "Fleury Michon", "Bonduelle", "Cassegrain", "Amora",
    ]
    
    from django.utils.text import slugify
    
    marques = []
    for nom in marques_data:
        marque, _ = Marque.objects.get_or_create(
            nom=nom,
            defaults={
                'slug': slugify(nom),
                'description': f"Marque {nom}"
            }
        )
        marques.append(marque)
    
    print(f"   ✅ {len(marques)} marques créées")
    return marques

def create_units():
    """Crée les unités de mesure."""
    print("📏 Création des unités de mesure...")
    
    unites_data = [
        ("Kilogramme", "kg"),
        ("Gramme", "g"),
        ("Litre", "L"),
        ("Millilitre", "mL"),
        ("Unité", "u"),
        ("Paquet", "pqt"),
        ("Boîte", "bte"),
    ]
    
    unites = []
    for nom, symbole in unites_data:
        unite, _ = UniteMesure.objects.get_or_create(
            nom=nom,
            symbole=symbole
        )
        unites.append(unite)
    
    print(f"   ✅ {len(unites)} unités créées")
    return unites

def create_products(categories, marques, unites):
    """Crée les produits."""
    print("📦 Création des produits...")
    
    produits_data = [
        # Fruits et Légumes
        ("Pommes Golden", "Fruits et Légumes", "Carrefour", 1.0, "kg", "Pommes Golden de qualité"),
        ("Bananes", "Fruits et Légumes", "Auchan", 1.0, "kg", "Bananes fraîches"),
        ("Tomates", "Fruits et Légumes", "Leclerc", 1.0, "kg", "Tomates rondes"),
        ("Carottes", "Fruits et Légumes", "Intermarché", 1.0, "kg", "Carottes fraîches"),
        
        # Produits Laitiers
        ("Lait Demi-Écrémé", "Produits Laitiers", "Président", 1.0, "L", "Lait demi-écrémé UHT"),
        ("Yaourt Nature", "Produits Laitiers", "Danone", 1.0, "kg", "Pack de 12 yaourts nature"),
        ("Beurre Doux", "Produits Laitiers", "Président", 250.0, "g", "Beurre doux de baratte"),
        ("Fromage Emmental", "Produits Laitiers", "Président", 200.0, "g", "Emmental râpé"),
        
        # Épicerie Salée
        ("Pâtes Spaghetti", "Épicerie Salée", "Carrefour", 500.0, "g", "Pâtes spaghetti"),
        ("Riz Basmati", "Épicerie Salée", "U", 1.0, "kg", "Riz basmati"),
        ("Huile d'Olive", "Épicerie Salée", "Carrefour", 1.0, "L", "Huile d'olive vierge extra"),
        ("Sel Fin", "Épicerie Salée", "Carrefour", 1.0, "kg", "Sel fin de cuisine"),
        
        # Épicerie Sucrée
        ("Sucre Blanc", "Épicerie Sucrée", "Daddy", 1.0, "kg", "Sucre blanc cristallisé"),
        ("Confiture Fraise", "Épicerie Sucrée", "Bonne Maman", 370.0, "g", "Confiture de fraises"),
        ("Chocolat au Lait", "Épicerie Sucrée", "Nestlé", 200.0, "g", "Tablette chocolat au lait"),
        ("Biscuits Petit Beurre", "Épicerie Sucrée", "Lu", 400.0, "g", "Biscuits petit beurre"),
        
        # Boissons
        ("Eau Minérale", "Boissons", "Carrefour", 1.5, "L", "Pack de 6 bouteilles"),
        ("Coca-Cola", "Boissons", "Coca-Cola", 1.5, "L", "Coca-Cola Original"),
        ("Jus d'Orange", "Boissons", "Tropicana", 1.0, "L", "Jus d'orange 100% pur jus"),
        ("Café Moulu", "Boissons", "Carte Noire", 250.0, "g", "Café moulu arabica"),
        
        # Viandes et Poissons
        ("Poulet Entier", "Viandes et Poissons", "Carrefour", 1.5, "kg", "Poulet fermier"),
        ("Steak Haché", "Viandes et Poissons", "Herta", 500.0, "g", "Steak haché 15% MG"),
        ("Saumon Fumé", "Viandes et Poissons", "Fleury Michon", 200.0, "g", "Saumon fumé Norvège"),
        
        # Hygiène
        ("Gel Douche", "Soins du Corps", "L'Oréal", 250.0, "mL", "Gel douche hydratant"),
        ("Shampoing", "Soins du Corps", "L'Oréal", 300.0, "mL", "Shampoing tous types"),
        ("Dentifrice", "Hygiène Bucco-dentaire", "Colgate", 75.0, "mL", "Dentifrice protection caries"),
        ("Savon", "Soins du Corps", "Dove", 100.0, "g", "Pain de savon"),
        
        # Entretien
        ("Lessive Liquide", "Lessive et Entretien du Linge", "Ariel", 1.5, "L", "Lessive liquide 30 lavages"),
        ("Liquide Vaisselle", "Vaisselle", "Paic", 500.0, "mL", "Liquide vaisselle citron"),
        ("Nettoyant Multi-usages", "Nettoyage de la Maison", "Cif", 750.0, "mL", "Spray nettoyant"),
        
        # Bébé
        ("Couches Taille 4", "Couches et Changes", "Pampers", 1.0, "pqt", "Pack de 50 couches"),
        ("Lait Infantile", "Alimentation Bébé", "Nestlé", 800.0, "g", "Lait 1er âge"),
    ]
    
    produits = []
    for nom, cat_nom, marque_nom, quantite, unite_sym, description in produits_data:
        categorie = Categorie.objects.filter(nom=cat_nom).first()
        marque = Marque.objects.filter(nom=marque_nom).first()
        unite = UniteMesure.objects.filter(symbole=unite_sym).first()
        
        if categorie and marque and unite:
            from django.utils.text import slugify
            produit, created = Produit.objects.get_or_create(
                nom=nom,
                defaults={
                    'slug': slugify(nom),
                    'description': description,
                    'categorie': categorie,
                    'marque': marque,
                    'code_barre': f"3{random.randint(100000000000, 999999999999)}",
                    'quantite_unite': quantite,
                    'unite_mesure': unite,
                    'est_actif': True,
                }
            )
            if created:
                produits.append(produit)
    
    print(f"   ✅ {len(produits)} produits créés")
    return produits

def create_prices(produits, magasins):
    """Crée les prix pour les produits."""
    print("💰 Création des prix...")
    
    prix_count = 0
    for produit in produits:
        # Définir un prix de base selon la catégorie
        if "Fruits et Légumes" in produit.categorie.nom:
            prix_base = Decimal(random.uniform(1.5, 4.0))
        elif "Produits Laitiers" in produit.categorie.nom:
            prix_base = Decimal(random.uniform(1.0, 5.0))
        elif "Viandes" in produit.categorie.nom:
            prix_base = Decimal(random.uniform(5.0, 15.0))
        elif "Boissons" in produit.categorie.nom:
            prix_base = Decimal(random.uniform(0.5, 3.0))
        elif "Hygiène" in produit.categorie.nom or "Soins" in produit.categorie.nom:
            prix_base = Decimal(random.uniform(2.0, 8.0))
        elif "Entretien" in produit.categorie.nom:
            prix_base = Decimal(random.uniform(2.0, 6.0))
        elif "Bébé" in produit.categorie.nom:
            prix_base = Decimal(random.uniform(5.0, 20.0))
        else:
            prix_base = Decimal(random.uniform(1.0, 10.0))
        
        # Créer des prix pour plusieurs magasins
        for magasin in random.sample(magasins, min(len(magasins), random.randint(5, 10))):
            # Variation de prix selon le type de magasin
            if "Discount" in magasin.type_magasin:
                variation = Decimal(random.uniform(0.8, 0.95))
            elif "Hypermarché" in magasin.type_magasin:
                variation = Decimal(random.uniform(0.9, 1.1))
            else:
                variation = Decimal(random.uniform(1.0, 1.2))
            
            prix_actuel = (prix_base * variation).quantize(Decimal('0.01'))
            
            prix, created = Prix.objects.get_or_create(
                produit=produit,
                magasin=magasin,
                defaults={
                    'prix_actuel': prix_actuel,
                    'prix_precedent': prix_actuel * Decimal('1.05'),
                    'est_disponible': random.choice([True, True, True, False]),  # 75% disponible
                    'date_modification': datetime.now() - timedelta(days=random.randint(0, 30)),
                }
            )
            if created:
                prix_count += 1
    
    print(f"   ✅ {prix_count} prix créés")

def show_summary():
    """Affiche un résumé des données créées."""
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES DONNÉES CRÉÉES")
    print("="*60)
    
    from apps.produits.models import Produit, Prix, Categorie, Marque
    from apps.magasins.models import Magasin, Ville, Region
    
    print(f"\n✅ Données en base :")
    print(f"   - Régions : {Region.objects.count()}")
    print(f"   - Villes : {Ville.objects.count()}")
    print(f"   - Magasins : {Magasin.objects.count()}")
    print(f"   - Catégories : {Categorie.objects.count()}")
    print(f"   - Marques : {Marque.objects.count()}")
    print(f"   - Produits : {Produit.objects.count()}")
    print(f"   - Prix : {Prix.objects.count()}")
    print(f"   - Utilisateurs : {User.objects.count()}")
    
    print(f"\n📦 Exemples de produits :")
    for p in Produit.objects.all()[:5]:
        prix_count = Prix.objects.filter(produit=p).count()
        print(f"   - {p.nom} ({prix_count} prix)")
    
    print(f"\n🏪 Exemples de magasins :")
    for m in Magasin.objects.all()[:5]:
        prix_count = Prix.objects.filter(magasin=m).count()
        print(f"   - {m.nom} ({prix_count} produits)")
    
    print("\n" + "="*60)
    print("🎉 PEUPLEMENT TERMINÉ AVEC SUCCÈS !")
    print("="*60)

def main():
    """Fonction principale."""
    print("🚀 PEUPLEMENT DE LA BASE AVEC DES DONNÉES DE TEST")
    print("="*60 + "\n")
    
    try:
        villes = create_regions_and_cities()
        magasins = create_stores(villes)
        categories = create_categories()
        marques = create_brands()
        unites = create_units()
        produits = create_products(categories, marques, unites)
        create_prices(produits, magasins)
        
        show_summary()
        
    except Exception as e:
        print(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
