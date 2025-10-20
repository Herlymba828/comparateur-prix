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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
try:
    from rest_framework_simplejwt.views import (
        TokenObtainPairView,
        TokenRefreshView,
    )
except Exception:  # simplejwt non installé
    TokenObtainPairView = TokenRefreshView = None

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('api/produits/', include('apps.produits.urls')),
    path('api/magasins/', include('apps.magasins.urls')),
    # Important: include utilisateurs URLs at root so their internal 'api/' prefixes map correctly
    path('', include('apps.utilisateurs.urls')),
    path('api/recommandations/', include('apps.recommandations.urls')),
    path('api/analyses/', include('apps.analyses.urls')),
    path('api/', include('apps.api.urls')),
    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Social OAuth (social-auth-app-django)
    path('oauth/', include('social_django.urls', namespace='social')),
]

# Racine: Swagger UI seulement en DEBUG
if settings.DEBUG:
    urlpatterns.insert(1, path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui-root'))

# JWT endpoints (SimpleJWT) seulement si activé
if getattr(settings, 'USE_JWT_AUTH', False) and TokenObtainPairView and TokenRefreshView:
    urlpatterns += [
        path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
        path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]
