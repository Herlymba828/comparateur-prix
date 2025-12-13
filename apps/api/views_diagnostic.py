"""
Vues de diagnostic pour l'API.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db import connection
from django.conf import settings
from apps.produits.models import Produit, Categorie, Prix
from apps.magasins.models import Magasin
from apps.utilisateurs.models import Utilisateur
import sys

@api_view(['GET'])
@permission_classes([AllowAny])
def diagnostic_api(request):
    """
    Endpoint de diagnostic pour vérifier l'état du système.
    Accessible sans authentification pour faciliter le debugging.
    """
    diagnostic = {
        'status': 'ok',
        'version': '1.0.0',
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'debug_mode': settings.DEBUG,
        'database': {},
        'data': {},
        'endpoints': {},
        'issues': [],
        'recommendations': []
    }
    
    # Vérifier la connexion DB
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        diagnostic['database']['status'] = 'connected'
        diagnostic['database']['engine'] = connection.settings_dict['ENGINE'].split('.')[-1]
        # Convertir WindowsPath en string
        db_name = connection.settings_dict['NAME']
        diagnostic['database']['name'] = str(db_name) if db_name else 'N/A'
    except Exception as e:
        diagnostic['status'] = 'error'
        diagnostic['database']['status'] = 'disconnected'
        diagnostic['database']['error'] = str(e)
        diagnostic['issues'].append('Base de données inaccessible')
    
    # Vérifier les données
    try:
        nb_produits = Produit.objects.count()
        nb_categories = Categorie.objects.count()
        nb_magasins = Magasin.objects.count()
        nb_prix = Prix.objects.count()
        nb_users = Utilisateur.objects.count()
        
        diagnostic['data'] = {
            'produits': nb_produits,
            'categories': nb_categories,
            'magasins': nb_magasins,
            'prix': nb_prix,
            'utilisateurs': nb_users
        }
        
        # Détecter les problèmes
        if nb_produits == 0:
            diagnostic['issues'].append('Aucun produit en base de données')
            diagnostic['recommendations'].append('Exécuter: python manage.py seed_data --produits 100')
        
        if nb_categories == 0:
            diagnostic['issues'].append('Aucune catégorie en base de données')
            diagnostic['recommendations'].append('Exécuter: python manage.py init_categories')
        
        if nb_magasins == 0:
            diagnostic['issues'].append('Aucun magasin en base de données')
            diagnostic['recommendations'].append('Exécuter: python manage.py seed_data --magasins 10')
        
        if nb_prix == 0 and nb_produits > 0:
            diagnostic['issues'].append('Produits sans prix')
            diagnostic['recommendations'].append('Vérifier les données de prix')
        
    except Exception as e:
        diagnostic['status'] = 'error'
        diagnostic['data']['error'] = str(e)
        diagnostic['issues'].append(f'Erreur lors de la lecture des données: {str(e)}')
    
    # Endpoints disponibles
    diagnostic['endpoints'] = {
        'auth': {
            'register': '/api/auth/register/',
            'login': '/api/auth/login/',
            'me': '/api/auth/me/',
            'activate': '/api/auth/activate/'
        },
        'produits': {
            'list': '/api/produits/produits/',
            'tous': '/api/produits/produits/tous/',
            'populaires': '/api/produits/produits/populaires/',
            'categories': '/api/produits/categories/'
        },
        'magasins': {
            'list': '/api/magasins/magasins/',
            'nearby': '/api/magasins/magasins/nearby/'
        },
        'docs': {
            'swagger': '/api/docs/',
            'schema': '/api/schema/'
        }
    }
    
    # Statut global
    if diagnostic['issues']:
        diagnostic['status'] = 'warning'
    
    return Response(diagnostic)


@api_view(['GET'])
@permission_classes([AllowAny])
def endpoints_list(request):
    """
    Liste tous les endpoints disponibles avec leur méthode HTTP.
    """
    endpoints = {
        'authentication': [
            {'method': 'POST', 'path': '/api/auth/register/', 'description': 'Inscription'},
            {'method': 'POST', 'path': '/api/auth/login/', 'description': 'Connexion'},
            {'method': 'GET', 'path': '/api/auth/me/', 'description': 'Utilisateur actuel'},
            {'method': 'POST', 'path': '/api/auth/activate/', 'description': 'Activation compte'},
            {'method': 'POST', 'path': '/api/auth/token/', 'description': 'JWT tokens (si activé)'},
        ],
        'produits': [
            {'method': 'GET', 'path': '/api/produits/produits/', 'description': 'Liste produits'},
            {'method': 'GET', 'path': '/api/produits/produits/tous/', 'description': 'Tous les produits'},
            {'method': 'GET', 'path': '/api/produits/produits/populaires/', 'description': 'Produits populaires'},
            {'method': 'GET', 'path': '/api/produits/produits/defiscalises/', 'description': 'Produits défiscalisés'},
            {'method': 'GET', 'path': '/api/produits/categories/', 'description': 'Catégories'},
            {'method': 'GET', 'path': '/api/produits/prix/promotions/', 'description': 'Promotions'},
        ],
        'magasins': [
            {'method': 'GET', 'path': '/api/magasins/magasins/', 'description': 'Liste magasins'},
            {'method': 'GET', 'path': '/api/magasins/magasins/nearby/', 'description': 'Magasins proches'},
        ],
        'recommandations': [
            {'method': 'GET', 'path': '/api/recommandations/populaires/', 'description': 'Recommandations populaires'},
            {'method': 'GET', 'path': '/api/recommandations/pour-moi/', 'description': 'Recommandations personnalisées'},
        ],
        'utilitaires': [
            {'method': 'GET', 'path': '/api/health/', 'description': 'Health check'},
            {'method': 'GET', 'path': '/api/diagnostic/', 'description': 'Diagnostic système'},
            {'method': 'GET', 'path': '/api/endpoints/', 'description': 'Liste des endpoints'},
            {'method': 'GET', 'path': '/api/docs/', 'description': 'Documentation Swagger'},
            {'method': 'GET', 'path': '/api/schema/', 'description': 'Schéma OpenAPI'},
        ]
    }
    
    return Response(endpoints)
