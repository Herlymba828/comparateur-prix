import django_filters
from django.db.models import Q, Exists, OuterRef
from .models import Produit, Categorie, Marque, UniteMesure, Prix, AlertePrix, SuggestionPrix, HomologationProduit


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
    # Filtres de prix utilisant les annotations du queryset
    prix_min = django_filters.NumberFilter(method='filter_prix_min')
    prix_max = django_filters.NumberFilter(method='filter_prix_max')
    unite_mesure = django_filters.ModelChoiceFilter(field_name='unite_mesure', queryset=UniteMesure.objects.all())
    
    # Filtre pour la recherche par catégorie et sous-catégories
    categorie_etendue = django_filters.ModelChoiceFilter(
        method='filter_categorie_etendue',
        queryset=Categorie.objects.all(),
        label="Catégorie (incluant les sous-catégories)"
    )
    
    # Filtres pour produits défiscalisés et homologués
    est_defiscalise = django_filters.BooleanFilter(method='filter_est_defiscalise')
    est_homologue = django_filters.BooleanFilter(method='filter_est_homologue')
    
    class Meta:
        model = Produit
        fields = ['nom', 'code_barre', 'categorie', 'marque', 'unite_mesure']
    
    def filter_prix_min(self, queryset, name, value):
        """Filtre par prix minimum en utilisant l'annotation prix_moyen_agg"""
        if value is not None:
            return queryset.filter(prix_moyen_agg__gte=value)
        return queryset
    
    def filter_prix_max(self, queryset, name, value):
        """Filtre par prix maximum en utilisant l'annotation prix_moyen_agg"""
        if value is not None:
            return queryset.filter(prix_moyen_agg__lte=value)
        return queryset
    
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
    
    def filter_est_defiscalise(self, queryset, name, value):
        """Filtre les produits défiscalisés (basé sur la catégorie ou autres critères)"""
        if value is None:
            return queryset
        
        # Logique: produits défiscalisés sont généralement dans certaines catégories
        # Vous pouvez ajuster cette logique selon vos besoins métier
        # Exemple: catégories spécifiques ou un champ dédié si ajouté au modèle
        categories_defiscalisees = ['Alimentaire', 'Médicament', 'Équipement médical']
        
        if value:
            # Produits défiscalisés: correspondance par nom de catégorie ou sous-catégorie
            return queryset.filter(
                Q(categorie__nom__in=categories_defiscalisees) |
                Q(categorie__sous_categories__nom__in=categories_defiscalisees)
            ).distinct()
        else:
            # Produits non défiscalisés
            return queryset.exclude(
                Q(categorie__nom__in=categories_defiscalisees) |
                Q(categorie__sous_categories__nom__in=categories_defiscalisees)
            )
    
    def filter_est_homologue(self, queryset, name, value):
        """Filtre les produits homologués (correspondance avec HomologationProduit)"""
        if value is None:
            return queryset
        
        # Vérifier si un produit correspond à un HomologationProduit par nom ou code-barres
        if value:
            # Produits homologués: correspondance par nom (approximative) ou code-barres
            homologations = HomologationProduit.objects.filter(
                Q(nom__iexact=OuterRef('nom')) |
                Q(nom__icontains=OuterRef('nom'))
            )
            return queryset.annotate(
                est_homologue_agg=Exists(homologations)
            ).filter(est_homologue_agg=True)
        else:
            # Produits non homologués
            homologations = HomologationProduit.objects.filter(
                Q(nom__iexact=OuterRef('nom')) |
                Q(nom__icontains=OuterRef('nom'))
            )
            return queryset.annotate(
                est_homologue_agg=Exists(homologations)
            ).filter(est_homologue_agg=False)


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