"""
Commande Django pour diagnostiquer les endpoints et identifier les erreurs.

Usage:
    python manage.py diagnostic_endpoints
    railway run python manage.py diagnostic_endpoints
"""
from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from apps.produits.models import Produit, Prix, Categorie
from apps.magasins.models import Magasin

User = get_user_model()


class Command(BaseCommand):
    help = "Diagnostique les endpoints de l'API et identifie les erreurs"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Diagnostic des Endpoints API'))
        self.stdout.write("=" * 60)
        
        client = Client()
        
        endpoints = [
            ('Produits (base)', '/api/produits/produits/'),
            ('Produits populaires', '/api/produits/produits/populaires/'),
            ('Produits tous', '/api/produits/produits/tous/'),
            ('Produits défiscalisés', '/api/produits/produits/defiscalises/'),
            ('Produits homologués', '/api/produits/produits/homologues/'),
            ('Catégories', '/api/produits/categories/'),
            ('Catégories racines', '/api/produits/categories/racines/'),
            ('Magasins', '/api/magasins/magasins/'),
            ('Prix', '/api/produits/prix/'),
            ('Prix promotions', '/api/produits/prix/promotions/'),
            ('Stats prix', '/api/stats/prix/'),
            ('Stats prix (alt)', '/api/produits/statistiques-prix/'),
            ('Stats homologations', '/api/produits/homologations-stats/'),
        ]
        
        results = []
        for name, url in endpoints:
            result = self.test_endpoint(client, url, name)
            results.append((name, url, result))
            status_icon = result['status']
            self.stdout.write(
                f"{status_icon} {name:30} {str(result['code']):10} {result['type']:20} {result['count']}"
            )
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("\n📊 Statistiques de la base de données:"))
        self.stdout.write(f"   - Produits: {Produit.objects.count()}")
        self.stdout.write(f"   - Produits actifs: {Produit.objects.filter(est_actif=True).count()}")
        self.stdout.write(f"   - Prix: {Prix.objects.count()}")
        self.stdout.write(f"   - Prix disponibles: {Prix.objects.filter(est_disponible=True).count()}")
        self.stdout.write(f"   - Catégories: {Categorie.objects.count()}")
        self.stdout.write(f"   - Magasins: {Magasin.objects.count()}")
        
        # Vérifier les problèmes potentiels
        self.stdout.write(self.style.WARNING("\n🔍 Vérifications:"))
        
        produits_sans_categorie = Produit.objects.filter(categorie__isnull=True).count()
        if produits_sans_categorie > 0:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Produits sans catégorie: {produits_sans_categorie}"))
        
        produits_sans_prix = Produit.objects.filter(prix__isnull=True, est_actif=True).count()
        if produits_sans_prix > 0:
            self.stdout.write(self.style.WARNING(f"   ⚠️  Produits actifs sans prix: {produits_sans_prix}"))
        
        prix_sans_produit = Prix.objects.filter(produit__isnull=True).count()
        if prix_sans_produit > 0:
            self.stdout.write(self.style.ERROR(f"   ❌ Prix sans produit: {prix_sans_produit}"))
        
        prix_sans_magasin = Prix.objects.filter(magasin__isnull=True).count()
        if prix_sans_magasin > 0:
            self.stdout.write(self.style.ERROR(f"   ❌ Prix sans magasin: {prix_sans_magasin}"))
        
        # Résumé
        success_count = sum(1 for _, _, r in results if r['status'] == '✅')
        error_count = sum(1 for _, _, r in results if r['status'] == '❌')
        
        self.stdout.write(self.style.SUCCESS(f"\n📊 Résumé:"))
        self.stdout.write(f"   ✅ Endpoints OK: {success_count}")
        self.stdout.write(f"   ❌ Endpoints en erreur: {error_count}")
    
    def test_endpoint(self, client, url, name):
        """Teste un endpoint et retourne le résultat"""
        try:
            response = client.get(url)
            status = response.status_code
            
            # Vérifier si c'est du HTML (erreur)
            content_type = response.get('Content-Type', '')
            is_html = 'text/html' in content_type or response.content[:100].startswith(b'<!DOCTYPE') or response.content[:100].startswith(b'<html')
            
            if status == 200 and not is_html:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        count = len(data.get('results', [])) if 'results' in data else data.get('count', 0)
                    elif isinstance(data, list):
                        count = len(data)
                    else:
                        count = 1
                    return {
                        'status': '✅',
                        'code': status,
                        'count': count,
                        'type': 'JSON'
                    }
                except:
                    return {
                        'status': '⚠️',
                        'code': status,
                        'count': 'N/A',
                        'type': 'Non-JSON'
                    }
            elif is_html:
                return {
                    'status': '❌',
                    'code': status,
                    'count': 'HTML',
                    'type': 'Erreur HTML'
                }
            else:
                return {
                    'status': '❌',
                    'code': status,
                    'count': 'Erreur',
                    'type': f'HTTP {status}'
                }
        except Exception as e:
            return {
                'status': '❌',
                'code': 'Exception',
                'count': str(e)[:50],
                'type': 'Exception'
            }

