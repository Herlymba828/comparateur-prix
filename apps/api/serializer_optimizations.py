"""
Optimisations pour les serializers DRF.
"""
from rest_framework import serializers
from django.core.cache import cache
import hashlib


class CachedSerializerMixin:
    """
    Mixin pour cacher les résultats de sérialisation.
    Utile pour les objets qui changent rarement.
    """
    cache_timeout = 300  # 5 minutes par défaut
    
    def to_representation(self, instance):
        """Sérialiser avec cache."""
        # Générer une clé de cache
        cache_key = self._get_cache_key(instance)
        
        # Essayer de récupérer depuis le cache
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return cached_data
        
        # Sérialiser normalement
        data = super().to_representation(instance)
        
        # Mettre en cache
        cache.set(cache_key, data, self.cache_timeout)
        
        return data
    
    def _get_cache_key(self, instance):
        """Générer une clé de cache pour l'instance."""
        model_name = instance.__class__.__name__
        instance_id = instance.pk
        
        # Inclure updated_at si disponible pour invalider automatiquement
        updated_at = getattr(instance, 'updated_at', None) or getattr(instance, 'date_modification', None)
        timestamp = updated_at.timestamp() if updated_at else 0
        
        cache_key = f"serializer:{model_name}:{instance_id}:{timestamp}"
        return cache_key


class LazySerializerMixin:
    """
    Mixin pour charger les relations de manière lazy.
    Évite de charger des données non nécessaires.
    """
    
    def __init__(self, *args, **kwargs):
        # Récupérer les champs demandés depuis le contexte
        context = kwargs.get('context', {})
        request = context.get('request')
        
        if request:
            # Permettre de spécifier les champs via ?fields=nom,prix,categorie
            fields_param = request.query_params.get('fields')
            if fields_param:
                fields = fields_param.split(',')
                # Supprimer les champs non demandés
                allowed = set(fields)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
        
        super().__init__(*args, **kwargs)


class BulkSerializerMixin:
    """
    Mixin pour optimiser la sérialisation en masse.
    Précharge toutes les relations nécessaires.
    """
    
    @classmethod
    def setup_eager_loading(cls, queryset):
        """
        Précharger toutes les relations nécessaires.
        À surcharger dans les sous-classes.
        """
        return queryset
    
    def to_representation(self, instance):
        """Sérialiser avec préchargement."""
        # Si c'est une liste, précharger les relations
        if isinstance(instance, list):
            # Obtenir le queryset
            if instance:
                model = instance[0].__class__
                ids = [obj.pk for obj in instance]
                queryset = model.objects.filter(pk__in=ids)
                
                # Précharger les relations
                queryset = self.setup_eager_loading(queryset)
                
                # Créer un dictionnaire pour un accès rapide
                objects_dict = {obj.pk: obj for obj in queryset}
                
                # Remplacer les instances par les versions préchargées
                instance = [objects_dict.get(obj.pk, obj) for obj in instance]
        
        return super().to_representation(instance)


class MinimalSerializerMixin:
    """
    Mixin pour créer des versions minimales de serializers.
    Utile pour les listes où on ne veut pas tous les détails.
    """
    
    # Champs à inclure dans la version minimale
    minimal_fields = ['id', 'nom']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Si minimal=true dans le contexte, garder seulement les champs minimaux
        context = kwargs.get('context', {})
        request = context.get('request')
        
        if request and request.query_params.get('minimal') == 'true':
            allowed = set(self.minimal_fields)
            existing = set(self.fields.keys())
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class DynamicFieldsSerializer(serializers.ModelSerializer):
    """
    Serializer qui permet de spécifier dynamiquement les champs.
    
    Usage:
        # Tous les champs
        GET /api/produits/
        
        # Seulement certains champs
        GET /api/produits/?fields=id,nom,prix
        
        # Exclure certains champs
        GET /api/produits/?exclude=description,caracteristiques
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        context = kwargs.get('context', {})
        request = context.get('request')
        
        if not request:
            return
        
        # Champs à inclure
        fields = request.query_params.get('fields')
        if fields:
            fields = set(fields.split(','))
            allowed = set(self.fields.keys())
            for field_name in allowed - fields:
                self.fields.pop(field_name)
        
        # Champs à exclure
        exclude = request.query_params.get('exclude')
        if exclude:
            exclude = set(exclude.split(','))
            for field_name in exclude:
                self.fields.pop(field_name, None)


class ReadOnlySerializerMixin:
    """
    Mixin pour créer des serializers en lecture seule optimisés.
    Évite la validation inutile.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Marquer tous les champs comme read_only
        for field in self.fields.values():
            field.read_only = True


class FastListSerializer(serializers.ListSerializer):
    """
    ListSerializer optimisé pour les grandes listes.
    Utilise values() au lieu de charger les objets complets.
    """
    
    def to_representation(self, data):
        """
        Sérialiser en utilisant values() pour de meilleures performances.
        """
        # Si c'est un queryset, utiliser values()
        if hasattr(data, 'values'):
            # Obtenir les champs nécessaires
            fields = list(self.child.fields.keys())
            
            # Utiliser values() pour charger seulement les champs nécessaires
            values_data = list(data.values(*fields))
            
            return values_data
        
        # Sinon, utiliser la méthode normale
        return super().to_representation(data)


# Exemple d'utilisation combinée

class OptimizedProduitSerializer(
    CachedSerializerMixin,
    LazySerializerMixin,
    MinimalSerializerMixin,
    DynamicFieldsSerializer
):
    """
    Serializer produit avec toutes les optimisations.
    """
    
    cache_timeout = 600  # 10 minutes
    minimal_fields = ['id', 'nom', 'code_barre', 'prix_min']
    
    class Meta:
        model = None  # À définir dans la sous-classe
        fields = '__all__'
    
    @classmethod
    def setup_eager_loading(cls, queryset):
        """Précharger les relations."""
        return queryset.select_related(
            'categorie',
            'marque'
        ).prefetch_related(
            'prix'
        )
