# 🔧 Correction des Endpoints Frontend

Guide pour corriger les erreurs identifiées par le script de vérification frontend.

---

## 📊 Problèmes Identifiés

### ❌ Erreurs HTTP 500
- Tous les endpoints produits retournent 500
- Endpoints catégories retournent 500
- Endpoints prix retournent 500

### ⚠️ Erreurs HTML
- Certains endpoints retournent du HTML au lieu de JSON
- Indique des exceptions non gérées

### ❌ Endpoints 404
- `/api/prix/` → devrait être `/api/produits/prix/`
- `/api/magasin/` → devrait être `/api/magasins/magasins/`
- `/api/stores/` → devrait être `/api/magasins/magasins/`
- `/api/stats/prix/` → existe mais peut-être mal configuré
- `/api/produits/stats/prix/` → n'existe pas
- `/api/produits/stats/homologations/` → n'existe pas
- `/api/stats/homologations/` → n'existe pas

---

## ✅ Solutions Appliquées

### 1. Alias d'URLs pour Compatibilité Frontend

**Fichier :** `config/urls.py`

Ajout d'alias pour les URLs alternatives :

```python
# Alias pour compatibilité frontend (URLs alternatives)
path('api/prix/', include('apps.produits.urls')),  # Redirige vers /api/produits/prix/
path('api/magasin/', include('apps.magasins.urls')),  # Redirige vers /api/magasins/magasins/
path('api/stores/', include('apps.magasins.urls')),  # Alias pour /api/magasins/magasins/
```

### 2. Correction des Erreurs 500

**Problème :** Les annotations de prix peuvent retourner `None` si aucun prix n'existe, causant des erreurs dans les serializers.

**Solution :** Les annotations sont déjà filtrées par `est_disponible=True`, mais il faut s'assurer que les serializers gèrent les valeurs `None`.

### 3. Gestion des Erreurs JSON

**Problème :** Les exceptions non gérées retournent du HTML (page d'erreur Django).

**Solution :** Les vues ont déjà des blocs `try-except` qui retournent du JSON, mais il faut vérifier que toutes les vues les ont.

---

## 🔍 URLs Correctes

### Produits
- ✅ `/api/produits/produits/` - Liste des produits
- ✅ `/api/produits/produits/{id}/` - Détail d'un produit
- ✅ `/api/produits/populaires/` - Produits populaires
- ✅ `/api/produits/tous/` - Tous les produits (actifs + inactifs)
- ✅ `/api/produits/categories/` - Liste des catégories
- ✅ `/api/categories/` - Alias vers catégories

### Prix
- ✅ `/api/produits/prix/` - Liste des prix
- ✅ `/api/prix/` - Alias vers prix (nouveau)

### Magasins
- ✅ `/api/magasins/magasins/` - Liste des magasins
- ✅ `/api/magasin/` - Alias vers magasins (nouveau)
- ✅ `/api/stores/` - Alias vers magasins (nouveau)

### Statistiques
- ✅ `/api/stats/prix/` - Statistiques sur les prix
- ✅ `/api/produits/statistiques-prix/` - Statistiques prix (ViewSet)
- ✅ `/api/produits/homologations-stats/` - Statistiques homologations

---

## 🚀 Actions Immédiates

### 1. Vérifier les Logs Backend

```bash
railway logs --tail 100 | grep -i error
```

### 2. Tester les Endpoints

```bash
# Test produits
curl https://comparo.up.railway.app/api/produits/produits/

# Test prix
curl https://comparo.up.railway.app/api/produits/prix/

# Test stats
curl https://comparo.up.railway.app/api/stats/prix/

# Test magasins
curl https://comparo.up.railway.app/api/magasins/magasins/
```

### 3. Remplir la Base de Données

Si la base est vide, exécuter le seed :

```bash
railway run python manage.py seed_data --produits 100 --magasins 5
```

---

## 📝 Checklist

- [x] Alias URLs ajoutés pour compatibilité frontend
- [ ] Erreurs 500 corrigées (vérifier les logs)
- [ ] Endpoints testés manuellement
- [ ] Base de données remplie avec des données
- [ ] Frontend mis à jour avec les bonnes URLs

---

## 🎯 Résultats Attendus

Après les corrections :

- ✅ **Endpoints 404** : Devraient être résolus avec les alias
- ✅ **Erreurs 500** : Devraient être résolues après vérification des logs
- ✅ **Erreurs HTML** : Devraient être remplacées par des réponses JSON

---

**Les alias sont maintenant en place !** 🎉

