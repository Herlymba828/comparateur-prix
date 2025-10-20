from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'analyses', views.AnalysePrixViewSet, basename='analyse')
router.register(r'rapports', views.RapportAnalyseViewSet, basename='rapport')
router.register(r'indicateurs', views.IndicateurPerformanceViewSet, basename='indicateur')
router.register(r'resultats', views.AnalysisResultViewSet, basename='resultat')
router.register(r'aggregats', views.PriceAggregateViewSet, basename='aggregat')
router.register(r'analyses-optimisees', views.AnalyseOptimiseeViewSet, basename='analyse-optimisee')
try:
    # Optional graph analytics endpoints (available if models/serializers/viewsets are present)
    router.register(r'graph/snapshots', views.GraphSnapshotViewSet, basename='graph-snapshot')
    router.register(r'graph/nodes', views.NodeMetricViewSet, basename='graph-nodes')
    router.register(r'graph/edges', views.EdgeMetricViewSet, basename='graph-edges')
except AttributeError:
    pass

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/graph/latest/', views.latest_graph, name='graph-latest'),
    path('api/stats/prix/overview', views.stats_prix_overview, name='stats-prix-overview'),
    path('api/stats/magasins_plus_actifs', views.stats_magasins_plus_actifs, name='stats-magasins-plus-actifs'),
    path('api/stats/produits_plus_recherches', views.stats_produits_plus_recherches, name='stats-produits-plus-recherches'),
    path('api/stats/tendances', views.stats_tendances, name='stats-tendances'),
]