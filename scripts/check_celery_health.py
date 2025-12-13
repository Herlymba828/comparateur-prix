#!/usr/bin/env python
"""
Health check pour Celery Worker et Beat
Vérifie que les processus sont actifs et fonctionnels
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from celery import Celery
from datetime import datetime, timedelta
import logging

try:
    from django_celery_beat.models import PeriodicTask
    HAS_BEAT = True
except ImportError:
    HAS_BEAT = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_worker_health():
    """Vérifie la santé du Worker"""
    try:
        from config.celery import app
        
        # Inspecter les workers actifs
        inspect = app.control.inspect()
        
        # Workers actifs
        active = inspect.active()
        if not active:
            logger.error("❌ Aucun worker actif détecté")
            return False
        
        logger.info(f"✅ Workers actifs: {list(active.keys())}")
        
        # Tâches en cours
        for worker, tasks in active.items():
            logger.info(f"   Worker {worker}: {len(tasks)} tâches en cours")
        
        # Stats des workers
        stats = inspect.stats()
        if stats:
            for worker, stat in stats.items():
                logger.info(f"   {worker}: {stat.get('total', 'N/A')} tâches totales")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification Worker: {e}")
        return False

def check_beat_health():
    """Vérifie la santé de Beat"""
    try:
        if not HAS_BEAT:
            logger.warning("⚠️ django-celery-beat non installé, vérification Beat ignorée")
            return True
        
        # Vérifier les tâches périodiques
        tasks = PeriodicTask.objects.filter(enabled=True)
        logger.info(f"✅ Tâches périodiques actives: {tasks.count()}")
        
        for task in tasks:
            logger.info(f"   - {task.name}: {task.crontab or task.interval}")
            
            # Vérifier la dernière exécution
            if task.last_run_at:
                time_since = datetime.now(task.last_run_at.tzinfo) - task.last_run_at
                logger.info(f"     Dernière exécution: il y a {time_since}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur vérification Beat: {e}")
        return False

def check_redis_connection():
    """Vérifie la connexion Redis"""
    try:
        from django.core.cache import cache
        
        # Test de connexion
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        
        if result == 'ok':
            logger.info("✅ Redis connecté et fonctionnel")
            return True
        else:
            logger.error("❌ Redis ne répond pas correctement")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur connexion Redis: {e}")
        return False

def main():
    logger.info("🔍 Vérification de la santé de Celery...")
    
    results = {
        'redis': check_redis_connection(),
        'worker': check_worker_health(),
        'beat': check_beat_health()
    }
    
    logger.info("\n📊 RÉSUMÉ:")
    for service, status in results.items():
        icon = "✅" if status else "❌"
        logger.info(f"{icon} {service.upper()}: {'OK' if status else 'ERREUR'}")
    
    # Exit code basé sur les résultats
    if all(results.values()):
        logger.info("\n✅ Tous les services Celery sont opérationnels")
        sys.exit(0)
    else:
        logger.error("\n❌ Certains services Celery ont des problèmes")
        sys.exit(1)

if __name__ == '__main__':
    main()
