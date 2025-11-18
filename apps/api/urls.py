from django.urls import path
from .views import (
    health, 
    search_produits, 
    autocomplete_produits, 
    homologations_stats, 
    compare_offers,
    stats_prix,
    TestConnectionView
)
from .views_nearby import prix_proches_public

urlpatterns = [
    path('health/', health, name='api-health'),
    path('test-connection/', TestConnectionView.as_view(), name='api-test-connection'),
    path('search/produits/', search_produits, name='api-search-produits'),
    path('search/autocomplete/', autocomplete_produits, name='api-autocomplete-produits'),
    path('homologations-stats/', homologations_stats, name='api-homologations-stats'),
    path('compare/', compare_offers, name='api-compare-offers'),
    path('nearby/prix/', prix_proches_public, name='api-nearby-prix'),
    path('stats/prix/', stats_prix, name='api-stats-prix'),
]
