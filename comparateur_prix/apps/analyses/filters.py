import django_filters
from .models import AnalysePrix, AnalysisResult, PriceAggregate, AnalysisType

class AnalysePrixFilter(django_filters.FilterSet):
    type_analyse = django_filters.ChoiceFilter(choices=AnalysePrix.TYPE_ANALYSE_CHOICES)
    date_debut_periode = django_filters.DateFilter(field_name='date_debut_periode', lookup_expr='gte')
    date_fin_periode = django_filters.DateFilter(field_name='date_fin_periode', lookup_expr='lte')
    date_creation = django_filters.DateFromToRangeFilter()
    
    class Meta:
        model = AnalysePrix
        fields = ['type_analyse', 'utilisateur', 'date_debut_periode', 'date_fin_periode', 'date_creation']

class AnalysisResultFilter(django_filters.FilterSet):
    type = django_filters.ChoiceFilter(choices=AnalysisType.choices)
    calcule_le = django_filters.DateFromToRangeFilter()
    
    class Meta:
        model = AnalysisResult
        fields = ['type', 'produit', 'categorie', 'ville', 'region', 'calcule_le']

class PriceAggregateFilter(django_filters.FilterSet):
    fenetre_debut = django_filters.DateTimeFilter(field_name='fenetre_debut', lookup_expr='gte')
    fenetre_fin = django_filters.DateTimeFilter(field_name='fenetre_fin', lookup_expr='lte')
    
    class Meta:
        model = PriceAggregate
        fields = ['produit', 'categorie', 'ville', 'region', 'fenetre_debut', 'fenetre_fin']