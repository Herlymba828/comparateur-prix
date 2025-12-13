"""
Optimisations de requêtes pour l'app produits.
"""
from django.db.models import Prefetch, Q, F, Count, Avg, Min, Max
from .models import Produit, Prix, Categorie, AvisProduit


class ProduitQueryOptimizer:
    """Optimiseur de requêtes pour les produits."""
    
    @staticmethod
    def get_optimized_queryset():
        """
        Retourne un queryset optimisé pour les produits avec toutes les relations.
        Évite les requêtes N+1.
        """
        return Produit.objects.select_related(
            'categorie',
            'marque',
            'unite_mesure'
        ).prefetch_related(
            Prefetch(
                'prix',
                queryset=Prix.objects.select_related('magasin').filter(est_disponible=True)
            ),
            Prefetch(
                'avis',
                queryset=AvisProduit.objects.select_related('utilisateur').order_by('-date_creation')[:5]
            ),
            'caracteristiques'
        ).annotate(
            nb_avis=Count('avis'),
            note_moyenne=Avg('avis__note'),
            prix_min=Min('prix__prix_actuel', filter=Q(prix__est_disponible=True)),
            prix_max=Max('prix__prix_actuel', filter=Q(prix__est_disponible=True))
        )
    
    @staticmethod
    def get_list_queryset():
        """
        Queryset optimisé pour la liste des produits (moins de données).
        """
        return Produit.objects.select_related(
            'categorie',
            'marque'
        ).prefetch_related(
            Prefetch(
                'prix',
                queryset=Prix.objects.select_related('magasin').filter(est_disponible=True).order_by('prix_actuel')[:3]
            )
        ).annotate(
            nb_avis=Count('avis'),
            note_moyenne=Avg('avis__note'),
            prix_min=Min('prix__prix_actuel', filter=Q(prix__est_disponible=True))
        )
    
    @staticmethod
    def get_detail_queryset():
        """
        Queryset optimisé pour le détail d'un produit (toutes les données).
        """
        return ProduitQueryOptimizer.get_optimized_queryset()


class CategorieQueryOptimizer:
    """Optimiseur de requêtes pour les catégories."""
    
    @staticmethod
    def get_optimized_queryset():
        """
        Retourne un queryset optimisé pour les catégories.
        """
        return Categorie.objects.select_related('parent').prefetch_related(
            Prefetch(
                'enfants',
                queryset=Categorie.objects.annotate(nb_produits=Count('produits'))
            )
        ).annotate(
            nb_produits=Count('produits')
        )
    
    @staticmethod
    def get_tree_queryset():
        """
        Queryset pour l'arbre complet des catégories.
        """
        return Categorie.objects.select_related('parent').prefetch_related(
            'enfants',
            'enfants__enfants'
        ).annotate(
            nb_produits=Count('produits')
        )


class PrixQueryOptimizer:
    """Optimiseur de requêtes pour les prix."""
    
    @staticmethod
    def get_optimized_queryset():
        """
        Retourne un queryset optimisé pour les prix.
        """
        return Prix.objects.select_related(
            'produit',
            'produit__categorie',
            'produit__marque',
            'magasin',
            'magasin__ville',
            'magasin__ville__region'
        ).filter(est_disponible=True)
    
    @staticmethod
    def get_with_history_queryset():
        """
        Queryset avec historique des prix.
        """
        return PrixQueryOptimizer.get_optimized_queryset().prefetch_related(
            Prefetch(
                'historique',
                queryset=Prix.objects.order_by('-date_changement')[:10]
            )
        )


def optimize_queryset_for_serialization(queryset, serializer_class):
    """
    Optimise automatiquement un queryset en fonction du serializer utilisé.
    
    Args:
        queryset: Le queryset à optimiser
        serializer_class: La classe du serializer
    
    Returns:
        Queryset optimisé
    """
    # Analyser les champs du serializer pour déterminer les relations nécessaires
    select_related_fields = []
    prefetch_related_fields = []
    
    # Cette fonction peut être étendue pour analyser automatiquement
    # les champs du serializer et optimiser en conséquence
    
    return queryset


# Mixins pour les ViewSets

class OptimizedQuerysetMixin:
    """
    Mixin pour optimiser automatiquement les querysets dans les ViewSets.
    """
    
    def get_queryset(self):
        """Override pour appliquer les optimisations."""
        queryset = super().get_queryset()
        
        # Appliquer les optimisations selon l'action
        if hasattr(self, 'action'):
            if self.action == 'list':
                return self._optimize_for_list(queryset)
            elif self.action == 'retrieve':
                return self._optimize_for_detail(queryset)
        
        return queryset
    
    def _optimize_for_list(self, queryset):
        """Optimiser pour la liste."""
        # À surcharger dans les sous-classes
        return queryset
    
    def _optimize_for_detail(self, queryset):
        """Optimiser pour le détail."""
        # À surcharger dans les sous-classes
        return queryset


class CachedQuerysetMixin:
    """
    Mixin pour ajouter du cache aux querysets.
    """
    cache_timeout = 300  # 5 minutes par défaut
    
    def get_queryset(self):
        """Override pour ajouter du cache."""
        from django.core.cache import cache
        from django.conf import settings
        
        queryset = super().get_queryset()
        
        # Ne pas cacher en mode DEBUG
        if settings.DEBUG:
            return queryset
        
        # Construire une clé de cache basée sur le modèle et les filtres
        cache_key = self._get_cache_key()
        
        # Essayer de récupérer depuis le cache
        cached_ids = cache.get(cache_key)
        if cached_ids is not None:
            # Retourner les objets depuis les IDs cachés
            return queryset.filter(pk__in=cached_ids)
        
        # Exécuter la requête et cacher les IDs
        ids = list(queryset.values_list('pk', flat=True))
        cache.set(cache_key, ids, self.cache_timeout)
        
        return queryset
    
    def _get_cache_key(self):
        """Générer une clé de cache unique."""
        model_name = self.queryset.model.__name__.lower()
        action = getattr(self, 'action', 'list')
        return f"queryset:{model_name}:{action}"
