"""
Script de diagnostic et réparation automatique du système.
Usage: python scripts/diagnostic_et_reparation.py [--fix]
"""
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection
from django.core.management import call_command
from apps.utilisateurs.models import Utilisateur
from apps.produits.models import Produit, Categorie, Marque
from apps.magasins.models import Magasin, Ville, Region

class Diagnostic:
    """Classe pour diagnostiquer et réparer le système."""
    
    def __init__(self, fix=False):
        self.fix = fix
        self.problemes = []
        self.solutions = []
    
    def verifier_connexion_db(self):
        """Vérifier la connexion à la base de données."""
        print("\n🔍 Vérification de la connexion à la base de données...")
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            print("✅ Connexion à la base de données OK")
            return True
        except Exception as e:
            print(f"❌ Erreur de connexion à la base de données: {e}")
            self.problemes.append("Connexion DB échouée")
            return False
    
    def verifier_donnees(self):
        """Vérifier la présence de données essentielles."""
        print("\n🔍 Vérification des données...")
        
        # Vérifier les produits
        nb_produits = Produit.objects.count()
        print(f"   📦 Produits: {nb_produits}")
        if nb_produits == 0:
            self.problemes.append("Aucun produit en base")
            self.solutions.append("python manage.py seed_data --produits 100")
        
        # Vérifier les catégories
        nb_categories = Categorie.objects.count()
        print(f"   📁 Catégories: {nb_categories}")
        if nb_categories == 0:
            self.problemes.append("Aucune catégorie en base")
            self.solutions.append("python manage.py init_categories")
        
        # Vérifier les magasins
        nb_magasins = Magasin.objects.count()
        print(f"   🏪 Magasins: {nb_magasins}")
        if nb_magasins == 0:
            self.problemes.append("Aucun magasin en base")
            self.solutions.append("python manage.py seed_data --magasins 10")
        
        # Vérifier les utilisateurs
        nb_users = Utilisateur.objects.count()
        print(f"   👥 Utilisateurs: {nb_users}")
        
        return len(self.problemes) == 0
    
    def verifier_emails_dupliques(self):
        """Vérifier les emails en double."""
        print("\n🔍 Vérification des emails dupliqués...")
        
        from django.db.models import Count
        
        emails_dupliques = (
            Utilisateur.objects
            .values('email')
            .annotate(count=Count('email'))
            .filter(count__gt=1)
        )
        
        if emails_dupliques.exists():
            print(f"⚠️  {emails_dupliques.count()} email(s) en double détecté(s):")
            for item in emails_dupliques:
                email = item['email']
                count = item['count']
                print(f"   - {email}: {count} comptes")
                
                if self.fix:
                    # Garder le plus ancien, supprimer les autres
                    users = Utilisateur.objects.filter(email=email).order_by('date_joined')
                    users_to_delete = users[1:]
                    nb_deleted = users_to_delete.count()
                    users_to_delete.delete()
                    print(f"   ✅ {nb_deleted} compte(s) dupliqué(s) supprimé(s)")
            
            if not self.fix:
                self.problemes.append(f"{emails_dupliques.count()} email(s) dupliqué(s)")
                self.solutions.append("Exécuter avec --fix pour nettoyer automatiquement")
        else:
            print("✅ Aucun email dupliqué")
    
    def verifier_indexes(self):
        """Vérifier les indexes de base de données."""
        print("\n🔍 Vérification des indexes...")
        
        try:
            with connection.cursor() as cursor:
                # PostgreSQL
                if 'postgresql' in connection.settings_dict['ENGINE']:
                    cursor.execute("""
                        SELECT 
                            schemaname,
                            tablename,
                            indexname
                        FROM pg_indexes
                        WHERE schemaname = 'public'
                        ORDER BY tablename, indexname;
                    """)
                    indexes = cursor.fetchall()
                    print(f"✅ {len(indexes)} index(es) trouvé(s)")
                else:
                    print("ℹ️  Vérification des indexes disponible uniquement pour PostgreSQL")
        except Exception as e:
            print(f"⚠️  Erreur lors de la vérification des indexes: {e}")
    
    def reparer_donnees(self):
        """Réparer les données manquantes."""
        if not self.fix:
            return
        
        print("\n🔧 Réparation des données...")
        
        # Créer les catégories si manquantes
        if Categorie.objects.count() == 0:
            print("   📁 Création des catégories...")
            try:
                call_command('init_categories')
                print("   ✅ Catégories créées")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
        
        # Créer des données de test si manquantes
        if Produit.objects.count() == 0 or Magasin.objects.count() == 0:
            print("   📦 Création de données de test...")
            try:
                call_command('seed_data', '--produits', '50', '--magasins', '5', '--skip-elasticsearch')
                print("   ✅ Données de test créées")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
    
    def generer_rapport(self):
        """Générer un rapport de diagnostic."""
        print("\n" + "="*60)
        print("📊 RAPPORT DE DIAGNOSTIC")
        print("="*60)
        
        if not self.problemes:
            print("\n✅ Aucun problème détecté !")
        else:
            print(f"\n⚠️  {len(self.problemes)} problème(s) détecté(s):")
            for i, probleme in enumerate(self.problemes, 1):
                print(f"   {i}. {probleme}")
            
            if self.solutions:
                print(f"\n💡 Solutions proposées:")
                for i, solution in enumerate(self.solutions, 1):
                    print(f"   {i}. {solution}")
        
        print("\n" + "="*60)
    
    def executer(self):
        """Exécuter le diagnostic complet."""
        print("🚀 Démarrage du diagnostic système...")
        
        if not self.verifier_connexion_db():
            print("\n❌ Impossible de continuer sans connexion DB")
            return
        
        self.verifier_donnees()
        self.verifier_emails_dupliques()
        self.verifier_indexes()
        
        if self.fix:
            self.reparer_donnees()
        
        self.generer_rapport()

def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Diagnostic et réparation du système')
    parser.add_argument('--fix', action='store_true', help='Réparer automatiquement les problèmes')
    args = parser.parse_args()
    
    diagnostic = Diagnostic(fix=args.fix)
    diagnostic.executer()

if __name__ == '__main__':
    main()
