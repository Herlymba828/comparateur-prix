"""
Script de benchmark pour mesurer les performances de l'API.
Usage: python scripts/benchmark_api.py [--url http://localhost:8000]
"""
import requests
import time
import statistics
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Ajouter le répertoire parent au path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


class APIBenchmark:
    """Classe pour benchmarker l'API."""
    
    def __init__(self, base_url='http://localhost:8000'):
        self.base_url = base_url.rstrip('/')
        self.results = {}
    
    def benchmark_endpoint(self, endpoint, method='GET', data=None, iterations=100):
        """
        Benchmarker un endpoint.
        
        Args:
            endpoint: Chemin de l'endpoint (ex: /api/produits/)
            method: Méthode HTTP
            data: Données pour POST/PUT
            iterations: Nombre d'itérations
        
        Returns:
            Dict avec les statistiques
        """
        print(f"\n🔍 Benchmark: {method} {endpoint}")
        print(f"   Itérations: {iterations}")
        
        url = f"{self.base_url}{endpoint}"
        durations = []
        errors = 0
        
        for i in range(iterations):
            try:
                start = time.time()
                
                if method == 'GET':
                    response = requests.get(url, timeout=30)
                elif method == 'POST':
                    response = requests.post(url, json=data, timeout=30)
                else:
                    raise ValueError(f"Méthode non supportée: {method}")
                
                duration = time.time() - start
                durations.append(duration)
                
                if response.status_code >= 400:
                    errors += 1
                
                # Afficher la progression
                if (i + 1) % 10 == 0:
                    print(f"   Progression: {i + 1}/{iterations}")
            
            except Exception as e:
                errors += 1
                print(f"   Erreur: {e}")
        
        # Calculer les statistiques
        if durations:
            stats = {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'errors': errors,
                'success_rate': (iterations - errors) / iterations * 100,
                'min': min(durations) * 1000,  # en ms
                'max': max(durations) * 1000,
                'mean': statistics.mean(durations) * 1000,
                'median': statistics.median(durations) * 1000,
                'stdev': statistics.stdev(durations) * 1000 if len(durations) > 1 else 0,
                'p95': sorted(durations)[int(len(durations) * 0.95)] * 1000,
                'p99': sorted(durations)[int(len(durations) * 0.99)] * 1000,
            }
        else:
            stats = {
                'endpoint': endpoint,
                'method': method,
                'iterations': iterations,
                'errors': errors,
                'success_rate': 0,
            }
        
        self.results[endpoint] = stats
        self.print_stats(stats)
        
        return stats
    
    def benchmark_concurrent(self, endpoint, method='GET', data=None, concurrent_users=10, requests_per_user=10):
        """
        Benchmarker avec des requêtes concurrentes.
        
        Args:
            endpoint: Chemin de l'endpoint
            method: Méthode HTTP
            data: Données pour POST/PUT
            concurrent_users: Nombre d'utilisateurs concurrents
            requests_per_user: Nombre de requêtes par utilisateur
        """
        print(f"\n🔍 Benchmark concurrent: {method} {endpoint}")
        print(f"   Utilisateurs concurrents: {concurrent_users}")
        print(f"   Requêtes par utilisateur: {requests_per_user}")
        
        url = f"{self.base_url}{endpoint}"
        durations = []
        errors = 0
        
        def make_request():
            """Faire une requête."""
            try:
                start = time.time()
                
                if method == 'GET':
                    response = requests.get(url, timeout=30)
                elif method == 'POST':
                    response = requests.post(url, json=data, timeout=30)
                else:
                    return None, True
                
                duration = time.time() - start
                
                if response.status_code >= 400:
                    return duration, True
                
                return duration, False
            
            except Exception:
                return None, True
        
        # Exécuter les requêtes en parallèle
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            futures = []
            
            for _ in range(concurrent_users * requests_per_user):
                futures.append(executor.submit(make_request))
            
            for future in as_completed(futures):
                duration, error = future.result()
                
                if error:
                    errors += 1
                elif duration:
                    durations.append(duration)
        
        # Calculer les statistiques
        total_requests = concurrent_users * requests_per_user
        
        if durations:
            stats = {
                'endpoint': endpoint,
                'method': method,
                'concurrent_users': concurrent_users,
                'total_requests': total_requests,
                'errors': errors,
                'success_rate': (total_requests - errors) / total_requests * 100,
                'min': min(durations) * 1000,
                'max': max(durations) * 1000,
                'mean': statistics.mean(durations) * 1000,
                'median': statistics.median(durations) * 1000,
                'throughput': total_requests / sum(durations),  # req/s
            }
        else:
            stats = {
                'endpoint': endpoint,
                'method': method,
                'concurrent_users': concurrent_users,
                'total_requests': total_requests,
                'errors': errors,
                'success_rate': 0,
            }
        
        self.print_stats(stats)
        
        return stats
    
    def print_stats(self, stats):
        """Afficher les statistiques."""
        print(f"\n   📊 Résultats:")
        print(f"      Taux de succès: {stats.get('success_rate', 0):.1f}%")
        
        if 'mean' in stats:
            print(f"      Temps moyen: {stats['mean']:.2f}ms")
            print(f"      Médiane: {stats['median']:.2f}ms")
            print(f"      Min: {stats['min']:.2f}ms")
            print(f"      Max: {stats['max']:.2f}ms")
            
            if 'p95' in stats:
                print(f"      P95: {stats['p95']:.2f}ms")
                print(f"      P99: {stats['p99']:.2f}ms")
            
            if 'throughput' in stats:
                print(f"      Débit: {stats['throughput']:.2f} req/s")
    
    def run_full_benchmark(self):
        """Exécuter un benchmark complet."""
        print("🚀 Démarrage du benchmark complet...")
        
        # Endpoints à tester
        endpoints = [
            ('/api/health/', 'GET', None, 100),
            ('/api/diagnostic/', 'GET', None, 50),
            ('/api/produits/produits/', 'GET', None, 50),
            ('/api/produits/categories/', 'GET', None, 50),
            ('/api/magasins/magasins/', 'GET', None, 50),
        ]
        
        for endpoint, method, data, iterations in endpoints:
            self.benchmark_endpoint(endpoint, method, data, iterations)
            time.sleep(1)  # Pause entre les tests
        
        # Test de charge
        print("\n" + "="*60)
        print("🔥 Test de charge")
        print("="*60)
        
        self.benchmark_concurrent(
            '/api/produits/produits/',
            concurrent_users=10,
            requests_per_user=10
        )
        
        # Rapport final
        self.print_final_report()
    
    def print_final_report(self):
        """Afficher le rapport final."""
        print("\n" + "="*60)
        print("📊 RAPPORT FINAL")
        print("="*60)
        
        if not self.results:
            print("Aucun résultat disponible")
            return
        
        # Trier par temps moyen
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1].get('mean', float('inf'))
        )
        
        print("\n🏆 Endpoints les plus rapides:")
        for endpoint, stats in sorted_results[:3]:
            if 'mean' in stats:
                print(f"   {endpoint}: {stats['mean']:.2f}ms")
        
        print("\n🐌 Endpoints les plus lents:")
        for endpoint, stats in sorted_results[-3:]:
            if 'mean' in stats:
                print(f"   {endpoint}: {stats['mean']:.2f}ms")
        
        # Statistiques globales
        all_means = [s['mean'] for s in self.results.values() if 'mean' in s]
        if all_means:
            print(f"\n📈 Statistiques globales:")
            print(f"   Temps moyen global: {statistics.mean(all_means):.2f}ms")
            print(f"   Médiane globale: {statistics.median(all_means):.2f}ms")


def main():
    """Point d'entrée principal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Benchmarker l\'API')
    parser.add_argument('--url', default='http://localhost:8000', help='URL de base de l\'API')
    parser.add_argument('--endpoint', help='Endpoint spécifique à tester')
    parser.add_argument('--iterations', type=int, default=100, help='Nombre d\'itérations')
    args = parser.parse_args()
    
    benchmark = APIBenchmark(base_url=args.url)
    
    if args.endpoint:
        # Tester un endpoint spécifique
        benchmark.benchmark_endpoint(args.endpoint, iterations=args.iterations)
    else:
        # Benchmark complet
        benchmark.run_full_benchmark()


if __name__ == '__main__':
    main()
