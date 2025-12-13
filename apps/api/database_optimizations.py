"""
Optimisations avancées de la base de données.
"""
from django.db import connection
from django.core.cache import cache
from functools import wraps
import hashlib
import json


class DatabaseOptimizer:
    """Optimiseur de base de données."""
    
    @staticmethod
    def get_connection_pool_stats():
        """Obtenir les statistiques du pool de connexions."""
        try:
            with connection.cursor() as cursor:
                # PostgreSQL
                if 'postgresql' in connection.settings_dict['ENGINE']:
                    cursor.execute("""
                        SELECT 
                            count(*) as total_connections,
                            count(*) FILTER (WHERE state = 'active') as active_connections,
                            count(*) FILTER (WHERE state = 'idle') as idle_connections
                        FROM pg_stat_activity
                        WHERE datname = current_database();
                    """)
                    result = cursor.fetchone()
                    return {
                        'total': result[0],
                        'active': result[1],
                        'idle': result[2]
                    }
        except Exception:
            return None
    
    @staticmethod
    def optimize_table(table_name):
        """Optimiser une table (VACUUM ANALYZE pour PostgreSQL)."""
        try:
            with connection.cursor() as cursor:
                if 'postgresql' in connection.settings_dict['ENGINE']:
                    cursor.execute(f"VACUUM ANALYZE {table_name};")
                    return True
        except Exception:
            return False
    
    @staticmethod
    def get_slow_queries(limit=10):
        """Obtenir les requêtes les plus lentes (PostgreSQL)."""
        try:
            with connection.cursor() as cursor:
                if 'postgresql' in connection.settings_dict['ENGINE']:
                    cursor.execute("""
                        SELECT 
                            query,
                            calls,
                            total_time,
                            mean_time,
                            max_time
                        FROM pg_stat_statements
                        ORDER BY mean_time DESC
                        LIMIT %s;
                    """, [limit])
                    return cursor.fetchall()
        except Exception:
            return []
    
    @staticmethod
    def create_missing_indexes():
        """Créer les indexes manquants recommandés."""
        indexes = [
            # Produits
            ("produits_produit", "nom", "gin_trgm_ops", "GIN"),
            ("produits_produit", "code_barre", None, "BTREE"),
            ("produits_produit", "est_actif", None, "BTREE"),
            
            # Prix
            ("produits_prix", "prix_actuel", None, "BTREE"),
            ("produits_prix", "est_disponible", None, "BTREE"),
            ("produits_prix", "(produit_id, magasin_id)", None, "BTREE"),
            
            # Catégories
            ("produits_categorie", "parent_id", None, "BTREE"),
            ("produits_categorie", "slug", None, "BTREE"),
            
            # Utilisateurs
            ("utilisateurs_utilisateur", "email", None, "BTREE"),
            ("utilisateurs_utilisateur", "username", None, "BTREE"),
            
            # Magasins
            ("magasins_magasin", "(latitude, longitude)", None, "BTREE"),
        ]
        
        created = []
        errors = []
        
        try:
            with connection.cursor() as cursor:
                if 'postgresql' not in connection.settings_dict['ENGINE']:
                    return created, ["Indexes disponibles uniquement pour PostgreSQL"]
                
                for table, column, ops, index_type in indexes:
                    try:
                        index_name = f"idx_{table}_{column.replace('(', '').replace(')', '').replace(',', '_').replace(' ', '')}"
                        
                        if ops:
                            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING {index_type}({column} {ops});"
                        else:
                            sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} USING {index_type}({column});"
                        
                        cursor.execute(sql)
                        created.append(index_name)
                    except Exception as e:
                        errors.append(f"{table}.{column}: {str(e)}")
        
        except Exception as e:
            errors.append(f"Erreur globale: {str(e)}")
        
        return created, errors


def cache_query_result(timeout=300, key_prefix='query'):
    """
    Décorateur pour cacher les résultats de requêtes.
    
    Usage:
        @cache_query_result(timeout=600, key_prefix='produits')
        def get_produits_actifs():
            return Produit.objects.filter(est_actif=True)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Générer une clé de cache basée sur la fonction et les arguments
            cache_key_parts = [key_prefix, func.__name__]
            
            # Ajouter les arguments à la clé
            if args:
                cache_key_parts.append(str(args))
            if kwargs:
                cache_key_parts.append(json.dumps(kwargs, sort_keys=True))
            
            # Créer un hash de la clé
            cache_key_str = ":".join(cache_key_parts)
            cache_key = hashlib.md5(cache_key_str.encode()).hexdigest()
            
            # Essayer de récupérer depuis le cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Exécuter la fonction
            result = func(*args, **kwargs)
            
            # Mettre en cache
            cache.set(cache_key, result, timeout)
            
            return result
        
        return wrapper
    return decorator


class QuerySetCache:
    """Cache intelligent pour les QuerySets."""
    
    @staticmethod
    def cache_queryset(queryset, cache_key, timeout=300):
        """
        Cacher un queryset en stockant les IDs.
        
        Args:
            queryset: Le queryset à cacher
            cache_key: Clé de cache
            timeout: Durée du cache en secondes
        
        Returns:
            Le queryset (non modifié)
        """
        # Extraire les IDs
        ids = list(queryset.values_list('pk', flat=True))
        
        # Cacher les IDs
        cache.set(cache_key, ids, timeout)
        
        return queryset
    
    @staticmethod
    def get_cached_queryset(model, cache_key):
        """
        Récupérer un queryset depuis le cache.
        
        Args:
            model: Le modèle Django
            cache_key: Clé de cache
        
        Returns:
            QuerySet ou None si pas en cache
        """
        # Récupérer les IDs depuis le cache
        ids = cache.get(cache_key)
        
        if ids is None:
            return None
        
        # Retourner un queryset filtré par IDs
        return model.objects.filter(pk__in=ids)


class BulkOperationOptimizer:
    """Optimiseur pour les opérations en masse."""
    
    @staticmethod
    def bulk_create_with_cache_invalidation(model, objects, cache_patterns=None):
        """
        Créer des objets en masse et invalider le cache.
        
        Args:
            model: Le modèle Django
            objects: Liste d'objets à créer
            cache_patterns: Patterns de cache à invalider
        """
        # Créer en masse
        created = model.objects.bulk_create(objects)
        
        # Invalider le cache
        if cache_patterns:
            for pattern in cache_patterns:
                try:
                    cache.delete_pattern(pattern)
                except AttributeError:
                    # delete_pattern pas disponible
                    pass
        
        return created
    
    @staticmethod
    def bulk_update_with_cache_invalidation(objects, fields, cache_patterns=None):
        """
        Mettre à jour des objets en masse et invalider le cache.
        
        Args:
            objects: Liste d'objets à mettre à jour
            fields: Champs à mettre à jour
            cache_patterns: Patterns de cache à invalider
        """
        # Obtenir le modèle
        if not objects:
            return
        
        model = objects[0].__class__
        
        # Mettre à jour en masse
        model.objects.bulk_update(objects, fields)
        
        # Invalider le cache
        if cache_patterns:
            for pattern in cache_patterns:
                try:
                    cache.delete_pattern(pattern)
                except AttributeError:
                    pass


class ReadReplicaRouter:
    """
    Router pour utiliser des réplicas en lecture.
    À configurer dans settings.py si vous avez des réplicas.
    """
    
    def db_for_read(self, model, **hints):
        """Diriger les lectures vers le replica."""
        # Si vous avez un replica configuré, retourner 'replica'
        # Sinon, retourner None pour utiliser la DB par défaut
        return None
    
    def db_for_write(self, model, **hints):
        """Diriger les écritures vers la DB principale."""
        return 'default'
    
    def allow_relation(self, obj1, obj2, **hints):
        """Autoriser les relations."""
        return True
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Autoriser les migrations sur la DB principale uniquement."""
        return db == 'default'
