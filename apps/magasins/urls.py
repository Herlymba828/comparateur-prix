from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VueEnsembleRegion, VueEnsembleVille, VueEnsembleMagasin

router = DefaultRouter()
router.register(r'regions', VueEnsembleRegion, basename='region')
router.register(r'villes', VueEnsembleVille, basename='ville')
router.register(r'magasins', VueEnsembleMagasin, basename='magasin')

urlpatterns = [
    path('', include(router.urls)),
    path('regions/', VueEnsembleRegion.as_view({'get': 'list'}), name='regions-list'),
    path('regions/<int:pk>/', VueEnsembleRegion.as_view({'get': 'retrieve'}), name='regions-detail'),
    path('villes/', VueEnsembleVille.as_view({'get': 'list'}), name='villes-list'),
    path('villes/<int:pk>/', VueEnsembleVille.as_view({'get': 'retrieve'}), name='villes-detail'),
    path('magasins/', VueEnsembleMagasin.as_view({'get': 'list'}), name='magasins-list'),
    path('magasins/<int:pk>/', VueEnsembleMagasin.as_view({'get': 'retrieve'}), name='magasins-detail'),
]
