from django.urls import path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'utilisateurs'

router = DefaultRouter()
router.register(r'utilisateurs', views.UtilisateurViewSet, basename='utilisateurs')
router.register(r'profils', views.ProfilViewSet, basename='profils')
router.register(r'abonnements', views.AbonnementViewSet, basename='abonnements')

urlpatterns = [
    path('api/', include(router.urls)),
    # Déplacer les URLs d'auth DRF sous un préfixe différent pour éviter de masquer /api/auth/login/
    path('api/auth/session/', include('rest_framework.urls', namespace='rest_framework')),
    # Nouvelles routes d'auth sans 2FA
    path('api/auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('api/auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('api/auth/activate/', views.ActivateView.as_view(), name='auth-activate'),
    path('activate/<str:uid>/<str:token>/', views.web_activate_uid_page, name='web-activate-uid'),
    # Endpoint /api/auth/me/ pour compatibilité frontend (alias vers /api/utilisateurs/moi/)
    path('api/auth/me/', views.auth_me_view, name='auth-me'),
    # Endpoint pour vérifier la validité du token
    path('api/auth/verify/', views.verify_token, name='auth-verify'),
    # Endpoints de réinitialisation de mot de passe
    path('api/auth/password/reset/', views.demander_reset_mot_de_passe, name='auth-password-reset'),
    path('api/auth/password/reset/verify/<str:token>/', views.verifier_token_reset_view, name='auth-password-reset-verify'),
    path('api/auth/password/reset/confirm/<str:token>/', views.confirmer_reset_mot_de_passe, name='auth-password-reset-confirm'),
    path('api/auth/password/change/', views.changer_mot_de_passe, name='auth-password-change'),
    # Anciens endpoints (pour compatibilité)
    path('api/auth/mot-de-passe/demander/', views.demander_reset_mot_de_passe, name='auth-mot-de-passe-demander'),
    path('api/auth/mot-de-passe/confirmer/<str:token>/', views.confirmer_reset_mot_de_passe, name='auth-mot-de-passe-confirmer'),
    # Endpoints de connexion sociale (OAuth)
    path('api/auth/google/', views.google_login, name='auth-google'),
    path('api/auth/facebook/', views.facebook_login, name='auth-facebook'),
    path('api/auth/apple/', views.apple_login, name='auth-apple'),
    # Note: JWT endpoints sont définis dans config/urls.py sous api/auth/token/
]

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