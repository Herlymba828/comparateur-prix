import django_filters
from .models import HistoriqueRecommandation, FeedbackRecommandation

class HistoriqueRecommandationFilter(django_filters.FilterSet):
    date_min = django_filters.DateFilter(field_name='date_creation', lookup_expr='gte')
    date_max = django_filters.DateFilter(field_name='date_creation', lookup_expr='lte')
    score_min = django_filters.NumberFilter(field_name='score_confiance', lookup_expr='gte')
    algorithme = django_filters.ChoiceFilter(choices=HistoriqueRecommandation.ALGORITHME_CHOICES)
    
    class Meta:
        model = HistoriqueRecommandation
        fields = ['algorithme_utilise', 'a_ete_clique']

class FeedbackRecommandationFilter(django_filters.FilterSet):
    date_min = django_filters.DateFilter(field_name='date_feedback', lookup_expr='gte')
    date_max = django_filters.DateFilter(field_name='date_feedback', lookup_expr='lte')
    note_min = django_filters.NumberFilter(field_name='note_utilisateur', lookup_expr='gte')
    
    class Meta:
        model = FeedbackRecommandation
        fields = ['note_utilisateur', 'aime']