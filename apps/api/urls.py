from django.urls import path
from .views import (
    health,
    test_simple,
    search_produits, 
    autocomplete_produits, 
    homologations_stats, 
    compare_offers,
    stats_prix,
    TestConnectionView
)
from .views_nearby import prix_proches_public
from .views_diagnostic import diagnostic_api, endpoints_list
from .views_admin import populate_database, reset_database, database_stats

urlpatterns = [
    path('health/', health, name='api-health'),
    path('test-simple/', test_simple, name='api-test-simple'),
    path('diagnostic/', diagnostic_api, name='api-diagnostic'),
    path('endpoints/', endpoints_list, name='api-endpoints'),
    path('test-connection/', TestConnectionView.as_view(), name='api-test-connection'),
    path('search/produits/', search_produits, name='api-search-produits'),
    path('search/autocomplete/', autocomplete_produits, name='api-autocomplete-produits'),
    path('homologations-stats/', homologations_stats, name='api-homologations-stats'),
    path('compare/', compare_offers, name='api-compare-offers'),
    path('nearby/prix/', prix_proches_public, name='api-nearby-prix'),
    path('stats/prix/', stats_prix, name='api-stats-prix'),
    # Alias pour stats homologations
    path('stats/homologations/', homologations_stats, name='api-stats-homologations'),
    
    # Admin endpoints (temporaires pour setup)
    path('admin/populate/', populate_database, name='api-admin-populate'),
    path('admin/reset/', reset_database, name='api-admin-reset'),
    path('admin/stats/', database_stats, name='api-admin-stats'),
]
