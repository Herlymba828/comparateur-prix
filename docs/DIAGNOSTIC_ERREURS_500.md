# 🔍 Diagnostic des Erreurs 500

Guide pour diagnostiquer et résoudre les erreurs HTTP 500 sur les endpoints produits.

---

## 🚀 Diagnostic Rapide sur Railway

### 1. Tester les Endpoints Directement

```bash
# Test produits
railway run python manage.py shell -c "
from django.test import Client
client = Client()
response = client.get('/api/produits/produits/')
print(f'Status: {response.status_code}')
print(f'Content-Type: {response.get(\"Content-Type\")}')
if response.status_code != 200:
    print(f'Content: {response.content[:500]}')
"
```

### 2. Vérifier les Données de la Base

```bash
railway run python manage.py shell -c "
from apps.produits.models import Produit, Prix, Categorie
print(f'Produits: {Produit.objects.count()}')
print(f'Produits actifs: {Produit.objects.filter(est_actif=True).count()}')
print(f'Prix: {Prix.objects.count()}')
print(f'Catégories: {Categorie.objects.count()}')
"
```

### 3. Vérifier les Problèmes de Relations

```bash
railway run python manage.py shell -c "
from apps.produits.models import Produit, Prix
# Produits sans catégorie
print(f'Produits sans catégorie: {Produit.objects.filter(categorie__isnull=True).count()}')
# Produits sans prix
print(f'Produits sans prix: {Produit.objects.filter(prix__isnull=True).count()}')
# Prix sans produit
print(f'Prix sans produit: {Prix.objects.filter(produit__isnull=True).count()}')
"
```

---

## 🔧 Causes Communes des Erreurs 500

### 1. Base de Données Vide

**Symptôme :** Tous les endpoints produits retournent 500

**Solution :**
```bash
# Remplir avec des données de test
railway run python manage.py seed_data --produits 100 --magasins 5

# Ou scraper des données réelles
railway run python manage.py scrape_dgccrf --limit 100
```

### 2. Annotations Retournant None

**Symptôme :** Erreur lors du calcul des prix moyens/min/max

**Solution :** Les annotations ont été corrigées pour gérer les valeurs None, mais vérifiez que les produits ont des prix.

### 3. Relations ForeignKey NULL

**Symptôme :** `RelatedObjectDoesNotExist` dans les logs

**Solution :**
```bash
# Vérifier et corriger
railway run python manage.py shell -c "
from apps.produits.models import Produit
# Trouver les produits sans catégorie
produits_sans_cat = Produit.objects.filter(categorie__isnull=True)
print(f'Produits sans catégorie: {produits_sans_cat.count()}')
# Les corriger si nécessaire
"
```

### 4. Problèmes de Serializer

**Symptôme :** Erreur lors de la sérialisation

**Solution :** Les serializers ont été améliorés pour gérer les valeurs None.

---

## 📋 Checklist de Diagnostic

### Étape 1 : Vérifier les Données

```bash
railway run python manage.py shell -c "
from apps.produits.models import Produit, Prix, Categorie
print('=== Statistiques ===')
print(f'Produits: {Produit.objects.count()}')
print(f'Prix: {Prix.objects.count()}')
print(f'Catégories: {Categorie.objects.count()}')
"
```

### Étape 2 : Tester un Endpoint Simple

```bash
# Test catégories (plus simple)
curl https://comparo.up.railway.app/api/produits/categories/
```

### Étape 3 : Tester avec Données Minimales

```bash
# Créer une catégorie de test
railway run python manage.py shell -c "
from apps.produits.models import Categorie
cat, created = Categorie.objects.get_or_create(slug='test', defaults={'nom': 'Test'})
print(f'Catégorie créée: {created}')
"
```

### Étape 4 : Vérifier les Logs

```powershell
# PowerShell
railway logs --tail 200 | Select-String -Pattern "PRODUITS|ERROR|Exception" -CaseSensitive:$false
```

---

## 🎯 Solutions Rapides

### Si la Base est Vide

```bash
# Option 1: Seed avec données de test
railway run python manage.py seed_data --produits 50 --magasins 3

# Option 2: Scraper des données réelles
railway run python manage.py scrape_dgccrf --limit 50
```

### Si les Catégories Manquent

```bash
# Initialiser les catégories
railway run python manage.py init_categories
```

### Si les Relations sont Cassées

```bash
# Vérifier et corriger manuellement via shell
railway run python manage.py shell
```

---

## 📊 Commandes Utiles

### Voir les Erreurs dans les Logs

```powershell
# Filtrer les erreurs produits
railway logs --tail 500 | Select-String -Pattern "\[PRODUITS\].*ERROR" -CaseSensitive:$false

# Filtrer toutes les erreurs
railway logs --tail 500 | Select-String -Pattern "ERROR|Exception|Traceback" -CaseSensitive:$false
```

### Tester un Endpoint Spécifique

```bash
# Via curl (si disponible)
curl -v https://comparo.up.railway.app/api/produits/produits/

# Via Python
railway run python manage.py shell -c "
from django.test import Client
c = Client()
r = c.get('/api/produits/produits/')
print(r.status_code, r.get('Content-Type'))
"
```

---

## 🔄 Prochaines Étapes

1. **Remplir la base de données** avec `seed_data` ou `scrape_dgccrf`
2. **Vérifier les logs** pour identifier les erreurs spécifiques
3. **Tester les endpoints** un par un
4. **Corriger les problèmes** identifiés

---

**Utilisez ces commandes pour diagnostiquer les erreurs 500 !** 🎉

