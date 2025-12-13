#!/usr/bin/env python
"""
Vérification complète de la base de données PostgreSQL
Vérifie la connexion, les tables, les indexes, et l'intégrité des données
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from django.apps import apps
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def check_connection():
    """Vérifie la connexion à la base de données"""
    try:
        db_engine = connection.settings_dict['ENGINE']
        is_postgres = 'postgresql' in db_engine
        
        with connection.cursor() as cursor:
            if is_postgres:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                logger.info(f"✅ PostgreSQL connecté: {version}")
                
                # Infos sur la base
                cursor.execute("SELECT current_database(), current_user;")
                db_name, user = cursor.fetchone()
                logger.info(f"   Base: {db_name}, Utilisateur: {user}")
            else:
                cursor.execute("SELECT sqlite_version();")
                version = cursor.fetchone()[0]
                logger.info(f"✅ SQLite connecté: version {version}")
                logger.info(f"   Base: {connection.settings_dict['NAME']}")
            
            return True, is_postgres
    except Exception as e:
        logger.error(f"❌ Erreur connexion base de données: {e}")
        return False, False

def check_tables(is_postgres):
    """Vérifie les tables de la base"""
    try:
        with connection.cursor() as cursor:
            if is_postgres:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cursor.fetchall()]
            else:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' 
                    ORDER BY name;
                """)
                tables = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"\n📊 Tables trouvées: {len(tables)}")
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    logger.info(f"   - {table}: {count} lignes")
                except:
                    pass
            
            return True
    except Exception as e:
        logger.error(f"❌ Erreur vérification tables: {e}")
        return False

def check_indexes(is_postgres):
    """Vérifie les indexes de performance"""
    try:
        with connection.cursor() as cursor:
            if is_postgres:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                    ORDER BY tablename, indexname;
                """)
                indexes = cursor.fetchall()
                
                logger.info(f"\n🔍 Indexes trouvés: {len(indexes)}")
                
                # Grouper par table
                tables_indexes = {}
                for schema, table, index, definition in indexes:
                    if table not in tables_indexes:
                        tables_indexes[table] = []
                    tables_indexes[table].append(index)
                
                for table, idx_list in sorted(tables_indexes.items()):
                    logger.info(f"   {table}: {len(idx_list)} indexes")
                    for idx in idx_list:
                        logger.info(f"      - {idx}")
            else:
                cursor.execute("""
                    SELECT name, tbl_name, sql 
                    FROM sqlite_master 
                    WHERE type='index'
                    ORDER BY tbl_name, name;
                """)
                indexes = cursor.fetchall()
                logger.info(f"\n🔍 Indexes trouvés: {len(indexes)}")
                for name, table, sql in indexes:
                    if sql:  # Skip auto-indexes
                        logger.info(f"   {table}.{name}")
            
            return True
    except Exception as e:
        logger.error(f"❌ Erreur vérification indexes: {e}")
        return False

def check_models_data():
    """Vérifie les données des modèles Django"""
    try:
        logger.info("\n📦 Données des modèles Django:")
        
        # Produits
        from apps.produits.models import Produit, Categorie, Prix
        logger.info(f"   Produits: {Produit.objects.count()}")
        logger.info(f"   Catégories: {Categorie.objects.count()}")
        logger.info(f"   Prix: {Prix.objects.count()}")
        
        # Magasins
        from apps.magasins.models import Magasin
        logger.info(f"   Magasins: {Magasin.objects.count()}")
        
        # Utilisateurs
        from apps.utilisateurs.models import Utilisateur
        logger.info(f"   Utilisateurs: {Utilisateur.objects.count()}")
        
        # Analyses
        try:
            from apps.analyses.models import Analyse
            logger.info(f"   Analyses: {Analyse.objects.count()}")
        except:
            pass
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur vérification modèles: {e}")
        return False

def check_database_size(is_postgres):
    """Vérifie la taille de la base"""
    try:
        if is_postgres:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        pg_size_pretty(pg_database_size(current_database())) as size;
                """)
                size = cursor.fetchone()[0]
                logger.info(f"\n💾 Taille de la base: {size}")
                
                # Taille par table
                cursor.execute("""
                    SELECT 
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 10;
                """)
                
                logger.info("   Top 10 tables par taille:")
                for table, table_size in cursor.fetchall():
                    logger.info(f"      {table}: {table_size}")
        else:
            import os
            db_path = connection.settings_dict['NAME']
            if os.path.exists(db_path):
                size = os.path.getsize(db_path)
                logger.info(f"\n💾 Taille de la base: {size / 1024 / 1024:.2f} MB")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur vérification taille: {e}")
        return False

def check_constraints(is_postgres):
    """Vérifie les contraintes et clés étrangères"""
    try:
        if is_postgres:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        tc.table_name,
                        tc.constraint_name,
                        tc.constraint_type
                    FROM information_schema.table_constraints tc
                    WHERE tc.table_schema = 'public'
                    ORDER BY tc.table_name, tc.constraint_type;
                """)
                
                constraints = cursor.fetchall()
                logger.info(f"\n🔒 Contraintes trouvées: {len(constraints)}")
                
                # Compter par type
                types = {}
                for table, name, ctype in constraints:
                    types[ctype] = types.get(ctype, 0) + 1
                
                for ctype, count in sorted(types.items()):
                    logger.info(f"   {ctype}: {count}")
        else:
            logger.info("\n🔒 Contraintes: Non disponible pour SQLite")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur vérification contraintes: {e}")
        return False

def check_performance(is_postgres):
    """Vérifie les statistiques de performance"""
    try:
        if is_postgres:
            with connection.cursor() as cursor:
                # Cache hit ratio
                cursor.execute("""
                    SELECT 
                        sum(heap_blks_read) as heap_read,
                        sum(heap_blks_hit) as heap_hit,
                        sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) * 100 as ratio
                    FROM pg_statio_user_tables;
                """)
                
                result = cursor.fetchone()
                if result and result[2]:
                    logger.info(f"\n⚡ Cache hit ratio: {result[2]:.2f}%")
                    if result[2] < 90:
                        logger.warning("   ⚠️ Cache hit ratio faible, considérer augmenter shared_buffers")
                
                # Requêtes lentes (si pg_stat_statements est activé)
                try:
                    cursor.execute("""
                        SELECT query, calls, mean_exec_time, total_exec_time
                        FROM pg_stat_statements
                        ORDER BY mean_exec_time DESC
                        LIMIT 5;
                    """)
                    
                    slow_queries = cursor.fetchall()
                    if slow_queries:
                        logger.info("\n🐌 Top 5 requêtes lentes:")
                        for query, calls, mean_time, total_time in slow_queries:
                            logger.info(f"   {mean_time:.2f}ms (avg) - {calls} calls")
                            logger.info(f"      {query[:100]}...")
                except:
                    logger.info("\n   pg_stat_statements non disponible")
        else:
            logger.info("\n⚡ Performance: Non disponible pour SQLite")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur vérification performance: {e}")
        return False

def main():
    logger.info("🔍 VÉRIFICATION COMPLÈTE DE LA BASE DE DONNÉES\n")
    logger.info("=" * 60)
    
    # Vérifier la connexion d'abord
    conn_result, is_postgres = check_connection()
    if not conn_result:
        logger.error("\n❌ Impossible de se connecter à la base de données")
        sys.exit(1)
    
    checks = [
        ("Tables", lambda: check_tables(is_postgres)),
        ("Indexes", lambda: check_indexes(is_postgres)),
        ("Modèles Django", check_models_data),
        ("Taille base", lambda: check_database_size(is_postgres)),
        ("Contraintes", lambda: check_constraints(is_postgres)),
        ("Performance", lambda: check_performance(is_postgres)),
    ]
    
    results = {"Connexion": True}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            logger.error(f"❌ Erreur lors de {name}: {e}")
            results[name] = False
    
    # Résumé
    logger.info("\n" + "=" * 60)
    logger.info("📊 RÉSUMÉ DES VÉRIFICATIONS:\n")
    
    for name, status in results.items():
        icon = "✅" if status else "❌"
        logger.info(f"{icon} {name}: {'OK' if status else 'ERREUR'}")
    
    # Exit code
    if all(results.values()):
        logger.info(f"\n✅ Base de données {'PostgreSQL' if is_postgres else 'SQLite'}: TOUT EST OK!")
        sys.exit(0)
    else:
        logger.error(f"\n❌ Base de données {'PostgreSQL' if is_postgres else 'SQLite'}: PROBLÈMES DÉTECTÉS")
        sys.exit(1)

if __name__ == '__main__':
    main()
