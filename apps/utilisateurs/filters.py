import django_filters
from django.utils.translation import gettext_lazy as _
from django.db import models
from .models import Utilisateur, Abonnement

class UtilisateurFilter(django_filters.FilterSet):
    """Filtres avancés pour les utilisateurs"""
    
    type_utilisateur = django_filters.ChoiceFilter(
        choices=Utilisateur.TypesUtilisateur.choices
    )
    niveau_fidelite = django_filters.NumberFilter(
        field_name='niveau_fidelite',
        lookup_expr='exact'
    )
    niveau_fidelite_min = django_filters.NumberFilter(
        field_name='niveau_fidelite',
        lookup_expr='gte',
        label=_('Niveau fidélité minimum')
    )
    niveau_fidelite_max = django_filters.NumberFilter(
        field_name='niveau_fidelite',
        lookup_expr='lte',
        label=_('Niveau fidélité maximum')
    )
    est_client_fidele = django_filters.BooleanFilter(
        field_name='niveau_fidelite',
        method='filter_est_client_fidele',
        label=_('Client fidèle')
    )
    total_achats_min = django_filters.NumberFilter(
        field_name='total_achats',
        lookup_expr='gte',
        label=_('Total achats minimum')
    )
    total_achats_max = django_filters.NumberFilter(
        field_name='total_achats',
        lookup_expr='lte',
        label=_('Total achats maximum')
    )
    date_creation_min = django_filters.DateFilter(
        field_name='date_creation', 
        lookup_expr='gte',
        label=_('Date de création minimum')
    )
    date_creation_max = django_filters.DateFilter(
        field_name='date_creation', 
        lookup_expr='lte',
        label=_('Date de création maximum')
    )
    code_postal = django_filters.CharFilter(
        field_name='code_postal',
        lookup_expr='icontains'
    )
    ville = django_filters.CharFilter(
        field_name='ville',
        lookup_expr='icontains'
    )
    has_abonnement = django_filters.BooleanFilter(
        field_name='abonnement',
        method='filter_has_abonnement',
        label=_('A un abonnement actif')
    )
    
    class Meta:
        model = Utilisateur
        fields = [
            'type_utilisateur', 'est_verifie', 'is_active',
            'code_postal', 'ville', 'niveau_fidelite'
        ]
    
    def filter_est_client_fidele(self, queryset, name, value):
        """Filtre les clients fidèles (niveau >= 3)"""
        if value:
            return queryset.filter(niveau_fidelite__gte=3)
        return queryset.filter(niveau_fidelite__lt=3)
    
    def filter_has_abonnement(self, queryset, name, value):
        """Filtre les utilisateurs avec abonnement actif"""
        from django.utils import timezone
        if value:
            return queryset.filter(
                abonnement__est_actif=True,
                abonnement__date_fin__gt=timezone.now()
            )
        return queryset.filter(
            models.Q(abonnement__isnull=True) |
            models.Q(abonnement__est_actif=False) |
            models.Q(abonnement__date_fin__lte=timezone.now())
        )
    
    @property
    def qs(self):
        queryset = super().qs
        return queryset.select_related('profil', 'abonnement')

class AbonnementFilter(django_filters.FilterSet):
    """Filtres pour les abonnements"""
    
    type_abonnement = django_filters.ChoiceFilter(
        choices=Abonnement.TypeAbonnement.choices
    )
    est_actif = django_filters.BooleanFilter(field_name='est_actif')
    est_valide = django_filters.BooleanFilter(method='filter_est_valide')
    date_debut_min = django_filters.DateFilter(
        field_name='date_debut', 
        lookup_expr='gte'
    )
    date_debut_max = django_filters.DateFilter(
        field_name='date_debut', 
        lookup_expr='lte'
    )
    date_fin_min = django_filters.DateFilter(
        field_name='date_fin', 
        lookup_expr='gte'
    )
    date_fin_max = django_filters.DateFilter(
        field_name='date_fin', 
        lookup_expr='lte'
    )
    
    class Meta:
        model = Abonnement
        fields = ['type_abonnement', 'est_actif']
    
    def filter_est_valide(self, queryset, name, value):
        """Filtre les abonnements valides"""
        from django.utils import timezone
        if value:
            return queryset.filter(
                est_actif=True,
                date_fin__gt=timezone.now()
            )
        return queryset.filter(
            models.Q(est_actif=False) |
            models.Q(date_fin__lte=timezone.now())
        )

class HistoriqueRemisesFilter(django_filters.FilterSet):
    """Filtres pour l'historique des remises"""
    
    date_application_min = django_filters.DateTimeFilter(
        field_name='date_application', 
        lookup_expr='gte'
    )
    date_application_max = django_filters.DateTimeFilter(
        field_name='date_application', 
        lookup_expr='lte'
    )
    type_remise = django_filters.ChoiceFilter(
        choices=[
            ('fidelite', 'Fidélité'),
            ('abonnement', 'Abonnement'),
            ('promotion', 'Promotion'),
            ('combinee', 'Combinée')
        ]
    )
    pourcentage_remise_min = django_filters.NumberFilter(
        field_name='pourcentage_remise',
        lookup_expr='gte'
    )
    pourcentage_remise_max = django_filters.NumberFilter(
        field_name='pourcentage_remise',
        lookup_expr='lte'
    )
    
    class Meta:
        model = HistoriqueRemises
        fields = ['type_remise', 'produit']