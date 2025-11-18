# 🔧 Résolution des Erreurs API

Guide pour résoudre les erreurs identifiées dans l'analyse de l'API.

---

## 📊 Problèmes Identifiés

### ❌ Erreurs Serveur (HTTP 500) - 7 endpoints

**Causes possibles :**
1. Base de données vide ou mal configurée
2. Annotations de prix manquantes dans les requêtes
3. Relations ForeignKey non résolues
4. Erreurs dans les serializers

### ⚠️ Erreurs HTML - 3 endpoints

**Causes possibles :**
1. Gestion d'erreurs retournant du HTML au lieu de JSON
2. Exceptions non capturées

### ❌ Endpoint 404 - `/api/stats/prix/`

**Cause :** Endpoint non implémenté ou mal configuré

### 🔐 Authentification requise - 1 endpoint

**Normal :** Certains endpoints nécessitent une authentification

---

## ✅ Solutions Appliquées

### 1. Script de Seed pour Remplir la Base de Données

**Commande créée :** `python manage.py seed_data`

```bash
# Créer 100 produits, 5 magasins, 3 prix par produit
python manage.py seed_data

# Personnaliser les quantités
python manage.py seed_data --produits 200 --magasins 10 --prix-par-produit 5

# Supprimer et recréer toutes les données
python manage.py seed_data --clear
```

**Ce que le script crée :**
- ✅ Catégories (Alimentation, Boissons, Hygiène, etc.)
- ✅ Marques (Coca-Cola, Nestlé, Danone, etc.)
- ✅ Unités de mesure (kg, g, L, ml, unité)
- ✅ Magasins (avec adresses et téléphones)
- ✅ Produits (avec codes-barres uniques)
- ✅ Prix (variations entre magasins)

### 2. Endpoint `/api/stats/prix/` Ajouté

**URL :** `GET /api/stats/prix/`

**Réponse :**
```json
{
  "total_prix": 300,
  "prix_moyen_global": 2500.50,
  "promotions_actives": 10,
  "produits_sans_prix": 0,
  "evolution_7_jours": {
    "variation_moyenne": 2.5,
    "hausses": 50,
    "baisses": 30
  },
  "top_promotions": [...]
}
```

### 3. Amélioration de la Gestion d'Erreurs

Les vues ont été améliorées pour :
- ✅ Retourner des réponses JSON au lieu de HTML
- ✅ Capturer toutes les exceptions
- ✅ Logger les erreurs pour le débogage
- ✅ Retourner des messages d'erreur clairs

---

## 🚀 Actions Immédiates

### Étape 1 : Remplir la Base de Données

```bash
# Sur Railway
railway run python manage.py seed_data --produits 100 --magasins 5

# En local
python manage.py seed_data --produits 100 --magasins 5
```

### Étape 2 : Vérifier les Migrations

```bash
# Vérifier l'état des migrations
railway run python manage.py showmigrations

# Appliquer les migrations si nécessaire
railway run python manage.py migrate
```

### Étape 3 : Vérifier les Logs

```bash
# Voir les logs Railway
railway logs

# Filtrer les erreurs
railway logs | grep -i error
```

### Étape 4 : Tester les Endpoints

```bash
# Test de l'endpoint stats/prix
curl https://comparo.up.railway.app/api/stats/prix/

# Test des produits
curl https://comparo.up.railway.app/api/produits/

# Test des prix
curl https://comparo.up.railway.app/api/produits/prix/
```

---

## 🔍 Diagnostic des Erreurs 500

### Vérifier les Logs Backend

```bash
# Logs Railway
railway logs --tail 100

# Chercher les erreurs spécifiques
railway logs | grep "500\|ERROR\|Exception"
```

### Erreurs Communes et Solutions

#### 1. "RelatedObjectDoesNotExist" ou "ForeignKey NULL"

**Cause :** Produit sans catégorie ou prix sans produit

**Solution :**
```bash
# Vérifier les données
railway run python manage.py shell -c "
from apps.produits.models import Produit, Prix
print(f'Produits sans catégorie: {Produit.objects.filter(categorie__isnull=True).count()}')
print(f'Prix sans produit: {Prix.objects.filter(produit__isnull=True).count()}')
"
```

#### 2. "AttributeError: 'NoneType' object has no attribute..."

**Cause :** Annotation de prix retournant None

**Solution :** Les annotations ont été corrigées pour filtrer par `est_disponible=True`

#### 3. "OperationalError: no such table"

**Cause :** Migrations non appliquées

**Solution :**
```bash
railway run python manage.py migrate
```

---

## 📝 Checklist de Résolution

- [ ] Base de données remplie avec `seed_data`
- [ ] Migrations appliquées
- [ ] Endpoint `/api/stats/prix/` accessible
- [ ] Logs vérifiés (pas d'erreurs 500)
- [ ] Endpoints testés manuellement
- [ ] Frontend peut récupérer les données

---

## 🎯 Résultats Attendus

Après avoir exécuté le seed :

- ✅ **Endpoints avec données** : Tous les endpoints devraient retourner des données
- ✅ **Erreurs 500** : Devraient être résolues (vérifier les logs)
- ✅ **Erreurs HTML** : Devraient être remplacées par des réponses JSON
- ✅ **Endpoint 404** : `/api/stats/prix/` devrait maintenant fonctionner

---

## 🔄 Maintenance Continue

### Ajouter Plus de Données

```bash
# Ajouter 50 produits supplémentaires
python manage.py seed_data --produits 50
```

### Vider et Recréer

```bash
# Supprimer toutes les données et recréer
python manage.py seed_data --clear --produits 200 --magasins 10
```

### Utiliser le Scraping DGCCRF

```bash
# Scraper des données réelles depuis DGCCRF
railway run python manage.py scrape_dgccrf --limit 100
```

---

## 📚 Ressources

- [Documentation API](./API.md)
- [Guide Scraping](./SCRAPING_RAILWAY.md)
- [Configuration Railway](./CONFIGURATION_DATABASE_RAILWAY.md)

---

**Le système devrait maintenant fonctionner correctement !** 🎉

