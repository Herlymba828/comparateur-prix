"""
Vues asynchrones pour de meilleures performances.
Nécessite Django 4.1+ et Python 3.8+
"""
from django.http import JsonResponse
from django.views import View
from asgiref.sync import sync_to_async
from django.core.cache import cache
import asyncio


class AsyncHealthCheckView(View):
    """
    Health check asynchrone qui vérifie tous les services en parallèle.
    """
    
    async def get(self, request):
        """Health check asynchrone."""
        # Exécuter toutes les vérifications en parallèle
        results = await asyncio.gather(
            self.check_database(),
            self.check_cache(),
            self.check_celery(),
            return_exceptions=True
        )
        
        # Analyser les résultats
        db_status, cache_status, celery_status = results
        
        health = {
            'status': 'healthy',
            'checks': {
                'database': db_status if not isinstance(db_status, Exception) else {'status': 'error', 'message': str(db_status)},
                'cache': cache_status if not isinstance(cache_status, Exception) else {'status': 'error', 'message': str(cache_status)},
                'celery': celery_status if not isinstance(celery_status, Exception) else {'status': 'error', 'message': str(celery_status)},
            }
        }
        
        # Déterminer le statut global
        for check in health['checks'].values():
            if isinstance(check, dict) and check.get('status') != 'healthy':
                health['status'] = 'unhealthy'
                break
        
        status_code = 200 if health['status'] == 'healthy' else 503
        return JsonResponse(health, status=status_code)
    
    @sync_to_async
    def check_database(self):
        """Vérifier la base de données."""
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': 'healthy', 'message': 'Database OK'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @sync_to_async
    def check_cache(self):
        """Vérifier le cache."""
        try:
            cache.set('health_check', 'ok', 10)
            result = cache.get('health_check')
            cache.delete('health_check')
            
            if result == 'ok':
                return {'status': 'healthy', 'message': 'Cache OK'}
            else:
                return {'status': 'error', 'message': 'Cache read/write failed'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    @sync_to_async
    def check_celery(self):
        """Vérifier Celery."""
        try:
            from celery import current_app
            inspect = current_app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                return {'status': 'healthy', 'message': 'Celery OK'}
            else:
                return {'status': 'warning', 'message': 'No workers'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class AsyncBatchView(View):
    """
    Vue pour traiter plusieurs requêtes en parallèle.
    
    POST /api/batch/
    {
        "requests": [
            {"method": "GET", "path": "/api/produits/1/"},
            {"method": "GET", "path": "/api/produits/2/"},
            {"method": "GET", "path": "/api/produits/3/"}
        ]
    }
    """
    
    async def post(self, request):
        """Traiter plusieurs requêtes en parallèle."""
        import json
        
        try:
            data = json.loads(request.body)
            requests_data = data.get('requests', [])
            
            # Limiter le nombre de requêtes parallèles
            if len(requests_data) > 10:
                return JsonResponse({
                    'error': 'Maximum 10 requests per batch'
                }, status=400)
            
            # Exécuter toutes les requêtes en parallèle
            tasks = [
                self.execute_request(req_data)
                for req_data in requests_data
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Formater les résultats
            responses = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    responses.append({
                        'index': i,
                        'status': 'error',
                        'error': str(result)
                    })
                else:
                    responses.append({
                        'index': i,
                        'status': 'success',
                        'data': result
                    })
            
            return JsonResponse({
                'responses': responses
            })
        
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    
    @sync_to_async
    def execute_request(self, request_data):
        """Exécuter une requête."""
        # Cette fonction devrait appeler les vues appropriées
        # Pour l'instant, retourner un placeholder
        return {
            'method': request_data.get('method'),
            'path': request_data.get('path'),
            'result': 'placeholder'
        }


class AsyncDataAggregatorView(View):
    """
    Vue pour agréger des données de plusieurs sources en parallèle.
    """
    
    async def get(self, request):
        """Agréger les données."""
        # Récupérer les données de plusieurs sources en parallèle
        results = await asyncio.gather(
            self.get_produits_populaires(),
            self.get_categories(),
            self.get_promotions(),
            self.get_magasins_proches(),
            return_exceptions=True
        )
        
        produits, categories, promotions, magasins = results
        
        return JsonResponse({
            'produits_populaires': produits if not isinstance(produits, Exception) else [],
            'categories': categories if not isinstance(categories, Exception) else [],
            'promotions': promotions if not isinstance(promotions, Exception) else [],
            'magasins_proches': magasins if not isinstance(magasins, Exception) else [],
        })
    
    @sync_to_async
    def get_produits_populaires(self):
        """Récupérer les produits populaires."""
        from apps.produits.models import Produit
        return list(
            Produit.objects.filter(est_actif=True)
            .order_by('-nombre_vues')[:10]
            .values('id', 'nom', 'code_barre')
        )
    
    @sync_to_async
    def get_categories(self):
        """Récupérer les catégories."""
        from apps.produits.models import Categorie
        return list(
            Categorie.objects.filter(parent__isnull=True)
            .values('id', 'nom', 'slug')
        )
    
    @sync_to_async
    def get_promotions(self):
        """Récupérer les promotions."""
        from apps.produits.models import Prix
        return list(
            Prix.objects.filter(est_promotion=True, est_disponible=True)
            .select_related('produit')
            .values('id', 'produit__nom', 'prix_actuel', 'prix_avant_promotion')[:10]
        )
    
    @sync_to_async
    def get_magasins_proches(self):
        """Récupérer les magasins proches."""
        from apps.magasins.models import Magasin
        return list(
            Magasin.objects.filter(est_actif=True)
            .values('id', 'nom', 'adresse')[:10]
        )


# Décorateur pour convertir une vue synchrone en asynchrone

def async_view(sync_view_func):
    """
    Décorateur pour convertir une vue synchrone en asynchrone.
    
    Usage:
        @async_view
        def my_view(request):
            # Code synchrone
            return JsonResponse({'status': 'ok'})
    """
    from functools import wraps
    
    @wraps(sync_view_func)
    async def async_wrapper(request, *args, **kwargs):
        return await sync_to_async(sync_view_func)(request, *args, **kwargs)
    
    return async_wrapper
