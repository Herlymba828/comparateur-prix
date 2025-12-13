"""
Pagination optimisée pour de meilleures performances.
"""
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response
from collections import OrderedDict
from django.core.cache import cache
import hashlib


class OptimizedPageNumberPagination(PageNumberPagination):
    """
    Pagination par numéro de page optimisée.
    Cache le count() qui est coûteux.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    # Durée du cache pour le count (5 minutes)
    count_cache_timeout = 300
    
    def get_count(self, queryset):
        """
        Obtenir le count avec cache.
        """
        # Générer une clé de cache basée sur le queryset
        cache_key = self._get_count_cache_key(queryset)
        
        # Essayer de récupérer depuis le cache
        cached_count = cache.get(cache_key)
        if cached_count is not None:
            return cached_count
        
        # Calculer le count
        count = super().get_count(queryset)
        
        # Mettre en cache
        cache.set(cache_key, count, self.count_cache_timeout)
        
        return count
    
    def _get_count_cache_key(self, queryset):
        """Générer une clé de cache pour le count."""
        # Utiliser le SQL de la requête comme base
        sql = str(queryset.query)
        cache_key = f"pagination:count:{hashlib.md5(sql.encode()).hexdigest()}"
        return cache_key
    
    def get_paginated_response(self, data):
        """
        Réponse paginée avec métadonnées optimisées.
        """
        return Response(OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('page_size', self.page_size),
            ('total_pages', self.page.paginator.num_pages),
            ('current_page', self.page.number),
            ('results', data)
        ]))


class FastCursorPagination(CursorPagination):
    """
    Pagination par curseur pour de très grandes listes.
    Plus rapide que PageNumberPagination pour les grandes tables.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    ordering = '-id'  # Doit être un champ indexé
    
    def get_paginated_response(self, data):
        """Réponse paginée simplifiée."""
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ]))


class LimitOffsetPaginationOptimized(PageNumberPagination):
    """
    Pagination limit/offset optimisée.
    Évite le count() coûteux en utilisant une estimation.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    # Utiliser une estimation du count au lieu du count exact
    use_estimated_count = True
    
    def get_count(self, queryset):
        """
        Obtenir le count (estimé si activé).
        """
        if not self.use_estimated_count:
            return super().get_count(queryset)
        
        # Pour PostgreSQL, utiliser une estimation rapide
        from django.db import connection
        
        if 'postgresql' in connection.settings_dict['ENGINE']:
            try:
                table_name = queryset.model._meta.db_table
                with connection.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT reltuples::bigint AS estimate
                        FROM pg_class
                        WHERE relname = %s;
                    """, [table_name])
                    result = cursor.fetchone()
                    if result:
                        return int(result[0])
            except Exception:
                pass
        
        # Fallback sur le count normal
        return super().get_count(queryset)


class InfinitePagination(PageNumberPagination):
    """
    Pagination infinie (scroll infini).
    Retourne seulement next/previous sans count.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        """Réponse sans count pour éviter la requête coûteuse."""
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data),
            ('has_more', self.page.has_next())
        ]))
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Paginer sans calculer le count total.
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None
        
        paginator = self.django_paginator_class(queryset, page_size)
        page_number = request.query_params.get(self.page_query_param, 1)
        
        try:
            self.page = paginator.page(page_number)
        except Exception:
            return []
        
        return list(self.page)


class SmartPagination:
    """
    Pagination intelligente qui choisit la meilleure stratégie.
    """
    
    @staticmethod
    def get_pagination_class(queryset, request):
        """
        Choisir la meilleure classe de pagination selon le contexte.
        
        Args:
            queryset: Le queryset à paginer
            request: La requête HTTP
        
        Returns:
            Classe de pagination appropriée
        """
        # Estimer la taille de la table
        estimated_count = queryset.count() if queryset.query.where else None
        
        # Pour les très grandes tables (>100k), utiliser cursor pagination
        if estimated_count and estimated_count > 100000:
            return FastCursorPagination
        
        # Pour les tables moyennes (10k-100k), utiliser pagination optimisée
        if estimated_count and estimated_count > 10000:
            return OptimizedPageNumberPagination
        
        # Pour les petites tables, utiliser pagination standard
        return PageNumberPagination
