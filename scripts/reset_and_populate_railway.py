#!/usr/bin/env python
"""
Script pour réinitialiser et repeupler la base de données Railway
Usage: railway run python scripts/reset_and_populate_railway.py
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

from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

User = get_user_model()

def confirm_reset():
    """Demande confirmation avant de supprimer les données."""
    db_name = connection.settings_dict['NAME']
    db_host = connection.settings_dict.get('HOST', 'localhost')
    
    logger.warning("⚠️  ATTENTION : Cette opération va supprimer TOUTES les données !")
    logger.info(f"📊 Base de données : {db_name}")
    logger.info(f"🌐 Hôte : {db_host}")
    
    # Compter les données actuelles
    try:
        from apps.produits.models import Produit, Prix
        from apps.magasins.models import Magasin
        from apps.utilisateurs.models import Utilisateur
        
        logger.info(f"\n📈 Données actuelles :")
        logger.info(f"   - Produits : {Produit.objects.count()}")
        logger.info(f"   - Prix : {Prix.objects.count()}")
        logger.info(f"   - Magasins : {Magasin.objects.count()}")
        logger.info(f"   - Utilisateurs : {Utilisateur.objects.count()}")
    except Exception as e:
        logger.warning(f"   Impossible de compter les données : {e}")
    
    print("\n" + "="*60)
    confirmation = input("Taper 'RESET' pour confirmer la suppression : ")
    print("="*60 + "\n")
    
    return confirmation == 'RESET'

def drop_all_tables():
    """Supprime toutes les tables de la base."""
    logger.info("🗑️  Suppression de toutes les tables...")
    
    with connection.cursor() as cursor:
        # Obtenir toutes les tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()
        
        if not tables:
            logger.info("ℹ️  Aucune table à supprimer")
            return
        
        logger.info(f"📋 {len(tables)} tables trouvées")
        
        # Désactiver les contraintes de clés étrangères
        cursor.execute("SET session_replication_role = 'replica';")
        
        # Supprimer chaque table
        for table in tables:
            table_name = table[0]
            logger.info(f"   - Suppression de {table_name}...")
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
        
        # Supprimer les séquences
        cursor.execute("""
            SELECT sequence_name FROM information_schema.sequences
            WHERE sequence_schema = 'public'
        """)
        sequences = cursor.fetchall()
        for seq in sequences:
            seq_name = seq[0]
            cursor.execute(f'DROP SEQUENCE IF EXISTS "{seq_name}" CASCADE')
        
        # Réactiver les contraintes
        cursor.execute("SET session_replication_role = 'origin';")
        
        logger.info("✅ Toutes les tables ont été supprimées")

def recreate_structure():
    """Recrée la structure de la base."""
    logger.info("\n🔨 Recréation de la structure de la base...")
    call_command('migrate', '--run-syncdb', verbosity=0)
    logger.info("✅ Structure de la base recréée")

def create_superuser():
    """Crée un superutilisateur admin."""
    logger.info("\n👤 Création du superutilisateur...")
    
    try:
        if User.objects.filter(username='admin').exists():
            logger.info("   ℹ️  Superutilisateur 'admin' existe déjà")
            return
        
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@comparo.com',
            password='admin123',
            first_name='Admin',
            last_name='Comparo'
        )
        logger.info(f"✅ Superutilisateur créé : {admin.username}")
        logger.info(f"   📧 Email : {admin.email}")
        logger.info(f"   🔑 Mot de passe : admin123")
    except Exception as e:
        logger.error(f"❌ Erreur création superutilisateur : {e}")

def populate_data():
    """Peuple la base avec des données."""
    logger.info("\n📦 Peuplement de la base de données...")
    
    # Vérifier si des commandes de peuplement existent
    commands = []
    
    # Essayer seed_data
    try:
        call_command('help', 'seed_data')
        commands.append('seed_data')
    except:
        pass
    
    # Essayer populate_db
    try:
        call_command('help', 'populate_db')
        commands.append('populate_db')
    except:
        pass
    
    if commands:
        logger.info(f"   Commandes disponibles : {', '.join(commands)}")
        for cmd in commands:
            try:
                logger.info(f"   Exécution de {cmd}...")
                call_command(cmd, verbosity=1)
                logger.info(f"   ✅ {cmd} terminé")
            except Exception as e:
                logger.warning(f"   ⚠️  Erreur {cmd} : {e}")
    else:
        logger.warning("   ⚠️  Aucune commande de peuplement trouvée")
        logger.info("   💡 Vous pouvez scraper les données DGCCRF manuellement")

def scrape_dgccrf():
    """Lance le scraping DGCCRF si disponible."""
    logger.info("\n🌐 Scraping des données DGCCRF...")
    
    try:
        call_command('help', 'scrape_dgccrf')
        
        response = input("   Lancer le scraping DGCCRF ? (o/N) : ")
        if response.lower() == 'o':
            logger.info("   Démarrage du scraping...")
            call_command('scrape_dgccrf', verbosity=1)
            logger.info("   ✅ Scraping terminé")
        else:
            logger.info("   ⏭️  Scraping ignoré")
    except:
        logger.warning("   ⚠️  Commande scrape_dgccrf non disponible")

def show_summary():
    """Affiche un résumé des données."""
    logger.info("\n" + "="*60)
    logger.info("📊 RÉSUMÉ DES DONNÉES")
    logger.info("="*60)
    
    try:
        from apps.produits.models import Produit, Prix, Categorie
        from apps.magasins.models import Magasin
        from apps.utilisateurs.models import Utilisateur
        
        logger.info(f"\n✅ Données créées :")
        logger.info(f"   - Produits : {Produit.objects.count()}")
        logger.info(f"   - Catégories : {Categorie.objects.count()}")
        logger.info(f"   - Prix : {Prix.objects.count()}")
        logger.info(f"   - Magasins : {Magasin.objects.count()}")
        logger.info(f"   - Utilisateurs : {Utilisateur.objects.count()}")
        
        # Afficher quelques exemples
        if Produit.objects.exists():
            logger.info(f"\n📦 Exemples de produits :")
            for p in Produit.objects.all()[:5]:
                logger.info(f"   - {p.nom}")
        
        if Magasin.objects.exists():
            logger.info(f"\n🏪 Exemples de magasins :")
            for m in Magasin.objects.all()[:5]:
                logger.info(f"   - {m.nom}")
        
    except Exception as e:
        logger.error(f"❌ Erreur affichage résumé : {e}")
    
    logger.info("\n" + "="*60)
    logger.info("🎉 BASE DE DONNÉES RÉINITIALISÉE ET PEUPLÉE !")
    logger.info("="*60)
    
    logger.info("\n💡 Prochaines étapes :")
    logger.info("   1. Tester l'API : curl https://comparo.up.railway.app/api/health/")
    logger.info("   2. Vérifier les données : curl https://comparo.up.railway.app/api/diagnostic/")
    logger.info("   3. Se connecter à l'admin : https://comparo.up.railway.app/admin/")
    logger.info("      Username : admin")
    logger.info("      Password : admin123")

def main():
    """Fonction principale."""
    logger.info("🚀 RÉINITIALISATION ET PEUPLEMENT DE LA BASE RAILWAY")
    logger.info("="*60 + "\n")
    
    # Confirmation
    if not confirm_reset():
        logger.info("❌ Opération annulée par l'utilisateur")
        return
    
    try:
        # Étape 1 : Supprimer les tables
        drop_all_tables()
        
        # Étape 2 : Recréer la structure
        recreate_structure()
        
        # Étape 3 : Créer le superutilisateur
        create_superuser()
        
        # Étape 4 : Peupler avec des données
        populate_data()
        
        # Étape 5 : Optionnel - Scraper DGCCRF
        scrape_dgccrf()
        
        # Étape 6 : Afficher le résumé
        show_summary()
        
    except Exception as e:
        logger.error(f"\n❌ ERREUR : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
