# Exécution des Migrations et du Scraping sur Railway

Ce guide explique comment exécuter les migrations Django et les scripts de scraping sur Railway.

## Prérequis

1. Avoir le CLI Railway installé : `npm i -g @railway/cli`
2. Être connecté à Railway : `railway login`
3. Avoir sélectionné votre projet : `railway link` (ou `railway link <project-id>`)

## 1. Exécuter les Migrations

### Méthode 1 : Via Railway CLI (Recommandé)

```bash
# Exécuter toutes les migrations en attente
railway run python manage.py migrate

# Exécuter les migrations avec affichage SQL
railway run python manage.py migrate --verbosity 2

# Créer un superutilisateur (si nécessaire)
railway run python manage.py createsuperuser
```

### Méthode 2 : Via Railway Dashboard

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

## 2. Exécuter le Scraping DGCCRF

### Commande principale de scraping

```bash
# Scraping complet (sauvegarde en base)
railway run python manage.py scrape_dgccrf

# Scraping avec limite (pour tester)
railway run python manage.py scrape_dgccrf --limit 50

# Scraping sans sauvegarde (test uniquement)
railway run python manage.py scrape_dgccrf --no-save --limit 10

# Scraping de sources spécifiques
railway run python manage.py scrape_dgccrf --sources liste_produit,prix_homologue

# Scraping uniquement des éléments modifiés (par défaut)
railway run python manage.py scrape_dgccrf --only-changed
```

### Options disponibles

- `--limit N` : Limiter le nombre d'éléments à scraper (utile pour les tests)
- `--sources SOURCES` : Sources à scraper (séparées par des virgules)
  - `liste_produit` : Liste des produits homologués
  - `prix_homologue` : Prix homologués
  - `produit_petrolier` : Produits pétroliers
- `--no-save` : Ne pas sauvegarder en base (test uniquement)
- `--only-changed` : Ne scraper que les éléments modifiés (par défaut: True)

### Autres commandes de scraping disponibles

```bash
# Importer des données DGCCRF depuis un fichier JSON
railway run python manage.py import_dgccrf --limit 200

# Importer des homologations depuis un CSV
railway run python manage.py import_homologations data/homologations_sans_sous_categorie.csv

# Mettre à jour les prix
railway run python manage.py mettre_a_jour_prix

# Analyser les données DGCCRF
railway run python manage.py analyse_dgccrf
```

## 3. Configuration des Variables d'Environnement

Assurez-vous que les variables suivantes sont configurées dans Railway :

### Variables obligatoires pour le scraping

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

## 4. Exécution en Arrière-plan (One-off Tasks)

Pour exécuter des tâches longues sans bloquer le terminal :

```bash
# Exécuter en arrière-plan (déconnexion du terminal)
railway run --detach python manage.py scrape_dgccrf --limit 1000

# Voir les logs en temps réel
railway logs --follow
```

## 5. Planification Automatique (Celery Beat)

Pour automatiser le scraping, vous pouvez utiliser Celery Beat :

### Configuration dans Railway

1. Assurez-vous que le service `beat` est configuré dans votre `Procfile`
2. Ajoutez une tâche périodique dans `config/celery.py`

### Exemple de tâche périodique

```python
# Dans config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'scrape-dgccrf-daily': {
        'task': 'apps.analyses.tasks.scrape_dgccrf_task',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h du matin
    },
}
```

## 6. Vérification et Monitoring

### Vérifier que les données sont bien importées

```bash
# Compter les produits dans la base
railway run python manage.py shell -c "from apps.produits.models import Produit; print(Produit.objects.count())"

# Compter les prix
railway run python manage.py shell -c "from apps.produits.models import Prix; print(Prix.objects.count())"

# Voir les dernières homologations
railway run python manage.py shell -c "from apps.produits.models import HomologationProduit; print(HomologationProduit.objects.order_by('-date_creation')[:5])"
```

### Voir les logs

```bash
# Logs en temps réel
railway logs --follow

# Logs du dernier déploiement
railway logs --deployment <deployment-id>
```

## 7. Dépannage

### Erreur : "No migrations to apply"

Cela signifie que toutes les migrations sont déjà appliquées. C'est normal.

### Erreur : "Connection refused" lors du scraping

Vérifiez que :
- Les variables d'environnement `DATABASE_URL` ou les variables DB individuelles sont correctement configurées
- Le service PostgreSQL est bien démarré dans Railway

### Erreur : "Timeout" lors du scraping

- Augmentez `DGCCRF_TIMEOUT` (par exemple, `60`)
- Réduisez `--limit` pour tester avec moins de données
- Vérifiez la connexion réseau vers `dgccrf.ga`

### Erreur : "Permission denied" pour les fichiers

Les chemins de fichiers doivent être relatifs ou utiliser des chemins absolus accessibles. Évitez d'écrire dans `/tmp` si possible, utilisez plutôt des chemins dans le projet.

## 8. Exemple de Workflow Complet

```bash
# 1. Vérifier l'état des migrations
railway run python manage.py showmigrations

# 2. Appliquer les migrations
railway run python manage.py migrate

# 3. Créer un superutilisateur (si nécessaire)
railway run python manage.py createsuperuser

# 4. Tester le scraping avec une petite limite
railway run python manage.py scrape_dgccrf --limit 10 --no-save

# 5. Si le test fonctionne, lancer le scraping complet
railway run python manage.py scrape_dgccrf

# 6. Vérifier les données importées
railway run python manage.py shell -c "from apps.produits.models import Produit, Prix; print(f'Produits: {Produit.objects.count()}, Prix: {Prix.objects.count()}')"
```

## 9. Commandes Utiles

```bash
# Collecter les fichiers statiques (si nécessaire)
railway run python manage.py collectstatic --noinput

# Vider le cache
railway run python manage.py shell -c "from django.core.cache import cache; cache.clear()"

# Voir la configuration Django
railway run python manage.py diffsettings

# Vérifier la configuration de la base de données
railway run python manage.py dbshell
```

## Notes Importantes

1. **Limites de temps** : Railway a des limites de temps pour les one-off tasks. Pour des tâches très longues, utilisez Celery.

2. **Coûts** : Les one-off tasks consomment des ressources. Surveillez votre utilisation.

3. **Logs** : Les logs sont conservés pendant une période limitée. Exportez-les si nécessaire.

4. **Sauvegarde** : Assurez-vous d'avoir des sauvegardes régulières de votre base de données.

5. **Rate Limiting** : Respectez les limites de taux du site DGCCRF en configurant `DGCCRF_REQUEST_DELAY` appropriément.

