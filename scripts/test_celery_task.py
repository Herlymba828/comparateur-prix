#!/usr/bin/env python
"""
Script pour tester l'envoi d'une tâche Celery
Usage: python scripts/test_celery_task.py
"""
import os
import sys
from pathlib import Path
import time

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from celery import current_app
from apps.utilisateurs.tasks import send_activation_code_email

def test_celery_task():
    """Teste l'envoi d'une tâche Celery"""
    
    print("🧪 TEST D'UNE TÂCHE CELERY")
    print("=" * 60)
    
    # Envoyer une tâche de test
    print("\n📤 Envoi d'une tâche de test...")
    try:
        # Envoyer une tâche d'email (sans vraiment l'envoyer)
        result = send_activation_code_email.delay(
            user_email="test@example.com",
            activation_code="123456"
        )
        
        print(f"✅ Tâche envoyée avec succès")
        print(f"   Task ID: {result.id}")
        print(f"   État initial: {result.state}")
        
        # Attendre un peu et vérifier l'état
        print("\n⏳ Attente de l'exécution (5 secondes)...")
        time.sleep(5)
        
        # Vérifier l'état final
        print(f"   État final: {result.state}")
        
        if result.state == 'SUCCESS':
            print(f"\n✅ TÂCHE EXÉCUTÉE AVEC SUCCÈS")
            print(f"   Résultat: {result.result}")
            return True
        elif result.state == 'PENDING':
            print(f"\n⚠️  Tâche en attente (Celery Worker peut ne pas être actif)")
            return False
        elif result.state == 'FAILURE':
            print(f"\n❌ TÂCHE ÉCHOUÉE")
            print(f"   Erreur: {result.result}")
            return False
        else:
            print(f"\n⚠️  État inconnu: {result.state}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        print("\n⚠️  Impossible d'envoyer la tâche")
        print("   Assurez-vous que:")
        print("   1. Redis est accessible")
        print("   2. Celery Worker est en cours d'exécution")
        print("   3. Les variables d'environnement sont correctes")
        return False

if __name__ == '__main__':
    success = test_celery_task()
    sys.exit(0 if success else 1)
