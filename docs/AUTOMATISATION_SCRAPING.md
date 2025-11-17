# 🤖 Automatisation du Scraping DGCCRF

Guide complet pour automatiser le scraping et la sauvegarde en base de données.

---

## 📋 Vue d'ensemble

Le système d'automatisation utilise **Celery** et **Redis** pour exécuter automatiquement le scraping DGCCRF et sauvegarder les données en base de données selon une planification définie.

### Fonctionnalités

- ✅ **Scraping automatique** : Exécution périodique selon une planification
- ✅ **Sauvegarde automatique** : Données sauvegardées directement en base de données
- ✅ **Gestion des erreurs** : Retry automatique avec backoff exponentiel
- ✅ **Rapports détaillés** : Statistiques et métriques de chaque exécution
- ✅ **Mode incrémental** : Ne scrape que les éléments modifiés (quotidien)
- ✅ **Rafraîchissement complet** : Scraping complet périodique (hebdomadaire/mensuel)

---

## 🚀 Configuration

### Prérequis

1. **Redis** doit être installé et en cours d'exécution
2. **Celery Worker** doit être démarré
3. **Celery Beat** doit être démarré pour la planification

### Variables d'environnement

```bash
# Redis (obligatoire)
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True

# Scraping (optionnel)
DGCCRF_SAVE_TO_DB=true  # Sauvegarde automatique activée
DGCCRF_SKIP_UNCHANGED=true  # Mode incrémental activé
```

---

## 📅 Planification automatique

Les tâches sont configurées dans `config/celery.py` :

### 1. Scraping quotidien

- **Fréquence** : Tous les jours
- **Heure** : 2h du matin (configurable)
- **Mode** : Incrémental (`only_changed=True`)
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données

**Configuration :**
```python
'dgccrf-scrape-quotidien': {
    'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
    'schedule': 86400.0,  # 1 jour
    'kwargs': {
        'save': True,  # Sauvegarde automatique
        'only_changed': True,  # Mode incrémental
        'sources': ['auto', 'prix_homologue', 'liste_produit', 'produit_petrolier'],
    },
}
```

### 2. Scraping hebdomadaire

- **Fréquence** : Tous les 7 jours
- **Mode** : Rafraîchissement complet (`only_changed=False`)
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données

### 3. Scraping mensuel

- **Fréquence** : Tous les 30 jours
- **Mode** : Rafraîchissement complet avec exports
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données
- **Exports** : CSV, SQL, JSON (avec timestamp)

---

## 🔧 Démarrage des services

### En développement local

```bash
# Terminal 1 : Redis
redis-server

# Terminal 2 : Celery Worker
celery -A config worker -l info

# Terminal 3 : Celery Beat (planification)
celery -A config beat -l info

# Terminal 4 : Django (optionnel)
python manage.py runserver
```

### Sur Railway

Les services sont automatiquement démarrés via le `Procfile` :

```procfile
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A config worker -l info
beat: celery -A config beat -l info
```

Railway démarre automatiquement :
- **web** : Application Django
- **worker** : Celery Worker pour exécuter les tâches
- **beat** : Celery Beat pour la planification

---

## 📊 Utilisation manuelle

### Exécuter une tâche manuellement

**Via Django shell :**
```python
from apps.produits.tasks import dgccrf_scrape_report_task

# Exécuter immédiatement
result = dgccrf_scrape_report_task.delay(
    limit=100,
    save=True,
    only_changed=True,
    sources=['liste_produit']
)

# Vérifier le résultat
print(result.get())
```

**Via commande Django :**
```bash
python manage.py scrape_dgccrf --limit 100 --sources liste_produit
```

**Via Celery directement :**
```bash
celery -A config call apps.produits.tasks.dgccrf_scrape_report_task \
    --kwargs '{"save": true, "only_changed": true}'
```

---

## 📈 Monitoring et logs

### Vérifier les tâches en cours

```bash
# Lister les workers actifs
celery -A config inspect active

# Vérifier les tâches planifiées
celery -A config inspect scheduled

# Vérifier les statistiques
celery -A config inspect stats
```

### Logs

Les logs sont disponibles dans :
- **Django** : `logs/django.log` (si configuré)
- **Celery** : Console (stdout/stderr)
- **Railway** : Interface web → Deployments → View Logs

### Rapports de scraping

Les rapports sont générés automatiquement dans `data/dgccrf_YYYYMMDD_HHMMSS_report.json` :

```json
{
  "source": "DGCCRF",
  "total_items": 1500,
  "source_counts": {
    "auto": 200,
    "prix_homologue": 300,
    "liste_produit": 800,
    "produit_petrolier": 200
  },
  "duration_sec": 45.2,
  "saved_products": 150,
  "saved_prices": 1200,
  "timestamp": "2025-01-17T02:00:00Z"
}
```

---

## 🔍 Vérification de la sauvegarde

### Vérifier les données sauvegardées

```python
from apps.produits.models import Produit, Prix, HomologationProduit, PrixHomologue

# Compter les produits
print(f"Produits: {Produit.objects.count()}")

# Compter les prix
print(f"Prix: {Prix.objects.count()}")

# Compter les homologations
print(f"Homologations: {HomologationProduit.objects.count()}")

# Compter les prix homologués
print(f"Prix homologués: {PrixHomologue.objects.count()}")

# Derniers produits ajoutés
recent_products = Produit.objects.order_by('-date_creation')[:10]
for p in recent_products:
    print(f"{p.nom} - {p.date_creation}")
```

### Via Django shell

```bash
python manage.py shell -c "
from apps.produits.models import Produit, Prix;
print(f'Produits: {Produit.objects.count()}');
print(f'Prix: {Prix.objects.count()}');
"
```

---

## 🐛 Dépannage

### Erreur : "Connection refused" (Redis)

**Cause :** Redis n'est pas démarré.

**Solution :**
```bash
# Vérifier que Redis est démarré
redis-cli ping  # Devrait retourner PONG

# Démarrer Redis
redis-server
```

### Erreur : "No module named 'celery'"

**Solution :**
```bash
pip install celery redis
```

### Erreur : "Task not found"

**Cause :** Le worker n'a pas découvert la tâche.

**Solution :**
```bash
# Redémarrer le worker
celery -A config worker -l info --reload
```

### Tâche ne s'exécute pas automatiquement

**Vérifications :**
1. Celery Beat est-il démarré ?
2. Redis est-il accessible ?
3. Les tâches sont-elles bien planifiées dans `config/celery.py` ?

**Solution :**
```bash
# Vérifier la planification
celery -A config inspect scheduled

# Redémarrer Celery Beat
celery -A config beat -l info
```

---

## ⚙️ Personnalisation

### Modifier la fréquence

Éditez `config/celery.py` :

```python
app.conf.beat_schedule = {
    'dgccrf-scrape-quotidien': {
        'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
        'schedule': 3600.0,  # Toutes les heures (au lieu de quotidien)
        # ...
    },
}
```

### Utiliser crontab pour des heures précises

```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'dgccrf-scrape-quotidien': {
        'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
        # ...
    },
}
```

### Ajouter des sources personnalisées

```python
'dgccrf-scrape-custom': {
    'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
    'schedule': 86400.0,
    'kwargs': {
        'sources': ['liste_produit'],  # Seulement cette source
        'save': True,
        'only_changed': True,
    },
}
```

---

## ✅ Checklist de configuration

- [ ] Redis installé et démarré
- [ ] Variables d'environnement configurées
- [ ] Celery Worker démarré
- [ ] Celery Beat démarré
- [ ] Planification configurée dans `config/celery.py`
- [ ] Tâche testée manuellement
- [ ] Logs vérifiés
- [ ] Données sauvegardées en base de données

---

## 🎯 Résumé

1. **Configuration** : Redis + Celery configurés
2. **Planification** : Tâches configurées dans `config/celery.py`
3. **Démarrage** : Worker + Beat démarrés
4. **Automatisation** : Scraping et sauvegarde automatiques selon la planification

**Le système est maintenant entièrement automatisé !** 🎉

