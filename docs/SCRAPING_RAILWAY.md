# 🔄 Scraping DGCCRF sur Railway

Guide pour exécuter le scraping DGCCRF sur Railway.

---

## 🚀 Exécution du Scraping

### Méthode 1 : Via Railway CLI (Recommandé)

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

# Scraping complet (tous les éléments, même non modifiés)
railway run python manage.py scrape_dgccrf --no-only-changed
```

### Méthode 2 : Via Railway Dashboard

1. Allez sur https://railway.app
2. Ouvrez votre projet
3. Cliquez sur votre service Django
4. Allez dans l'onglet **"Deployments"**
5. Cliquez sur le dernier déploiement
6. Ouvrez l'onglet **"Logs"** ou **"Shell"**
7. Exécutez la commande :
   ```bash
   python manage.py scrape_dgccrf
   ```

---

## 📋 Options disponibles

### `--limit N`
Limite le nombre d'éléments à scraper (utile pour les tests)

```bash
railway run python manage.py scrape_dgccrf --limit 100
```

### `--sources SOURCES`
Sources à scraper, séparées par des virgules

**Sources disponibles :**
- `auto` : Détection automatique (JSON/CSV)
- `prix_homologue` : Page prix homologués (HTML)
- `liste_produit` : Page liste de produits (HTML)
- `produit_petrolier` : Produits pétroliers (HTML)

**Exemples :**
```bash
# Une seule source
railway run python manage.py scrape_dgccrf --sources liste_produit

# Plusieurs sources
railway run python manage.py scrape_dgccrf --sources liste_produit,prix_homologue

# Toutes les sources (par défaut)
railway run python manage.py scrape_dgccrf --sources auto,prix_homologue,liste_produit,produit_petrolier
```

### `--no-save`
Ne pas sauvegarder en base de données (test uniquement)

```bash
railway run python manage.py scrape_dgccrf --no-save --limit 10
```

### `--only-changed` (par défaut: True)
Ne scraper que les éléments modifiés depuis la dernière extraction

```bash
# Mode incrémental (par défaut)
railway run python manage.py scrape_dgccrf --only-changed

# Scraping complet (tous les éléments)
railway run python manage.py scrape_dgccrf --no-only-changed
```

---

## 📊 Résultats

### Sauvegarde en base de données

Les données sont automatiquement sauvegardées dans :
- **Produit** : Produits extraits
- **Prix** : Prix associés aux produits
- **HomologationProduit** : Produits homologués
- **PrixHomologue** : Prix homologués par zone

### Rapport généré

Un rapport JSON est généré dans `data/dgccrf_YYYYMMDD_HHMMSS_report.json` :

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

## 🔍 Vérification

### Vérifier les données sauvegardées

```bash
# Compter les produits
railway run python manage.py shell -c "from apps.produits.models import Produit; print(f'Produits: {Produit.objects.count()}')"

# Compter les prix
railway run python manage.py shell -c "from apps.produits.models import Prix; print(f'Prix: {Prix.objects.count()}')"

# Compter les homologations
railway run python manage.py shell -c "from apps.produits.models import HomologationProduit; print(f'Homologations: {HomologationProduit.objects.count()}')"

# Derniers produits ajoutés
railway run python manage.py shell -c "from apps.produits.models import Produit; [print(f'{p.nom} - {p.date_creation}') for p in Produit.objects.order_by('-date_creation')[:10]]"
```

---

## ⚙️ Automatisation

Le scraping est automatiquement planifié via Celery Beat :

- **Quotidien** : Scraping incrémental (tous les jours)
- **Hebdomadaire** : Rafraîchissement complet (tous les 7 jours)
- **Mensuel** : Rafraîchissement complet avec exports (tous les 30 jours)

Voir `docs/AUTOMATISATION_SCRAPING_BACKUP.md` pour plus de détails.

---

## 🐛 Dépannage

### Erreur : "Connection refused"

**Cause :** La base de données n'est pas accessible.

**Solution :**
1. Vérifiez que PostgreSQL est créé dans Railway
2. Vérifiez que `DATABASE_URL` est présent dans les variables d'environnement
3. Vérifiez les logs Railway pour plus de détails

### Erreur : "No module named 'scraper_dgccrf'"

**Solution :**
```bash
# Vérifier que le fichier existe
railway run ls scripts/scraper_dgccrf.py
```

### Erreur : "Timeout"

**Cause :** Le scraping prend trop de temps.

**Solution :**
```bash
# Utiliser une limite pour tester
railway run python manage.py scrape_dgccrf --limit 100
```

---

## 📝 Exemples complets

### Test rapide (10 éléments, pas de sauvegarde)

```bash
railway run python manage.py scrape_dgccrf --limit 10 --no-save
```

### Scraping complet d'une source spécifique

```bash
railway run python manage.py scrape_dgccrf --sources liste_produit --no-only-changed
```

### Scraping avec sauvegarde (production)

```bash
railway run python manage.py scrape_dgccrf
```

---

## ✅ Checklist

- [ ] Railway CLI installé et connecté
- [ ] Projet Railway lié (`railway link`)
- [ ] Service PostgreSQL créé
- [ ] `DATABASE_URL` configuré
- [ ] Commandes testées avec `--limit` d'abord
- [ ] Logs vérifiés

---

## 🎯 Résumé

1. **Exécution** : `railway run python manage.py scrape_dgccrf`
2. **Options** : `--limit`, `--sources`, `--no-save`, `--only-changed`
3. **Résultats** : Données sauvegardées en base + rapport JSON
4. **Automatisation** : Planifiée via Celery Beat

**Le scraping est prêt à être utilisé sur Railway !** 🎉

