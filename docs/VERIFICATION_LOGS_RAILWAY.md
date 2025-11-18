# 📋 Vérification des Logs Railway

Guide pour vérifier et analyser les logs Railway sur Windows PowerShell.

---

## 🔍 Commandes PowerShell pour Filtrer les Logs

### Méthode 1 : Filtrer avec Select-String (équivalent grep)

```powershell
# Filtrer les erreurs
railway logs --tail 100 | Select-String -Pattern "error|exception|500" -CaseSensitive:$false

# Filtrer les erreurs Django spécifiquement
railway logs --tail 200 | Select-String -Pattern "ERROR|Exception|Traceback" -CaseSensitive:$false

# Filtrer les erreurs produits
railway logs --tail 200 | Select-String -Pattern "PRODUITS.*ERROR|produits.*error" -CaseSensitive:$false
```

### Méthode 2 : Sauvegarder dans un fichier puis analyser

```powershell
# Sauvegarder les logs dans un fichier
railway logs --tail 500 > logs_railway.txt

# Puis ouvrir avec un éditeur de texte ou filtrer
Get-Content logs_railway.txt | Select-String -Pattern "error|exception" -CaseSensitive:$false
```

### Méthode 3 : Logs en temps réel avec filtre

```powershell
# Suivre les logs en temps réel et filtrer les erreurs
railway logs --tail 0 | Select-String -Pattern "error|exception|500" -CaseSensitive:$false
```

---

## 🎯 Commandes Utiles

### Voir tous les logs récents

```powershell
railway logs --tail 100
```

### Voir les logs d'un service spécifique

```powershell
# Si vous avez plusieurs services
railway logs --service <nom-du-service> --tail 100
```

### Filtrer par type d'erreur

```powershell
# Erreurs 500
railway logs --tail 200 | Select-String -Pattern "500|HTTP_500" -CaseSensitive:$false

# Erreurs de base de données
railway logs --tail 200 | Select-String -Pattern "database|db|postgres|sql" -CaseSensitive:$false

# Erreurs d'import
railway logs --tail 200 | Select-String -Pattern "ImportError|ModuleNotFoundError" -CaseSensitive:$false
```

---

## 🔍 Analyse des Erreurs Communes

### Erreur : "OperationalError" ou "connection failed"

**Cause :** Problème de connexion à la base de données

**Solution :**
```bash
# Vérifier DATABASE_URL
railway run python -c "import os; print(os.getenv('DATABASE_URL', 'Non défini')[:100])"
```

### Erreur : "DoesNotExist" ou "RelatedObjectDoesNotExist"

**Cause :** Relation ForeignKey manquante ou NULL

**Solution :**
```bash
# Vérifier les données
railway run python manage.py shell -c "
from apps.produits.models import Produit, Prix
print(f'Produits: {Produit.objects.count()}')
print(f'Prix: {Prix.objects.count()}')
print(f'Produits sans catégorie: {Produit.objects.filter(categorie__isnull=True).count()}')
"
```

### Erreur : "AttributeError" ou "NoneType"

**Cause :** Annotation retournant None

**Solution :** Les annotations ont été corrigées pour gérer les valeurs None

### Erreur : "IntegrityError" ou "UniqueViolation"

**Cause :** Contrainte unique violée

**Solution :** Vérifier les données dupliquées

---

## 📊 Exemple de Commande Complète

```powershell
# Récupérer les 200 dernières lignes, filtrer les erreurs, et sauvegarder
railway logs --tail 200 | Select-String -Pattern "error|exception|500|ERROR|Exception" -CaseSensitive:$false | Out-File -FilePath errors.txt

# Puis ouvrir errors.txt pour analyser
notepad errors.txt
```

---

## 🚀 Diagnostic Rapide

### 1. Vérifier l'état de l'application

```powershell
railway status
```

### 2. Voir les logs récents (sans filtre)

```powershell
railway logs --tail 50
```

### 3. Filtrer les erreurs Django

```powershell
railway logs --tail 200 | Select-String -Pattern "\[PRODUITS\]|\[PRIX\]|\[CATEGORIES\]" -CaseSensitive:$false
```

---

## 📝 Checklist de Diagnostic

- [ ] Logs récupérés avec `railway logs --tail 200`
- [ ] Erreurs filtrées avec `Select-String`
- [ ] Erreurs identifiées et analysées
- [ ] Solutions appliquées
- [ ] Application redéployée
- [ ] Logs vérifiés à nouveau

---

**Utilisez ces commandes PowerShell pour analyser vos logs Railway !** 🎉

