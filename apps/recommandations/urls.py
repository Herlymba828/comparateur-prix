from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'historique', views.HistoriqueRecommandationViewSet, basename='historique-recommandation')
router.register(r'feedback', views.FeedbackRecommandationViewSet, basename='feedback-recommandation')
router.register(r'recommandations', views.RecommandationViewSet, basename='recommandations')
router.register(r'modeles-ml', views.ModeleMLViewSet, basename='modeles-ml')

urlpatterns = [
    # Le préfixe 'api/recommandations/' est déjà dans config/urls.py
    path('', include(router.urls)),
    path('statut-modeles/', views.statut_modeles, name='statut-modeles'),
    
    # Routes directes pour les actions (le router génère /recommandations/{action}/ mais le frontend attend /{action}/)
    # Utiliser la vue fonction pour pour_moi (authentification garantie)
    path('pour_moi/', 
         views.recommandations_pour_moi, 
         name='recommandations-pour-moi'),
    # Utiliser la vue fonction pour populaires (accès public garanti)
    path('populaires/', views.recommandations_populaires, name='recommandations-populaires'),
    # Utiliser la vue fonction pour pour_produit (accès public garanti)
    path('pour_produit/', views.recommandations_pour_produit, name='recommandations-pour-produit'),
    
    # URLs dépréciées (maintenues pour la compatibilité)
    path('recommandations/utilisateur/', 
         views.recommandations_pour_moi, 
         name='recommandations-utilisateur-legacy'),
    path('recommandations/produit/<int:produit_id>/', 
         views.RecommandationViewSet.as_view({'get': 'pour_produit'}), 
         name='recommandations-produit-legacy'),
    
    # Alias pour compatibilité frontend
    path('reco/pour-vous/', 
         views.recommandations_pour_moi, 
         name='reco-pour-vous'),
    # Utiliser la vue fonction pour tendances (accès public garanti)
    path('reco/tendances/', views.recommandations_populaires, name='reco-tendances'),
]