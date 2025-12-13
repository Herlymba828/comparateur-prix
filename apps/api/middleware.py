"""
Middleware pour le monitoring des performances.
"""
from django.utils.deprecation import MiddlewareMixin
from .monitoring import PerformanceMonitor
import time


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware pour monitorer les performances de chaque requête.
    """
    
    def process_request(self, request):
        """Enregistrer le début de la requête."""
        request._start_time = time.time()
    
    def process_response(self, request, response):
        """Enregistrer les métriques de la requête."""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Enregistrer les métriques
            PerformanceMonitor.track_request(
                endpoint=request.path,
                method=request.method,
                duration=duration,
                status_code=response.status_code,
                user_id=request.user.id if request.user.is_authenticated else None
            )
            
            # Ajouter les headers de performance
            response['X-Response-Time'] = f"{duration:.3f}s"
        
        return response
