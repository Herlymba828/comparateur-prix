from django.urls import path
from .views import health, search_produits, autocomplete_produits, homologations_stats

urlpatterns = [
    path('health/', health, name='api-health'),
    path('search/produits/', search_produits, name='api-search-produits'),
    path('search/autocomplete/', autocomplete_produits, name='api-autocomplete-produits'),
    path('homologations-stats/', homologations_stats, name='api-homologations-stats'),
    
]
