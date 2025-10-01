from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'historique', views.HistoriqueRecommandationViewSet, basename='historique-recommandation')
router.register(r'feedback', views.FeedbackRecommandationViewSet, basename='feedback-recommandation')
router.register(r'recommandations', views.RecommandationViewSet, basename='recommandations')
router.register(r'modeles-ml', views.ModeleMLViewSet, basename='modeles-ml')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/statut-modeles/', views.statut_modeles, name='statut-modeles'),
    
    # URLs dépréciées (maintenues pour la compatibilité)
    path('api/recommandations/utilisateur/', 
         views.RecommandationViewSet.as_view({'get': 'pour_moi'}), 
         name='recommandations-utilisateur-legacy'),
    path('api/recommandations/produit/<int:produit_id>/', 
         views.RecommandationViewSet.as_view({'get': 'pour_produit'}), 
         name='recommandations-produit-legacy'),
]