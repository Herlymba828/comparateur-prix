from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'utilisateurs'

router = DefaultRouter()
router.register(r'utilisateurs', views.UtilisateurViewSet, basename='utilisateurs')
router.register(r'profils', views.ProfilViewSet, basename='profils')
router.register(r'abonnements', views.AbonnementViewSet, basename='abonnements')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # URLs supplémentaires pour les fonctionnalités spécifiques
    path('api/utilisateurs/moi/statistiques-fidelite/', 
         views.UtilisateurViewSet.as_view({'get': 'statistiques_fidelite'}), 
         name='statistiques-fidelite'),
    path('api/utilisateurs/moi/historique-remises/', 
         views.UtilisateurViewSet.as_view({'get': 'historique_remises'}), 
         name='historique-remises'),
    path('api/utilisateurs/moi/appliquer-remise/', 
         views.UtilisateurViewSet.as_view({'post': 'appliquer_remise'}), 
         name='appliquer-remise'),
]

# URLs JWT personnalisées
jwt_urlpatterns = [
    path('api/auth/inscription/', 
         views.UtilisateurViewSet.as_view({'post': 'inscrire'}), 
         name='inscription'),
    path('api/auth/connexion/', 
         views.UtilisateurViewSet.as_view({'post': 'connecter'}), 
         name='connexion'),
    path('api/auth/changer-mot-de-passe/', 
         views.UtilisateurViewSet.as_view({'post': 'changer_mot_de_passe'}), 
         name='changer-mot-de-passe'),
    # Activation email
    path('api/auth/activation/confirmer/<str:token>/', 
         views.activer_compte, 
         name='activation-confirmer'),
    path('api/auth/activation/confirmer', 
         views.activer_compte_query, 
         name='activation-confirmer-query'),
    path('api/auth/activation/renvoyer/', 
         views.UtilisateurViewSet.as_view({'post': 'renvoyer_activation'}), 
         name='activation-renvoyer'),
    # Reset mot de passe
    path('api/auth/mot-de-passe/demander/', 
         views.demander_reset_mot_de_passe, 
         name='reset-demander'),
    path('api/auth/mot-de-passe/confirmer/<str:token>/', 
         views.confirmer_reset_mot_de_passe, 
         name='reset-confirmer'),
    # Social logins
    path('api/auth/google/', views.google_login, name='google-login'),
    path('api/auth/facebook/', views.facebook_login, name='facebook-login'),
    path('api/auth/apple/', views.apple_login, name='apple-login'),
]

urlpatterns += jwt_urlpatterns

# Session management endpoints
extra_patterns = [
    path('api/auth/sessions/', views.lister_sessions, name='sessions-list'),
    path('api/auth/sessions/revoke/', views.revoquer_session, name='sessions-revoke'),
    path('api/auth/logout_all/', views.logout_all, name='logout-all'),
]

urlpatterns += extra_patterns

# Universal/App Links web landing page
urlpatterns += [
    path('activate/<str:token>', views.web_activate_page, name='web-activate'),
]