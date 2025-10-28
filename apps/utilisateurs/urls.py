from django.urls import path, include
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import TokenRefreshView
from .tokens import EmailTokenObtainPairView

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
    # SimpleJWT (token via email uniquement)
    path('api/token/', EmailTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
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