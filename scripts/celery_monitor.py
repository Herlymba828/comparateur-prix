#!/usr/bin/env python
"""
Monitoring et auto-restart pour Celery Worker et Beat
Détecte les crashs et redémarre automatiquement les processus
"""
import os
import sys
import time
import signal
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class CeleryMonitor:
    def __init__(self):
        self.worker_process = None
        self.beat_process = None
        self.worker_restarts = 0
        self.beat_restarts = 0
        self.max_restarts = 5
        self.restart_window = 300  # 5 minutes
        self.last_restart_time = None
        
    def start_worker(self):
        """Démarre le Celery Worker"""
        try:
            logger.info("🔄 Démarrage de Celery Worker...")
            self.worker_process = subprocess.Popen(
                [
                    'celery', '-A', 'config', 'worker',
                    '--loglevel=info',
                    '--concurrency=2',
                    '--max-tasks-per-child=100',
                    '--time-limit=300',
                    '--soft-time-limit=240'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"✅ Celery Worker démarré (PID: {self.worker_process.pid})")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur démarrage Worker: {e}")
            return False
    
    def start_beat(self):
        """Démarre le Celery Beat"""
        try:
            logger.info("⏰ Démarrage de Celery Beat...")
            self.beat_process = subprocess.Popen(
                [
                    'celery', '-A', 'config', 'beat',
                    '--loglevel=info',
                    '--scheduler=django_celery_beat.schedulers:DatabaseScheduler'
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info(f"✅ Celery Beat démarré (PID: {self.beat_process.pid})")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur démarrage Beat: {e}")
            return False
    
    def check_worker(self):
        """Vérifie si le Worker est actif"""
        if self.worker_process is None:
            return False
        
        poll = self.worker_process.poll()
        if poll is not None:
            logger.warning(f"⚠️ Worker crashed (exit code: {poll})")
            self._log_process_output(self.worker_process, "Worker")
            return False
        return True
    
    def check_beat(self):
        """Vérifie si Beat est actif"""
        if self.beat_process is None:
            return False
        
        poll = self.beat_process.poll()
        if poll is not None:
            logger.warning(f"⚠️ Beat crashed (exit code: {poll})")
            self._log_process_output(self.beat_process, "Beat")
            return False
        return True
    
    def _log_process_output(self, process, name):
        """Log la sortie d'un processus crashé"""
        try:
            stdout, stderr = process.communicate(timeout=1)
            if stdout:
                logger.error(f"{name} stdout: {stdout[-500:]}")
            if stderr:
                logger.error(f"{name} stderr: {stderr[-500:]}")
        except:
            pass
    
    def restart_worker(self):
        """Redémarre le Worker"""
        if not self._can_restart('worker'):
            logger.error("❌ Trop de redémarrages Worker, abandon")
            return False
        
        logger.info("🔄 Redémarrage du Worker...")
        self.stop_worker()
        time.sleep(2)
        
        if self.start_worker():
            self.worker_restarts += 1
            self._update_restart_time()
            return True
        return False
    
    def restart_beat(self):
        """Redémarre Beat"""
        if not self._can_restart('beat'):
            logger.error("❌ Trop de redémarrages Beat, abandon")
            return False
        
        logger.info("🔄 Redémarrage de Beat...")
        self.stop_beat()
        time.sleep(2)
        
        if self.start_beat():
            self.beat_restarts += 1
            self._update_restart_time()
            return True
        return False
    
    def _can_restart(self, service):
        """Vérifie si on peut redémarrer (limite de redémarrages)"""
        now = time.time()
        
        # Reset le compteur si la fenêtre de temps est passée
        if self.last_restart_time and (now - self.last_restart_time) > self.restart_window:
            self.worker_restarts = 0
            self.beat_restarts = 0
        
        restarts = self.worker_restarts if service == 'worker' else self.beat_restarts
        return restarts < self.max_restarts
    
    def _update_restart_time(self):
        """Met à jour le temps du dernier redémarrage"""
        self.last_restart_time = time.time()
    
    def stop_worker(self):
        """Arrête le Worker proprement"""
        if self.worker_process:
            try:
                self.worker_process.terminate()
                self.worker_process.wait(timeout=10)
            except:
                self.worker_process.kill()
            self.worker_process = None
    
    def stop_beat(self):
        """Arrête Beat proprement"""
        if self.beat_process:
            try:
                self.beat_process.terminate()
                self.beat_process.wait(timeout=10)
            except:
                self.beat_process.kill()
            self.beat_process = None
    
    def stop_all(self):
        """Arrête tous les processus"""
        logger.info("🛑 Arrêt de tous les processus Celery...")
        self.stop_worker()
        self.stop_beat()
    
    def monitor(self):
        """Boucle de monitoring principale"""
        logger.info("🚀 Démarrage du monitoring Celery")
        
        # Démarrage initial
        self.start_worker()
        time.sleep(2)
        self.start_beat()
        
        try:
            while True:
                time.sleep(10)  # Check toutes les 10 secondes
                
                # Vérifier Worker
                if not self.check_worker():
                    logger.warning("⚠️ Worker non actif, tentative de redémarrage...")
                    if not self.restart_worker():
                        logger.error("❌ Impossible de redémarrer Worker")
                        break
                
                # Vérifier Beat
                if not self.check_beat():
                    logger.warning("⚠️ Beat non actif, tentative de redémarrage...")
                    if not self.restart_beat():
                        logger.error("❌ Impossible de redémarrer Beat")
                        break
                
                # Log status périodique
                if int(time.time()) % 60 == 0:
                    logger.info(f"✅ Status: Worker OK (restarts: {self.worker_restarts}), Beat OK (restarts: {self.beat_restarts})")
        
        except KeyboardInterrupt:
            logger.info("⚠️ Interruption utilisateur")
        except Exception as e:
            logger.error(f"❌ Erreur monitoring: {e}")
        finally:
            self.stop_all()

def main():
    monitor = CeleryMonitor()
    
    # Gestion des signaux
    def signal_handler(sig, frame):
        logger.info("🛑 Signal reçu, arrêt...")
        monitor.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    monitor.monitor()

if __name__ == '__main__':
    main()
