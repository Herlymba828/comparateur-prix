# 🤖 Automatisation : Scraping et Backup

Guide complet pour automatiser le scraping DGCCRF et les backups de la base de données.

---

## 📋 Vue d'ensemble

Le système d'automatisation utilise **Celery** et **Redis** pour :
- ✅ **Scraping automatique** : Extraction périodique des données DGCCRF
- ✅ **Sauvegarde automatique** : Données sauvegardées en base de données
- ✅ **Backup automatique** : Sauvegarde périodique de la base de données
- ✅ **Gestion des erreurs** : Retry automatique avec backoff exponentiel

---

## 🔄 Planification automatique

### Scraping DGCCRF

#### Quotidien (tous les jours)
- **Mode** : Incrémental (`only_changed=True`)
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données
- **Exports** : Aucun (gain d'espace)

#### Hebdomadaire (tous les 7 jours)
- **Mode** : Rafraîchissement complet
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données

#### Mensuel (tous les 30 jours)
- **Mode** : Rafraîchissement complet
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données
- **Exports** : CSV, SQL, JSON (avec timestamp)

### Backup de la base de données

#### Quotidien (tous les jours)
- **Format** : SQL (PostgreSQL dump)
- **Compression** : Oui (gzip)
- **Rétention** : 7 jours
- **Emplacement** : `backups/backup_YYYYMMDD_HHMMSS.sql.gz`

#### Hebdomadaire (tous les dimanches)
- **Format** : SQL + JSON (complet)
- **Compression** : Oui (gzip pour SQL)
- **Rétention** : 4 semaines
- **Emplacement** : 
  - `backups/backup_YYYYMMDD_HHMMSS.sql.gz`
  - `backups/backup_data_YYYYMMDD_HHMMSS.json`

---

## 🚀 Utilisation

### Exécution manuelle

#### Scraping

```bash
# Via commande Django
python manage.py scrape_dgccrf

# Via Celery (asynchrone)
python manage.py shell
>>> from apps.produits.tasks import dgccrf_scrape_report_task
>>> result = dgccrf_scrape_report_task.delay()
```

#### Backup

```bash
# Backup SQL uniquement
python manage.py backup_database --format sql --compress

# Backup JSON uniquement
python manage.py backup_database --format json

# Backup complet (SQL + JSON)
python manage.py backup_database --format both --compress

# Backup avec rétention personnalisée
python manage.py backup_database --format sql --keep 14
```

### Via Celery (asynchrone)

```python
from apps.produits.tasks import backup_database_task

# Backup SQL compressé
result = backup_database_task.delay(format_type='sql', compress=True, keep=7)

# Backup complet
result = backup_database_task.delay(format_type='both', compress=True, keep=4)
```

---

## 📁 Structure des backups

```
backups/
├── backup_20250117_020000.sql.gz          # Backup quotidien (compressé)
├── backup_20250116_020000.sql.gz
├── backup_20250115_020000.sql.gz
├── ...
├── backup_20250110_030000.sql.gz          # Backup hebdomadaire (dimanche)
├── backup_data_20250110_030000.json       # Export JSON hebdomadaire
└── ...
```

### Rotation automatique

- **Backups quotidiens** : Conservés pendant 7 jours
- **Backups hebdomadaires** : Conservés pendant 4 semaines
- **Nettoyage automatique** : Les anciens backups sont supprimés automatiquement

---

## ⚙️ Configuration

### Variables d'environnement

```bash
# Scraping
DGCCRF_SAVE_TO_DB=true          # Sauvegarde automatique en base
DGCCRF_SKIP_UNCHANGED=true      # Mode incrémental activé

# Backup (optionnel)
BACKUP_DIR=backups              # Répertoire de backup (par défaut: backups)
BACKUP_KEEP_DAILY=7             # Nombre de backups quotidiens à conserver
BACKUP_KEEP_WEEKLY=4            # Nombre de backups hebdomadaires à conserver
```

### Personnalisation de la planification

Éditez `config/celery.py` pour modifier les fréquences :

```python
app.conf.beat_schedule = {
    'dgccrf-scrape-quotidien': {
        'task': 'apps.produits.tasks.dgccrf_scrape_report_task',
        'schedule': 86400.0,  # Modifier la fréquence ici
        # ...
    },
    'backup-database-quotidien': {
        'task': 'apps.produits.tasks.backup_database_task',
        'schedule': 86400.0,  # Modifier la fréquence ici
        # ...
    },
}
```

---

## 🔍 Monitoring

### Vérifier les tâches planifiées

```bash
# Lister les tâches planifiées
celery -A config inspect scheduled

# Vérifier les workers actifs
celery -A config inspect active

# Statistiques
celery -A config inspect stats
```

### Logs

Les logs sont disponibles dans :
- **Django** : `logs/django.log` (si configuré)
- **Celery** : Console (stdout/stderr)
- **Railway** : Interface web → Deployments → View Logs

### Rapports de scraping

Les rapports sont générés dans `data/dgccrf_YYYYMMDD_HHMMSS_report.json` :

```json
{
  "source": "DGCCRF",
  "total_items": 1500,
  "saved_products": 150,
  "saved_prices": 1200,
  "duration_sec": 45.2,
  "timestamp": "2025-01-17T02:00:00Z"
}
```

---

## 🔄 Restauration depuis un backup

### Restaurer un backup SQL

```bash
# Décompresser si nécessaire
gunzip backups/backup_20250117_020000.sql.gz

# Restaurer
psql -h localhost -U postgres -d comparateur_prix < backups/backup_20250117_020000.sql

# Ou via Railway
railway run psql $DATABASE_URL < backups/backup_20250117_020000.sql
```

### Restaurer un backup JSON

```bash
# Restaurer depuis JSON
python manage.py loaddata backups/backup_data_20250117_020000.json
```

---

## 🐛 Dépannage

### Erreur : "pg_dump not found"

**Solution :** La commande utilise automatiquement Django `dumpdata` en fallback.

### Erreur : "Permission denied" sur le répertoire backups

**Solution :**
```bash
# Créer le répertoire avec les bonnes permissions
mkdir -p backups
chmod 755 backups
```

### Erreur : "Backup trop volumineux"

**Solution :**
- Activer la compression : `--compress`
- Réduire la rétention : `--keep 3`
- Utiliser seulement SQL : `--format sql`

---

## ✅ Checklist

- [ ] Redis installé et démarré
- [ ] Celery Worker démarré
- [ ] Celery Beat démarré
- [ ] Planification configurée dans `config/celery.py`
- [ ] Répertoire `backups/` créé
- [ ] Scraping testé manuellement
- [ ] Backup testé manuellement
- [ ] Logs vérifiés

---

## 🎯 Résumé

1. **Scraping** : Automatique quotidien/hebdomadaire/mensuel
2. **Sauvegarde** : Données sauvegardées automatiquement en base
3. **Backup** : Backup automatique quotidien/hebdomadaire
4. **Rotation** : Nettoyage automatique des anciens backups

**Le système est maintenant entièrement automatisé !** 🎉

