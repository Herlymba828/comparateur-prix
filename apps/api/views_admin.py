"""
Vues admin temporaires pour la gestion de la base de données
À utiliser uniquement en développement ou pour le setup initial
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from datetime import datetime
import random

from apps.produits.models import Produit, Categorie, Prix, Marque, UniteMesure
from apps.magasins.models import Magasin, Ville, Region

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAdminUser])
def populate_database(request):
    """
    Peuple la base de données avec des données de test
    Nécessite d'être authentifié en tant qu'admin
    """
    try:
        with transaction.atomic():
            # Créer les régions et villes
            region, _ = Region.objects.get_or_create(nom="Île-de-France")
            
            villes_data = ["Paris", "Versailles", "Nanterre", "Créteil"]
            villes = []
            for nom in villes_data:
                ville, _ = Ville.objects.get_or_create(nom=nom, region=region)
                villes.append(ville)
            
            # Créer les magasins
            from django.utils.text import slugify
            enseignes = [
                "Carrefour", "Auchan", "Leclerc", "Intermarché", "Super U",
                "Monoprix", "Franprix", "Lidl", "Aldi", "Leader Price"
            ]
            
            magasins = []
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
                        magasins.append(magasin)
            
            # Créer les catégories
            categories_data = {
                "Alimentation": ["Fruits et Légumes", "Viandes et Poissons", "Produits Laitiers", "Épicerie Salée", "Épicerie Sucrée", "Boissons"],
                "Hygiène et Beauté": ["Soins du Corps", "Soins du Visage", "Hygiène Bucco-dentaire"],
                "Entretien": ["Lessive et Entretien du Linge", "Nettoyage de la Maison", "Vaisselle"],
            }
            
            categories = []
            for parent_nom, sous_cats in categories_data.items():
                parent, _ = Categorie.objects.get_or_create(
                    nom=parent_nom,
                    defaults={'slug': slugify(parent_nom), 'description': f"Catégorie {parent_nom}"}
                )
                categories.append(parent)
                
                for sous_cat_nom in sous_cats:
                    sous_cat, _ = Categorie.objects.get_or_create(
                        nom=sous_cat_nom,
                        parent=parent,
                        defaults={'slug': slugify(sous_cat_nom), 'description': f"Sous-catégorie {sous_cat_nom}"}
                    )
                    categories.append(sous_cat)
            
            # Créer les marques
            marques_data = ["Danone", "Nestlé", "Coca-Cola", "Pepsi", "Ferrero", "Unilever", "L'Oréal", 
                           "Carrefour", "Auchan", "U", "Leclerc", "Président", "Yoplait", "Lu"]
            
            marques = []
            for nom in marques_data:
                marque, _ = Marque.objects.get_or_create(
                    nom=nom,
                    defaults={'slug': slugify(nom), 'description': f"Marque {nom}"}
                )
                marques.append(marque)
            
            # Créer les unités de mesure
            unites_data = [("Kilogramme", "kg"), ("Gramme", "g"), ("Litre", "L"), ("Millilitre", "mL"), ("Unité", "u")]
            
            unites = []
            for nom, symbole in unites_data:
                unite, _ = UniteMesure.objects.get_or_create(nom=nom, symbole=symbole)
                unites.append(unite)
            
            # Créer les produits
            produits_data = [
                ("Pommes Golden", "Fruits et Légumes", "Carrefour", 1.0, "kg"),
                ("Bananes", "Fruits et Légumes", "Auchan", 1.0, "kg"),
                ("Lait Demi-Écrémé", "Produits Laitiers", "Président", 1.0, "L"),
                ("Yaourt Nature", "Produits Laitiers", "Danone", 1.0, "kg"),
                ("Pâtes Spaghetti", "Épicerie Salée", "Carrefour", 500.0, "g"),
                ("Riz Basmati", "Épicerie Salée", "U", 1.0, "kg"),
                ("Sucre Blanc", "Épicerie Sucrée", "Carrefour", 1.0, "kg"),
                ("Chocolat au Lait", "Épicerie Sucrée", "Nestlé", 200.0, "g"),
                ("Eau Minérale", "Boissons", "Carrefour", 1.5, "L"),
                ("Coca-Cola", "Boissons", "Coca-Cola", 1.5, "L"),
            ]
            
            produits = []
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
                        produits.append(produit)
            
            # Créer les prix
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
        
        # Compter les résultats
        return Response({
            'status': 'success',
            'message': 'Base de données peuplée avec succès',
            'data': {
                'regions': Region.objects.count(),
                'villes': Ville.objects.count(),
                'magasins': Magasin.objects.count(),
                'categories': Categorie.objects.count(),
                'marques': Marque.objects.count(),
                'produits': Produit.objects.count(),
                'prix': Prix.objects.count(),
                'utilisateurs': User.objects.count(),
            }
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reset_database(request):
    """
    Supprime toutes les données de produits/magasins/prix
    Nécessite d'être authentifié en tant qu'admin
    """
    try:
        with transaction.atomic():
            Prix.objects.all().delete()
            Produit.objects.all().delete()
            Marque.objects.all().delete()
            Categorie.objects.all().delete()
            UniteMesure.objects.all().delete()
            Magasin.objects.all().delete()
            Ville.objects.all().delete()
            Region.objects.all().delete()
        
        return Response({
            'status': 'success',
            'message': 'Base de données réinitialisée avec succès'
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def database_stats(request):
    """
    Retourne les statistiques de la base de données
    Accessible sans authentification
    """
    return Response({
        'status': 'success',
        'data': {
            'regions': Region.objects.count(),
            'villes': Ville.objects.count(),
            'magasins': Magasin.objects.count(),
            'categories': Categorie.objects.count(),
            'marques': Marque.objects.count(),
            'produits': Produit.objects.count(),
            'prix': Prix.objects.count(),
            'utilisateurs': User.objects.count(),
        }
    })
