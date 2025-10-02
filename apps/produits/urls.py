from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'prix', views.PrixViewSet, basename='prix')
router.register(r'alertes-prix', views.AlertePrixViewSet, basename='alerteprix')
router.register(r'suggestions-prix', views.SuggestionPrixViewSet, basename='suggestion-prix')
router.register(r'comparaisons-prix', views.ComparaisonPrixViewSet, basename='comparaison-prix')
router.register(r'statistiques-prix', views.StatistiquesPrixViewSet, basename='statistiques-prix')
router.register(r'homologations-stats', views.HomologationsStatsViewSet, basename='homologations-stats')
router.register(r'offres', views.OffreViewSet, basename='offre')
router.register(r'categories', views.CategorieViewSet, basename='categorie')
router.register(r'marques', views.MarqueViewSet, basename='marque')
router.register(r'unites-mesure', views.UniteMesureViewSet, basename='unitemesure')
router.register(r'produits', views.ProduitViewSet, basename='produit')
router.register(r"avis", views.AvisProduitViewSet, basename='avis')
router.register(r'caracteristiques', views.CaracteristiqueProduitViewSet, basename='caracteristique')
router.register(r'statistiques-produits', views.StatistiquesProduitViewSet, basename='statistiques-produits')

urlpatterns = [
    path('', include(router.urls)),
]