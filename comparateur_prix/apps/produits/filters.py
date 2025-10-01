import django_filters
from django.db.models import Q
from .models import Produit, Categorie, Marque, UniteMesure, Prix, AlertePrix, SuggestionPrix


class CategorieFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.ModelChoiceFilter(queryset=Categorie.objects.all())
    est_racine = django_filters.BooleanFilter(method='filter_est_racine')
    
    class Meta:
        model = Categorie
        fields = ['nom', 'parent']
    
    def filter_est_racine(self, queryset, name, value):
        """Filtre les catégories racines"""
        if value:
            return queryset.filter(parent__isnull=True)
        return queryset.filter(parent__isnull=False)


class MarqueFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    pays_origine = django_filters.CharFilter(lookup_expr='icontains')
    has_site_web = django_filters.BooleanFilter(method='filter_has_site_web')
    
    class Meta:
        model = Marque
        fields = ['nom', 'pays_origine']
    
    def filter_has_site_web(self, queryset, name, value):
        """Filtre les marques avec/sans site web"""
        if value:
            return queryset.exclude(site_web='')
        return queryset.filter(site_web='')


class ProduitFilter(django_filters.FilterSet):
    nom = django_filters.CharFilter(lookup_expr='icontains')
    code_barre = django_filters.CharFilter(lookup_expr='exact')
    categorie = django_filters.ModelChoiceFilter(queryset=Categorie.objects.all())
    marque = django_filters.ModelChoiceFilter(queryset=Marque.objects.all())
    prix_min = django_filters.NumberFilter(field_name='prix__prix_actuel', lookup_expr='gte')
    prix_max = django_filters.NumberFilter(field_name='prix__prix_actuel', lookup_expr='lte')
    unite_mesure = django_filters.ModelChoiceFilter(field_name='unite_mesure', queryset=UniteMesure.objects.all())
    
    # Filtre pour la recherche par catégorie et sous-catégories
    categorie_etendue = django_filters.ModelChoiceFilter(
        method='filter_categorie_etendue',
        queryset=Categorie.objects.all(),
        label="Catégorie (incluant les sous-catégories)"
    )
    
    class Meta:
        model = Produit
        fields = ['nom', 'code_barre', 'categorie', 'marque', 'unite_mesure']
    
    def filter_categorie_etendue(self, queryset, name, value):
        """Filtre par catégorie en incluant les sous-catégories"""
        if not value:
            return queryset
        
        def get_sous_categories_ids(categorie):
            ids = [categorie.id]
            for sous_cat in categorie.sous_categories.all():
                ids.extend(get_sous_categories_ids(sous_cat))
            return ids
        
        categories_ids = get_sous_categories_ids(value)
        return queryset.filter(categorie_id__in=categories_ids)


class AlertePrixFilter(django_filters.FilterSet):
    produit = django_filters.NumberFilter(field_name='produit_id')
    est_active = django_filters.BooleanFilter(field_name='est_active')
    frequence = django_filters.CharFilter(field_name='frequence_verification', lookup_expr='exact')
    
    class Meta:
        model = AlertePrix
        fields = ['produit', 'est_active', 'frequence']


class SuggestionPrixFilter(django_filters.FilterSet):
    produit = django_filters.NumberFilter(field_name='produit_id')
    magasin = django_filters.NumberFilter(field_name='magasin_id')
    statut = django_filters.CharFilter(field_name='statut', lookup_expr='exact')
    date_min = django_filters.DateTimeFilter(field_name='date_creation', lookup_expr='gte')
    date_max = django_filters.DateTimeFilter(field_name='date_creation', lookup_expr='lte')

    class Meta:
        model = SuggestionPrix
        fields = ['produit', 'magasin', 'statut']


class PrixFilter(django_filters.FilterSet):
    produit = django_filters.NumberFilter(field_name='produit_id')
    magasin = django_filters.NumberFilter(field_name='magasin_id')
    est_promotion = django_filters.BooleanFilter(field_name='est_promotion')
    est_disponible = django_filters.BooleanFilter(field_name='est_disponible')
    prix_min = django_filters.NumberFilter(field_name='prix_actuel', lookup_expr='gte')
    prix_max = django_filters.NumberFilter(field_name='prix_actuel', lookup_expr='lte')
    categorie = django_filters.ModelChoiceFilter(field_name='produit__categorie', queryset=Categorie.objects.all())
    marque = django_filters.ModelChoiceFilter(field_name='produit__marque', queryset=Marque.objects.all())
    unite_mesure = django_filters.ModelChoiceFilter(field_name='produit__unite_mesure', queryset=UniteMesure.objects.all())

    class Meta:
        model = Prix
        fields = [
            'produit', 'magasin', 'est_promotion', 'est_disponible',
            'categorie', 'marque', 'unite_mesure'
        ]