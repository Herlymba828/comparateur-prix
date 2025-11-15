#!/usr/bin/env python
"""
Script de test pour valider l'extraction et la persistance des données DGCCRF.
Vérifie que toutes les informations sont correctement extraites et sauvegardées en base.
"""

import os
import sys
import json
from pathlib import Path

# Ajouter le répertoire parent au path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# Initialiser Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from scripts.scraper_dgccrf import DgccrfScraper
from apps.produits.models import Produit, Prix, Categorie, HomologationProduit, PrixHomologue, Marque
from apps.magasins.models import Magasin


def test_extraction():
    """Test l'extraction des données depuis la page."""
    print("=" * 80)
    print("TEST D'EXTRACTION DES DONNÉES")
    print("=" * 80)
    
    scraper = DgccrfScraper()
    items = []
    
    # Extraire les données
    print("\n1. Extraction des données depuis la page...")
    count = 0
    for item in scraper.iter_from_liste_produit_page():
        items.append(item)
        count += 1
        if count <= 5:  # Afficher les 5 premiers
            print(f"\n   Produit {count}:")
            print(f"   - Numéro: {item.get('numero')}")
            print(f"   - Nom: {item.get('nom')}")
            print(f"   - Catégorie: {item.get('categorie')}")
            print(f"   - Sous-catégorie: {item.get('sous_categorie')}")
            print(f"   - Prix détail: {item.get('prix_detail')} FCFA")
            print(f"   - Prix gros: {item.get('prix_gros')} FCFA")
            print(f"   - Prix demi-gros: {item.get('prix_demi_gros')} FCFA")
            print(f"   - Origine: {item.get('extra', {}).get('origine')}")
            print(f"   - Conditionnement: {item.get('extra', {}).get('conditionnement')}")
            print(f"   - Format: {item.get('format')}")
            print(f"   - Marque: {item.get('marque')}")
    
    print(f"\n✓ {count} produits extraits au total")
    
    # Vérifications
    print("\n2. Vérification de la qualité des données...")
    issues = []
    
    for i, item in enumerate(items, 1):
        if not item.get('nom'):
            issues.append(f"Produit {i}: Nom manquant")
        if not item.get('sous_categorie'):
            issues.append(f"Produit {i} ({item.get('nom')}): Sous-catégorie manquante")
        if item.get('prix_detail') is None and item.get('prix_unitaire') is None:
            issues.append(f"Produit {i} ({item.get('nom')}): Aucun prix disponible")
    
    if issues:
        print(f"⚠ {len(issues)} problèmes détectés:")
        for issue in issues[:10]:  # Afficher les 10 premiers
            print(f"   - {issue}")
    else:
        print("✓ Toutes les données semblent correctes")
    
    return items


def test_persistence(items):
    """Test la persistance des données en base."""
    print("\n" + "=" * 80)
    print("TEST DE PERSISTANCE EN BASE DE DONNÉES")
    print("=" * 80)
    
    scraper = DgccrfScraper()
    
    if not scraper._init_django():
        print("❌ Impossible d'initialiser Django")
        return False
    
    print("\n1. Sauvegarde des données...")
    created_prod, created_prix = scraper.persist_items(items)
    print(f"✓ {created_prod} produits créés")
    print(f"✓ {created_prix} prix créés")
    
    print("\n2. Vérification en base de données...")
    
    # Vérifier les produits
    produits = Produit.objects.filter(description__icontains='DGCCRF').order_by('-date_creation')[:10]
    print(f"\n   Produits récents (10 premiers):")
    for p in produits:
        print(f"   - {p.nom} (cat: {p.categorie.nom})")
    
    # Vérifier les catégories
    categories = Categorie.objects.filter(nom__icontains='défiscalisé').union(
        Categorie.objects.filter(sous_categories__isnull=False).distinct()
    )[:10]
    print(f"\n   Catégories créées ({categories.count()}):")
    for cat in categories:
        print(f"   - {cat.nom} (parent: {cat.parent.nom if cat.parent else 'Aucun'})")
    
    # Vérifier les homologations
    homologations = HomologationProduit.objects.filter(reference_titre__icontains='défiscalisé').order_by('-date_creation')[:10]
    print(f"\n   Homologations créées ({homologations.count()}):")
    for hp in homologations:
        print(f"   - {hp.nom} (sous-cat: {hp.sous_categorie})")
        prix_homologues = hp.prix_homologues.all()[:3]
        for ph in prix_homologues:
            print(f"     * Prix: {ph.prix_unitaire} FCFA (gros: {ph.prix_gros}, demi-gros: {ph.prix_demi_gros})")
    
    # Vérifier les prix
    prix_count = Prix.objects.filter(source_prix='dgccrf').count()
    print(f"\n   Prix en base: {prix_count}")
    
    # Vérifier les marques
    marques = Marque.objects.filter(produits__description__icontains='DGCCRF').distinct()[:10]
    print(f"\n   Marques créées ({marques.count()}):")
    for m in marques:
        print(f"   - {m.nom}")
    
    return True


def test_specific_fields():
    """Test des champs spécifiques."""
    print("\n" + "=" * 80)
    print("TEST DES CHAMPS SPÉCIFIQUES")
    print("=" * 80)
    
    # Vérifier que les sous-catégories sont bien créées
    print("\n1. Vérification des sous-catégories...")
    sous_cats = Categorie.objects.filter(parent__isnull=False).filter(
        nom__in=['VIANDE DE PORC', 'VIANDE DE BOEUF', 'VOLAILLE', 'POISSON']
    )
    print(f"   Sous-catégories trouvées: {sous_cats.count()}")
    for sc in sous_cats:
        print(f"   - {sc.nom} (parent: {sc.parent.nom if sc.parent else 'Aucun'})")
    
    # Vérifier que les prix gros/demi-gros sont bien sauvegardés
    print("\n2. Vérification des prix gros/demi-gros...")
    prix_with_gros = PrixHomologue.objects.filter(prix_gros__isnull=False).count()
    prix_with_demi_gros = PrixHomologue.objects.filter(prix_demi_gros__isnull=False).count()
    print(f"   Prix avec prix_gros: {prix_with_gros}")
    print(f"   Prix avec prix_demi_gros: {prix_with_demi_gros}")
    
    # Vérifier que les origines sont utilisées comme marques
    print("\n3. Vérification des origines utilisées comme marques...")
    marques_origine = Marque.objects.filter(nom__in=['USA', 'Brésil', 'ASIE', 'Afrique du Nord'])
    print(f"   Marques créées depuis origines: {marques_origine.count()}")
    for m in marques_origine:
        print(f"   - {m.nom}")
    
    # Vérifier les conditionnements
    print("\n4. Vérification des conditionnements...")
    produits_with_weight = Produit.objects.filter(poids__isnull=False, description__icontains='DGCCRF').count()
    produits_with_volume = Produit.objects.filter(volume__isnull=False, description__icontains='DGCCRF').count()
    print(f"   Produits avec poids: {produits_with_weight}")
    print(f"   Produits avec volume: {produits_with_volume}")


def main():
    """Fonction principale."""
    print("\n" + "=" * 80)
    print("SCRIPT DE VALIDATION DGCCRF")
    print("=" * 80)
    
    try:
        # Test d'extraction
        items = test_extraction()
        
        if not items:
            print("\n❌ Aucune donnée extraite. Vérifiez la connexion au site.")
            return
        
        # Test de persistance
        if test_persistence(items):
            # Test des champs spécifiques
            test_specific_fields()
            
            print("\n" + "=" * 80)
            print("✓ TOUS LES TESTS SONT TERMINÉS")
            print("=" * 80)
        else:
            print("\n❌ Échec de la persistance")
    
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

