"""
Système de monitoring et métriques pour l'API.
"""
from django.core.cache import cache
from django.utils import timezone
from django.db import connection
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Moniteur de performance pour les endpoints API."""
    
    @staticmethod
    def track_request(endpoint, method, duration, status_code, user_id=None):
        """
        Enregistrer les métriques d'une requête.
        
        Args:
            endpoint: Chemin de l'endpoint
            method: Méthode HTTP
            duration: Durée en secondes
            status_code: Code de statut HTTP
            user_id: ID de l'utilisateur (optionnel)
        """
        # Clé de cache pour les métriques
        date_key = timezone.now().strftime('%Y-%m-%d')
        hour_key = timezone.now().strftime('%Y-%m-%d-%H')
        
        # Incrémenter les compteurs (avec gestion des clés manquantes)
        def safe_incr(key, delta=1):
            """Incrémenter une clé de cache de manière sûre."""
            try:
                cache.incr(key, delta)
            except ValueError:
                # La clé n'existe pas, la créer
                cache.set(key, delta, 86400)  # 24h
        
        safe_incr(f'metrics:requests:total:{date_key}')
        safe_incr(f'metrics:requests:endpoint:{endpoint}:{date_key}')
        safe_incr(f'metrics:requests:method:{method}:{date_key}')
        safe_incr(f'metrics:requests:status:{status_code}:{date_key}')
        safe_incr(f'metrics:requests:hour:{hour_key}')
        
        # Enregistrer les durées (pour calculer la moyenne)
        durations_key = f'metrics:durations:{endpoint}:{date_key}'
        durations = cache.get(durations_key, [])
        durations.append(duration)
        # Garder seulement les 1000 dernières durées
        if len(durations) > 1000:
            durations = durations[-1000:]
        cache.set(durations_key, durations, 86400)  # 24h
        
        # Enregistrer les erreurs
        if status_code >= 400:
            safe_incr(f'metrics:errors:total:{date_key}')
            safe_incr(f'metrics:errors:endpoint:{endpoint}:{date_key}')
            
            # Logger les erreurs 5xx
            if status_code >= 500:
                logger.error(
                    f"Erreur serveur: {method} {endpoint} - "
                    f"Status: {status_code}, Durée: {duration:.3f}s, User: {user_id}"
                )
        
        # Alertes pour les requêtes lentes (> 2 secondes)
        if duration > 2.0:
            logger.warning(
                f"Requête lente: {method} {endpoint} - "
                f"Durée: {duration:.3f}s, User: {user_id}"
            )
    
    @staticmethod
    def get_metrics(date=None):
        """
        Récupérer les métriques pour une date donnée.
        
        Args:
            date: Date au format 'YYYY-MM-DD' (défaut: aujourd'hui)
        
        Returns:
            Dict avec les métriques
        """
        if date is None:
            date = timezone.now().strftime('%Y-%m-%d')
        
        metrics = {
            'date': date,
            'requests': {
                'total': cache.get(f'metrics:requests:total:{date}', 0),
            },
            'errors': {
                'total': cache.get(f'metrics:errors:total:{date}', 0),
            },
            'database': {},
            'cache': {},
        }
        
        # Métriques de base de données
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            metrics['database']['status'] = 'connected'
            metrics['database']['queries'] = len(connection.queries)
        except Exception as e:
            metrics['database']['status'] = 'error'
            metrics['database']['error'] = str(e)
        
        # Métriques de cache
        try:
            cache.set('test_key', 'test_value', 1)
            cache.get('test_key')
            metrics['cache']['status'] = 'connected'
        except Exception as e:
            metrics['cache']['status'] = 'error'
            metrics['cache']['error'] = str(e)
        
        return metrics
    
    @staticmethod
    def get_slow_endpoints(date=None, threshold=1.0):
        """
        Récupérer les endpoints les plus lents.
        
        Args:
            date: Date au format 'YYYY-MM-DD' (défaut: aujourd'hui)
            threshold: Seuil en secondes (défaut: 1.0)
        
        Returns:
            Liste des endpoints lents avec leurs durées moyennes
        """
        if date is None:
            date = timezone.now().strftime('%Y-%m-%d')
        
        # Cette fonction nécessiterait de parcourir toutes les clés de cache
        # Pour une implémentation complète, utiliser Redis avec SCAN
        # ou stocker les métriques dans une base de données
        
        return []


def monitor_performance(func):
    """
    Décorateur pour monitorer les performances d'une vue.
    
    Usage:
        @monitor_performance
        def my_view(request):
            ...
    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        
        # Exécuter la vue
        response = func(request, *args, **kwargs)
        
        # Calculer la durée
        duration = time.time() - start_time
        
        # Enregistrer les métriques
        endpoint = request.path
        method = request.method
        status_code = getattr(response, 'status_code', 200)
        user_id = request.user.id if request.user.is_authenticated else None
        
        PerformanceMonitor.track_request(
            endpoint=endpoint,
            method=method,
            duration=duration,
            status_code=status_code,
            user_id=user_id
        )
        
        # Ajouter les headers de performance
        if hasattr(response, '__setitem__'):
            response['X-Response-Time'] = f"{duration:.3f}s"
            response['X-DB-Queries'] = str(len(connection.queries))
        
        return response
    
    return wrapper


class QueryCounter:
    """Compteur de requêtes SQL pour détecter les problèmes N+1."""
    
    def __init__(self, threshold=10):
        self.threshold = threshold
        self.initial_count = 0
    
    def __enter__(self):
        self.initial_count = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        final_count = len(connection.queries)
        query_count = final_count - self.initial_count
        
        if query_count > self.threshold:
            logger.warning(
                f"Nombre élevé de requêtes SQL détecté: {query_count} requêtes "
                f"(seuil: {self.threshold})"
            )
            
            # Logger les requêtes en mode DEBUG
            from django.conf import settings
            if settings.DEBUG:
                for query in connection.queries[self.initial_count:final_count]:
                    logger.debug(f"SQL: {query['sql']}")


def check_n_plus_one(threshold=10):
    """
    Décorateur pour détecter les problèmes N+1.
    
    Usage:
        @check_n_plus_one(threshold=20)
        def my_view(request):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with QueryCounter(threshold=threshold):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class HealthChecker:
    """Vérificateur de santé du système."""
    
    @staticmethod
    def check_database():
        """Vérifier la connexion à la base de données."""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': 'healthy', 'message': 'Database connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    @staticmethod
    def check_cache():
        """Vérifier la connexion au cache."""
        try:
            test_key = 'health_check_test'
            test_value = 'ok'
            cache.set(test_key, test_value, 10)
            result = cache.get(test_key)
            cache.delete(test_key)
            
            if result == test_value:
                return {'status': 'healthy', 'message': 'Cache connection OK'}
            else:
                return {'status': 'unhealthy', 'message': 'Cache read/write failed'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    @staticmethod
    def check_celery():
        """Vérifier la connexion à Celery."""
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                return {'status': 'healthy', 'message': 'Celery workers active'}
            else:
                return {'status': 'unhealthy', 'message': 'No Celery workers found'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': str(e)}
    
    @staticmethod
    def get_full_health_status():
        """Obtenir le statut de santé complet du système."""
        health = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {
                'database': HealthChecker.check_database(),
                'cache': HealthChecker.check_cache(),
                'celery': HealthChecker.check_celery(),
            }
        }
        
        # Déterminer le statut global
        for check in health['checks'].values():
            if check['status'] == 'unhealthy':
                health['status'] = 'unhealthy'
                break
        
        return health
