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
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Pages HTML (templates)
    path('', TemplateView.as_view(template_name='index.html'), name='page-index'),
    path('produits/', TemplateView.as_view(template_name='produits.html'), name='page-produits'),
    path('magasins/', TemplateView.as_view(template_name='magasins.html'), name='page-magasins'),
    path('proximite/', TemplateView.as_view(template_name='proximite.html'), name='page-proximite'),
    path('recommandations/', TemplateView.as_view(template_name='recommandations.html'), name='page-recommandations'),
    path('analyses/', TemplateView.as_view(template_name='analyses.html'), name='page-analyses'),
    path('connexion/', TemplateView.as_view(template_name='connexion.html'), name='page-connexion'),
    path('inscription/', TemplateView.as_view(template_name='inscription.html'), name='page-inscription'),
    # Composants (utilisés par main.js via fetch)
    path('components/header.html', TemplateView.as_view(template_name='components/header.html'), name='component-header'),
    path('components/footer.html', TemplateView.as_view(template_name='components/footer.html'), name='component-footer'),
    path('api/produits/', include('apps.produits.urls')),
    path('api/magasins/', include('apps.magasins.urls')),
    path('api/utilisateurs/', include('apps.utilisateurs.urls')),
    path('api/recommandations/', include('apps.recommandations.urls')),
    path('api/analyses/', include('apps.analyses.urls')),
    path('api/', include('apps.api.urls')),
    # OpenAPI schema & docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # JWT endpoints (SimpleJWT)
    path('api/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Social OAuth (social-auth-app-django)
    path('oauth/', include('social_django.urls', namespace='social')),
]
