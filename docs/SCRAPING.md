# 🕷️ Guide Complet : Scraping DGCCRF

Guide complet pour le scraping des données DGCCRF, incluant la production, le lancement, la vérification, les migrations, le parsing, Celery et les backups.

## 📋 Table des matières

- [Vue d'ensemble](#vue-densemble)
- [Lancement en Production](#lancement-en-production)
- [Vérification](#vérification)
- [Migrations et Configuration](#migrations-et-configuration)
- [Parsing DGCCRF](#parsing-dgccrf)
- [Automatisation avec Celery](#automatisation-avec-celery)
- [Backup Automatique](#backup-automatique)
- [Dépannage](#dépannage)

---

## 🎯 Vue d'ensemble

Le système de scraping DGCCRF permet d'extraire automatiquement les données de produits depuis le site [dgccrf.ga](https://www.dgccrf.ga/). Les données sont sauvegardées en base de données et peuvent être automatiquement mises à jour via Celery.

### Sources disponibles

- **Liste des produits** : `/echo-liste-produit` - 67 produits défiscalisés
- **Prix homologués** : `/echo-prix-homologue` - Prix officiels
- **Produits pétroliers** : `/echo-produit-petrolier` - Produits pétroliers

---

## 🚀 Lancement en Production

### Méthode 1 : Via Railway Dashboard Terminal (Recommandé)

1. **Ouvrir Railway Dashboard**
   - Allez sur [railway.app](https://railway.app)
   - Connectez-vous à votre compte
   - Ouvrez votre projet

2. **Accéder au Terminal**
   - Allez dans l'onglet **"Deployments"**
   - Cliquez sur le **dernier déploiement**
   - Ouvrez l'onglet **"Terminal"** ou **"Logs"**

3. **Exécuter les commandes**

```bash
# 1. Vérifier les migrations (devrait être OK)
python manage.py showmigrations

# 2. Appliquer les migrations (si nécessaire)
python manage.py migrate

# 3. Initialiser les catégories (si pas déjà fait)
python manage.py init_categories

# 4. Lancer le scraping (test avec 50 produits)
python manage.py scrape_dgccrf --limit 50

# 5. Vérifier les résultats
python manage.py shell -c "from apps.produits.models import Produit, Prix, Categorie; print(f'Produits: {Produit.objects.count()}, Prix: {Prix.objects.count()}, Catégories: {Categorie.objects.count()}')"

# 6. Si ça fonctionne, lancer le scraping complet
python manage.py scrape_dgccrf
```

### Méthode 2 : Via Railway CLI

```bash
# Vérifier le statut
railway status

# Voir les services disponibles
railway service

# Sélectionner le service Django (pas Postgres)
railway service <service-django-name>

# Puis exécuter les commandes
railway run python manage.py migrate
railway run python manage.py init_categories
railway run python manage.py scrape_dgccrf --limit 50
```

### Options de scraping disponibles

```bash
# --limit N : Limiter le nombre d'éléments à scraper
railway run python manage.py scrape_dgccrf --limit 100

# --sources SOURCES : Sources à scraper (séparées par des virgules)
railway run python manage.py scrape_dgccrf --sources liste_produit,prix_homologue

# --no-save : Test sans sauvegarder en base
railway run python manage.py scrape_dgccrf --no-save --limit 10

# --only-changed : Scraper uniquement les éléments modifiés (par défaut: True)
railway run python manage.py scrape_dgccrf --only-changed
```

### Workflow complet recommandé

```bash
# 1. Vérifier l'état des migrations
railway run python manage.py showmigrations

# 2. Appliquer les migrations
railway run python manage.py migrate

# 3. Initialiser les catégories
railway run python manage.py init_categories

# 4. Tester le scraping avec une petite limite
railway run python manage.py scrape_dgccrf --limit 10

# 5. Si le test fonctionne, lancer le scraping complet
railway run python manage.py scrape_dgccrf

# 6. Vérifier les résultats
railway run python manage.py shell -c "from apps.produits.models import Produit, Prix; print(f'Produits: {Produit.objects.count()}, Prix: {Prix.objects.count()}')"
```

---

## ✅ Vérification

### Commandes de vérification

#### 1. Vérifier le nombre de produits créés

```bash
python manage.py shell -c "from apps.produits.models import Produit, Prix, Categorie; print(f'Produits: {Produit.objects.count()}, Prix: {Prix.objects.count()}, Catégories: {Categorie.objects.count()}')"
```

#### 2. Voir quelques exemples de produits

```bash
python manage.py shell -c "from apps.produits.models import Produit; produits = Produit.objects.all()[:5]; [print(f'{p.id}: {p.nom}') for p in produits]"
```

#### 3. Vérifier les prix associés

```bash
python manage.py shell -c "from apps.produits.models import Prix; print(f'Nombre de prix: {Prix.objects.count()}'); prix = Prix.objects.select_related('produit', 'magasin').first(); print(f'Exemple: {prix.produit.nom} - {prix.prix_actuel} FCFA chez {prix.magasin.nom if prix.magasin else \"N/A\"}')"
```

#### 4. Vérifier les catégories

```bash
python manage.py shell -c "from apps.produits.models import Categorie; print(f'Catégories racines: {Categorie.objects.filter(parent__isnull=True).count()}'); print(f'Total catégories: {Categorie.objects.count()}')"
```

### Notes sur les avertissements Elasticsearch

Les avertissements Elasticsearch sont **normaux** en local :
- Elasticsearch n'est pas disponible en local
- Les produits sont quand même créés en base de données
- L'indexation Elasticsearch est ignorée silencieusement
- En production, si Elasticsearch est configuré, l'indexation fonctionnera automatiquement

Pour désactiver complètement les tentatives d'indexation :

```bash
# Définir la variable d'environnement
export SEARCH_INDEX_ENABLED=false

# Ou sur Windows PowerShell
$env:SEARCH_INDEX_ENABLED="false"

# Puis relancer le scraping
python manage.py scrape_dgccrf --limit 50
```

---

## 🔧 Migrations et Configuration

### Exécution des migrations

#### Méthode 1 : Via Railway CLI (Recommandé)

```bash
# Exécuter toutes les migrations en attente
railway run python manage.py migrate

# Exécuter les migrations avec affichage SQL
railway run python manage.py migrate --verbosity 2

# Créer un superutilisateur (si nécessaire)
railway run python manage.py createsuperuser
```

#### Méthode 2 : Via Railway Dashboard

1. Allez dans votre projet Railway
2. Ouvrez l'onglet **"Deployments"**
3. Cliquez sur le dernier déploiement
4. Ouvrez l'onglet **"Logs"**
5. Utilisez le terminal intégré pour exécuter les commandes

### Vérifier l'état des migrations

```bash
# Voir les migrations en attente
railway run python manage.py showmigrations

# Voir les migrations appliquées
railway run python manage.py showmigrations --list
```

### Configuration des variables d'environnement

Assurez-vous que les variables suivantes sont configurées dans Railway :

```env
# Configuration DGCCRF
DGCCRF_BASE_URL=https://www.dgccrf.ga/
DGCCRF_USER_AGENT=ComparateurPrixBot/1.0 (+contact@example.com)
DGCCRF_REQUEST_DELAY=1.0
DGCCRF_TIMEOUT=30
DGCCRF_MAX_RETRIES=3
DGCCRF_BACKOFF=1.5
DGCCRF_SAVE_TO_DB=true
DGCCRF_SKIP_UNCHANGED=true

# URLs spécifiques DGCCRF
DGCCRF_PRIX_HOMOLOGUE_URL=https://www.dgccrf.ga/echo-prix-homologue
DGCCRF_LISTE_PRODUIT_URL=https://www.dgccrf.ga/echo-liste-produit
DGCCRF_PRODUIT_PETROLIER_URL=https://www.dgccrf.ga/echo-produit-petrolier

# Chemins de fichiers (optionnels)
DGCCRF_REPORT_OUT=data/dgccrf_report.json
DGCCRF_LOG_FILE=logs/dgccrf_scraper.log
DGCCRF_RAW_DIR=data/raw/dgccrf
```

### Comment ajouter des variables dans Railway

1. Allez dans votre projet Railway
2. Ouvrez l'onglet **"Variables"**
3. Cliquez sur **"New Variable"**
4. Entrez le nom et la valeur
5. Cliquez sur **"Add"**

---

## 📄 Parsing DGCCRF

### Vue d'ensemble

Le scraper DGCCRF parse la page [https://www.dgccrf.ga/echo-liste-produit](https://www.dgccrf.ga/echo-liste-produit) qui contient la liste des 67 produits défiscalisés à prix bloqués.

### Améliorations apportées

#### 1. Détection des catégories

Le parser détecte automatiquement les catégories de produits qui précèdent chaque tableau :
- **VIANDE DE PORC**
- **VIANDE DE BOEUF**
- **VOLAILLE**
- **POISSON**
- **CONSERVES DE POISSON**
- **CONSERVES DE LEGUMES**
- **PATES ALIMENTAIRES**
- **LAITS MATIERES GRASSES ANIMALES**
- **LAITS MATIERES GRASSES VEGETALES**
- **LAITS INFANTILES**
- **RIZ PARFUME AU JASMIN ENTIER**
- **HUILE RAFFINEE**
- **SUCRE**
- **POISSON DE PECHE LOCALE**

Ces catégories sont stockées dans le champ `sous_categorie` de chaque produit.

#### 2. Parsing des colonnes de tableaux

Le parser gère correctement les colonnes suivantes :
- **N** : Numéro de référence (stocké dans `reference_numero`)
- **DESIGNATION** : Nom du produit (stocké dans `nom`)
- **PRIX GROS** : Prix de gros (stocké dans `extra.prix_gros`)
- **PRIX DEMI GROS** : Prix demi-gros (stocké dans `extra.prix_demi_gros`)
- **PRIX DETAIL** : Prix au détail (stocké dans `prix_detail` et `prix_unitaire`)

#### 3. Extraction de l'origine

Le parser extrait automatiquement l'origine depuis les parenthèses dans la désignation :
- Exemple : "Cuisses de Poulet (USA)" → `nom: "Cuisses de Poulet"`, `extra.origine: "USA"`
- Exemple : "Maquereaux 300g - 500g (ASIE)" → `nom: "Maquereaux 300g - 500g"`, `extra.origine: "ASIE"`

#### 4. Parsing des conditionnements

Le parser gère maintenant plusieurs formats de conditionnement :

**Formats supportés :**
- `125g x 50` → 50 unités de 125g = 6250g total
- `400g x 24` → 24 unités de 400g = 9600g total
- `10lbs ou 4,54Kg x 10` → 10 unités de 4,54kg = 45,4kg total (prend la partie après "ou")
- `1L` → 1 unité de 1L
- `500ml` → 1 unité de 500ml

**Conversion automatique :**
- Les livres (lbs) sont automatiquement converties en kilogrammes (1 lb = 0.453592 kg)
- Les formats avec "ou" utilisent la partie métrique (après "ou")

#### 5. Extraction de la marque

Le parser tente d'extraire la marque depuis la désignation en cherchant des mots en majuscules :
- Exemple : "Sardines à huile Princesse 125g" → `marque: "PRINCESSE"`

### Structure des données extraites

Chaque produit extrait a la structure suivante :

```json
{
  "nom": "Cotis de Porc viandé",
  "categorie": "Produits défiscalisés",
  "sous_categorie": "VIANDE DE PORC",
  "format": "1.0unite",
  "marque": "",
  "prix_unitaire": 1875.0,
  "unite": "unite",
  "prix_detail": 1875.0,
  "prix_par_kilo": null,
  "date_publication": null,
  "periode_debut": null,
  "periode_fin": null,
  "reference_titre": "Produits défiscalisés",
  "reference_numero": "1",
  "reference_url": "https://www.dgccrf.ga/echo-liste-produit",
  "description": "1 | Cotis de Porc viandé | 16 340 F CFA | 16 990 F CFA | 1 875 F CFA",
  "zone": "",
  "devise": "FCFA",
  "type_prix": "detail",
  "extra": {
    "prix_gros": 16340.0,
    "prix_demi_gros": 16990.0,
    "origine": null,
    "conditionnement": {}
  }
}
```

### Utilisation

#### Exemple basique

```python
from scripts.scraper_dgccrf import DgccrfScraper

scraper = DgccrfScraper()

# Parser la page liste produits
for item in scraper.iter_from_liste_produit_page():
    print(f"Produit: {item['nom']}")
    print(f"Catégorie: {item['sous_categorie']}")
    print(f"Prix détail: {item['prix_detail']} FCFA")
    print(f"Prix gros: {item.get('extra', {}).get('prix_gros')} FCFA")
    print(f"Origine: {item.get('extra', {}).get('origine')}")
    print("---")
```

#### Exemple avec sauvegarde en base de données

```python
from scripts.scraper_dgccrf import DgccrfScraper

scraper = DgccrfScraper()
items = list(scraper.iter_from_liste_produit_page())

# Sauvegarder en base de données
if scraper._init_django():
    created_prod, created_prix = scraper.persist_items(items)
    print(f"Créés: {created_prod} produits, {created_prix} prix")
```

#### Utilisation en ligne de commande

```bash
# Parser uniquement la page liste produits
python scripts/scraper_dgccrf.py --sources liste_produit --out data/produits.json

# Parser et sauvegarder en base de données
python scripts/scraper_dgccrf.py --sources liste_produit --save

# Parser et exporter en CSV
python scripts/scraper_dgccrf.py --sources liste_produit --csv data/produits.csv
```

### Notes importantes

1. **Respect des robots.txt** : Le scraper respecte par défaut le fichier robots.txt du site
2. **Délai entre requêtes** : Un délai de 1 seconde est appliqué entre les requêtes pour éviter de surcharger le serveur
3. **Gestion des erreurs** : Le scraper gère automatiquement les erreurs de réseau avec retry et backoff
4. **Détection de changements** : Le scraper peut détecter si la page a changé depuis la dernière extraction

---

## ⚙️ Automatisation avec Celery

### Vue d'ensemble

Le scraping DGCCRF est automatisé avec Celery et Redis. La tâche s'exécute automatiquement selon une planification définie.

### Configuration

#### Prérequis

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

### Planification automatique

Les tâches sont planifiées dans `config/celery.py` :

#### Scraping quotidien
- **Fréquence** : Tous les jours
- **Configuration** : `only_changed=True` (extraction incrémentale)
- **Fichiers générés** :
  - `data/dgccrf_daily.csv`
  - `data/dgccrf_daily.sql`
  - `data/dgccrf_daily_report.json`

#### Scraping mensuel
- **Fréquence** : Tous les 30 jours
- **Configuration** : `only_changed=False` (rafraîchissement complet)
- **Fichiers générés** :
  - `data/dgccrf_monthly.csv`
  - `data/dgccrf_monthly.sql`
  - `data/dgccrf_monthly_report.json`

### Démarrage des services

#### 1. Démarrer Redis
```bash
redis-server
```

#### 2. Démarrer le worker Celery
```bash
celery -A config.celery:app worker -l info
```

#### 3. Démarrer Celery Beat (planificateur)
```bash
celery -A config.celery:app beat -l info
```

### Utilisation manuelle

#### Déclencher la tâche manuellement

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

#### Déclencher depuis la ligne de commande

```bash
# Via Django shell
python manage.py shell
>>> from apps.produits.tasks import dgccrf_scrape_report_task
>>> dgccrf_scrape_report_task.delay()
```

### Structure des résultats

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

### Monitoring

#### Vérifier l'état des tâches

```python
from celery.result import AsyncResult

# Obtenir le résultat d'une tâche
result = AsyncResult('task-id')
print(result.state)  # PENDING, SUCCESS, FAILURE, etc.
print(result.get())   # Résultat si terminée
```

#### Logs

Les logs sont disponibles dans :
- Console (si `-l info` est utilisé)
- Fichiers de log Django (selon configuration)

### Gestion des erreurs

- **Retry automatique** : 3 tentatives avec backoff exponentiel (60s, 120s, 240s)
- **Logging** : Toutes les erreurs sont loggées avec stack trace
- **Notification** : Les erreurs peuvent être envoyées par email si configuré

---

## 💾 Backup Automatique

### Vue d'ensemble

Le système d'automatisation utilise **Celery** et **Redis** pour :
- ✅ **Scraping automatique** : Extraction périodique des données DGCCRF
- ✅ **Sauvegarde automatique** : Données sauvegardées en base de données
- ✅ **Backup automatique** : Sauvegarde périodique de la base de données
- ✅ **Gestion des erreurs** : Retry automatique avec backoff exponentiel

### Planification automatique

#### Scraping DGCCRF

**Quotidien (tous les jours)**
- **Mode** : Incrémental (`only_changed=True`)
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données
- **Exports** : Aucun (gain d'espace)

**Hebdomadaire (tous les 7 jours)**
- **Mode** : Rafraîchissement complet
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données

**Mensuel (tous les 30 jours)**
- **Mode** : Rafraîchissement complet
- **Sources** : Toutes les sources disponibles
- **Sauvegarde** : Automatique en base de données
- **Exports** : CSV, SQL, JSON (avec timestamp)

#### Backup de la base de données

**Quotidien (tous les jours)**
- **Format** : SQL (PostgreSQL dump)
- **Compression** : Oui (gzip)
- **Rétention** : 7 jours
- **Emplacement** : `backups/backup_YYYYMMDD_HHMMSS.sql.gz`

**Hebdomadaire (tous les dimanches)**
- **Format** : SQL + JSON (complet)
- **Compression** : Oui (gzip pour SQL)
- **Rétention** : 4 semaines
- **Emplacement** : 
  - `backups/backup_YYYYMMDD_HHMMSS.sql.gz`
  - `backups/backup_data_YYYYMMDD_HHMMSS.json`

### Utilisation manuelle

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

#### Via Celery (asynchrone)

```python
from apps.produits.tasks import backup_database_task

# Backup SQL compressé
result = backup_database_task.delay(format_type='sql', compress=True, keep=7)

# Backup complet
result = backup_database_task.delay(format_type='both', compress=True, keep=4)
```

### Structure des backups

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

### Configuration

#### Variables d'environnement

```bash
# Scraping
DGCCRF_SAVE_TO_DB=true          # Sauvegarde automatique en base
DGCCRF_SKIP_UNCHANGED=true      # Mode incrémental activé

# Backup (optionnel)
BACKUP_DIR=backups              # Répertoire de backup (par défaut: backups)
BACKUP_KEEP_DAILY=7             # Nombre de backups quotidiens à conserver
BACKUP_KEEP_WEEKLY=4            # Nombre de backups hebdomadaires à conserver
```

#### Personnalisation de la planification

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

### Restauration depuis un backup

#### Restaurer un backup SQL

```bash
# Décompresser si nécessaire
gunzip backups/backup_20250117_020000.sql.gz

# Restaurer
psql -h localhost -U postgres -d comparateur_prix < backups/backup_20250117_020000.sql

# Ou via Railway
railway run psql $DATABASE_URL < backups/backup_20250117_020000.sql
```

#### Restaurer un backup JSON

```bash
# Restaurer depuis JSON
python manage.py loaddata backups/backup_data_20250117_020000.json
```

---

## 🐛 Dépannage

### Erreur : "relation does not exist"

**Solution** : Appliquer les migrations d'abord :
```bash
railway run python manage.py migrate
```

### Erreur : "connection failed"

**Solution** : Vérifier que Railway CLI est bien configuré :
```bash
railway login
railway link
```

### Erreur : "Timeout" lors du scraping

**Solutions** :
- Augmentez `DGCCRF_TIMEOUT` (par exemple, `60`)
- Réduisez `--limit` pour tester avec moins de données
- Vérifiez la connexion réseau vers `dgccrf.ga`

### Erreur : "Permission denied" pour les fichiers

Les chemins de fichiers doivent être relatifs ou utiliser des chemins absolus accessibles. Évitez d'écrire dans `/tmp` si possible, utilisez plutôt des chemins dans le projet.

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

### Le scraping prend trop de temps

**Solution** : Utiliser une limite pour tester :
```bash
railway run python manage.py scrape_dgccrf --limit 100
```

### Vérifier les logs en temps réel

```bash
# Suivre les logs en direct
railway logs --follow

# Voir les 100 dernières lignes
railway logs --tail 100
```

### Problème : Base de données vide après scraping local

**Important** : Le scraping local crée des produits dans votre base locale, **pas en production**. Pour scraper en production, utilisez Railway Dashboard Terminal ou Railway CLI.

---

## 📋 Checklist

### Configuration initiale
- [ ] Migrations appliquées avec succès
- [ ] Catégories initialisées (`init_categories`)
- [ ] Variables d'environnement DGCCRF configurées
- [ ] Redis installé et démarré (si Celery utilisé)
- [ ] Celery Worker démarré (si Celery utilisé)
- [ ] Celery Beat démarré (si Celery utilisé)

### Scraping
- [ ] Scraping testé avec `--limit 10`
- [ ] Scraping complet exécuté
- [ ] Produits vérifiés en base de données
- [ ] Prix vérifiés en base de données

### Automatisation
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

---

## 📚 Ressources

- [Documentation Celery](https://docs.celeryproject.org/)
- [Documentation Redis](https://redis.io/documentation)
- [Documentation Railway](https://docs.railway.app/)
- [Site DGCCRF](https://www.dgccrf.ga/)

---

*Dernière mise à jour : 2025-01-17*