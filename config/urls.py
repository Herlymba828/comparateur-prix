"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
try:
    from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView,
    )
except Exception:  # simplejwt non installé
    TokenObtainPairView = TokenRefreshView = None

# Import des vues de recommandations pour les alias legacy
try:
    from apps.recommandations import views as reco_views
except ImportError:
    reco_views = None

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/produits/', include('apps.produits.urls')),
    path('api/magasins/', include('apps.magasins.urls')),
    # Important: include utilisateurs URLs at root so their internal 'api/' prefixes map correctly
    path('', include('apps.utilisateurs.urls')),
    path('api/recommandations/', include('apps.recommandations.urls')),
    path('api/analyses/', include('apps.analyses.urls')),
    path('api/', include('apps.api.urls')),
    # Alias global pour compatibilité frontend
    path('api/categories/', include('apps.produits.urls')),  # Redirige vers /api/produits/categories/
    # Alias pour compatibilité frontend (URLs alternatives)
    path('api/prix/', include('apps.produits.urls')),  # Redirige vers /api/produits/prix/
    path('api/magasin/', include('apps.magasins.urls')),  # Redirige vers /api/magasins/magasins/
    path('api/stores/', include('apps.magasins.urls')),  # Alias pour /api/magasins/magasins/
    # Alias legacy pour les recommandations (si les vues sont disponibles)
    *([
        path('api/reco/pour-vous/', reco_views.recommandations_pour_moi, name='reco-pour-vous-legacy'),
        path('api/reco/tendances/', reco_views.recommandations_populaires, name='reco-tendances-legacy'),
        path('api/reco/produits/<int:produit_id>/similaires/', reco_views.recommandations_pour_produit_url, name='reco-produits-similaires'),
    ] if reco_views else []),
    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Social OAuth (social-auth-app-django)
    path('oauth/', include('social_django.urls', namespace='social')),
]

# Vue pour la racine
def root_view(request):
    """Vue pour la racine qui redirige vers la documentation API.
    Cette vue ne nécessite pas de connexion à la base de données,
    ce qui permet à Railway de faire un health check même si la DB n'est pas configurée.
    """
    return JsonResponse({
        'message': 'Comparateur Prix API',
        'version': '1.0.0',
        'status': 'ok',  # Pour Railway health check
        'documentation': '/api/docs/',
        'health_check': '/api/health/',
        'endpoints': {
            'api_docs': '/api/docs/',
            'api_schema': '/api/schema/',
            'api_health': '/api/health/',
            'admin': f'/{settings.ADMIN_URL}',
        }
    })

# Racine: Swagger UI en DEBUG, vue JSON en production
if settings.DEBUG:
    urlpatterns.insert(0, path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-root'))
else:
    urlpatterns.insert(0, path('', root_view, name='root'))

# JWT endpoints (SimpleJWT) seulement si activé
if getattr(settings, 'USE_JWT_AUTH', False) and TokenObtainPairView and TokenRefreshView:
    urlpatterns += [
        path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]
