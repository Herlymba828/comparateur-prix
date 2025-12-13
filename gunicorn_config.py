"""
Configuration Gunicorn pour Railway avec logging détaillé.
"""
import os
import multiprocessing

# Bind
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"

# Workers
workers = 2
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Restart workers after this many requests (with jitter)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'debug'  # Plus de détails pour le diagnostic
capture_output = True
enable_stdio_inheritance = True

# Preload app
preload_app = True

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL
keyfile = None
certfile = None

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("=" * 60)
    server.log.info("Gunicorn démarrage...")
    server.log.info(f"PORT: {os.getenv('PORT', '8080')}")
    server.log.info(f"DJANGO_SETTINGS_MODULE: {os.getenv('DJANGO_SETTINGS_MODULE', 'non défini')}")
    server.log.info(f"PYTHONPATH: {os.getenv('PYTHONPATH', 'non défini')}")
    server.log.info("=" * 60)

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Gunicorn prêt à accepter les connexions")

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Gunicorn arrêt...")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal."""
    worker.log.info(f"Worker {worker.pid} interrompu")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Préparation du fork du worker {worker.pid}")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker {worker.pid} forké avec succès")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Préparation du fork du master process")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal."""
    worker.log.error(f"Worker {worker.pid} aborté!")
