# Automatisation du Scraping DGCCRF avec Celery et Redis

## Vue d'ensemble

Le scraping DGCCRF est maintenant automatisé avec Celery et Redis. La tâche s'exécute automatiquement selon une planification définie et utilise directement le scraper Python pour une meilleure intégration.

## Configuration

### Prérequis

1. **Redis** doit être installé et en cours d'exécution :
   ```bash
   # Windows (PowerShell)
   redis-server
   
   # Linux/Mac
   redis-server
   ```

2. **Variables d'environnement** (dans `.env`) :
   ```env
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   REDIS_URL=redis://localhost:6379/0
   ```

### Tâche Celery

La tâche `dgccrf_scrape_report_task` est définie dans `apps/produits/tasks.py` :

```python
@shared_task(name="dgccrf_scrape_report_task", bind=True, max_retries=3)
def dgccrf_scrape_report_task(self, limit=None, unified=True, save=True, 
                               only_changed=True, csv_out=None, sql_out=None, 
                               report_out=None, sources=None) -> dict:
```

**Caractéristiques :**
- Utilise directement le scraper Python (pas de subprocess)
- Retry automatique avec backoff exponentiel (3 tentatives max)
- Retourne un dictionnaire avec les statistiques de l'extraction
- Logging intégré pour le suivi

## Planification automatique

Les tâches sont planifiées dans `config/celery.py` :

### Scraping quotidien
- **Fréquence** : Tous les jours
- **Configuration** : `only_changed=True` (extraction incrémentale)
- **Fichiers générés** :
  - `data/dgccrf_daily.csv`
  - `data/dgccrf_daily.sql`
  - `data/dgccrf_daily_report.json`

### Scraping mensuel
- **Fréquence** : Tous les 30 jours
- **Configuration** : `only_changed=False` (rafraîchissement complet)
- **Fichiers générés** :
  - `data/dgccrf_monthly.csv`
  - `data/dgccrf_monthly.sql`
  - `data/dgccrf_monthly_report.json`

## Démarrage des services

### 1. Démarrer Redis
```bash
redis-server
```

### 2. Démarrer le worker Celery
```bash
celery -A config.celery:app worker -l info
```

### 3. Démarrer Celery Beat (planificateur)
```bash
celery -A config.celery:app beat -l info
```

### Script PowerShell (Windows)
Un script est disponible pour démarrer tous les services :
```powershell
.\scripts\start_services.ps1
```

## Utilisation manuelle

### Déclencher la tâche manuellement

Depuis le shell Django :
```python
from apps.produits.tasks import dgccrf_scrape_report_task

# Exécution asynchrone
result = dgccrf_scrape_report_task.delay(
    limit=None,
    unified=True,
    save=True,
    only_changed=True,
    sources=['liste_produit']
)

# Attendre le résultat
stats = result.get()
print(f"Items extraits: {stats['total_items']}")
```

### Déclencher depuis la ligne de commande

```bash
# Via Django shell
python manage.py shell
>>> from apps.produits.tasks import dgccrf_scrape_report_task
>>> dgccrf_scrape_report_task.delay()
```

## Structure des résultats

La tâche retourne un dictionnaire avec les statistiques :

```python
{
    'success': True,
    'result_code': 0,
    'report_path': 'data/dgccrf_daily_report.json',
    'total_items': 67,
    'source_counts': {'liste_produit': 67},
    'saved_products': 45,
    'saved_prices': 67,
    'duration_sec': 12.345,
    'timestamp': '2025-11-13T16:39:31+01:00',
}
```

## Monitoring

### Vérifier l'état des tâches

```python
from celery.result import AsyncResult

# Obtenir le résultat d'une tâche
result = AsyncResult('task-id')
print(result.state)  # PENDING, SUCCESS, FAILURE, etc.
print(result.get())   # Résultat si terminée
```

### Logs

Les logs sont disponibles dans :
- Console (si `-l info` est utilisé)
- Fichiers de log Django (selon configuration)

## Gestion des erreurs

- **Retry automatique** : 3 tentatives avec backoff exponentiel (60s, 120s, 240s)
- **Logging** : Toutes les erreurs sont loggées avec stack trace
- **Notification** : Les erreurs peuvent être envoyées par email si configuré

## Nettoyage effectué

Les fichiers suivants ont été supprimés car non essentiels :
- `list_categories.py` - Script utilitaire non utilisé
- `Créer un environnement virtuel (rec.txt` - Fichier de notes
- `celerybeat-schedule.bak` - Fichier de backup
- `management/commands/update_prices.py` - Squelette dupliqué
- `scripts/tests/test_helpers.py` - Test skeleton non implémenté
- `scripts/test_dgccrf_extraction.py` - Déplacé vers `tests/scraper/`

## Améliorations apportées

1. **Tâche Celery améliorée** : Utilise directement le scraper Python au lieu de subprocess
2. **Retry automatique** : Gestion robuste des erreurs avec retry
3. **Statistiques détaillées** : Retourne un dictionnaire avec toutes les métriques
4. **Configuration flexible** : Paramètres configurables via kwargs dans Celery Beat
5. **Nettoyage du code** : Suppression des imports et fichiers non utilisés

## Prochaines étapes

Pour améliorer encore l'automatisation :
1. Ajouter des notifications email en cas d'échec
2. Créer un dashboard de monitoring des tâches
3. Ajouter des métriques Prometheus pour le monitoring
4. Implémenter un système d'alertes pour les anomalies

