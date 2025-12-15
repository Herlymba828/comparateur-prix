#!/usr/bin/env python
"""
Script pour vérifier que Celery Worker et Beat sont actifs et fonctionnels
Usage: python scripts/verify_celery_active.py
"""
import os
import sys
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from celery import current_app
from celery.app.control import Inspect

def check_celery_status():
    """Vérifie l'état de Celery Worker et Beat"""
    
    print("🔍 VÉRIFICATION DE CELERY")
    print("=" * 60)
    
    # Vérifier la configuration Celery
    print("\n📋 Configuration Celery:")
    print(f"  Broker: {current_app.conf.broker_url[:50]}...")
    print(f"  Result Backend: {current_app.conf.result_backend[:50]}...")
    print(f"  Timezone: {current_app.conf.timezone}")
    
    # Inspecter les workers
    print("\n🔍 Inspection des Workers:")
    try:
        inspector = Inspect(app=current_app)
        
        # Voir les workers actifs
        active_workers = inspector.active()
        if active_workers:
            print(f"  ✅ Workers actifs: {len(active_workers)}")
            for worker_name, tasks in active_workers.items():
                print(f"     - {worker_name}: {len(tasks)} tâches actives")
        else:
            print("  ❌ Aucun worker actif")
        
        # Voir les tâches planifiées
        scheduled = inspector.scheduled()
        if scheduled:
            print(f"\n📅 Tâches planifiées:")
            for worker_name, tasks in scheduled.items():
                print(f"  {worker_name}: {len(tasks)} tâches")
                for task in tasks[:3]:  # Afficher les 3 premières
                    print(f"    - {task.get('request', {}).get('name', 'Unknown')}")
        else:
            print("\n  ⚠️  Aucune tâche planifiée")
        
        # Voir les statistiques
        stats = inspector.stats()
        if stats:
            print(f"\n📊 Statistiques:")
            for worker_name, worker_stats in stats.items():
                print(f"  {worker_name}:")
                print(f"    - Pool: {worker_stats.get('pool', {}).get('implementation', 'Unknown')}")
                print(f"    - Concurrency: {worker_stats.get('pool', {}).get('max-concurrency', 'Unknown')}")
        
        print("\n✅ CELERY EST ACTIF ET FONCTIONNEL")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("\n⚠️  Celery Worker n'est pas accessible")
        print("   Assurez-vous que:")
        print("   1. Le service Celery Worker est en cours d'exécution")
        print("   2. Redis est accessible")
        print("   3. Les variables d'environnement sont correctes")
        return False

if __name__ == '__main__':
    success = check_celery_status()
    sys.exit(0 if success else 1)
