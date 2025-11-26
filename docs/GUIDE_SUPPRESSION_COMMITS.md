# Guide : Supprimer des commits Git

## ⚠️ AVERTISSEMENT IMPORTANT

**Si les commits sont déjà sur GitHub et partagés avec d'autres développeurs :**
- ⛔ **NE PAS** utiliser `git push --force` sans coordination
- Cela peut causer des problèmes pour les autres développeurs
- Préférez créer de nouveaux commits pour corriger

---

## Option 1 : Rebase Interactif (Pour supprimer/combiner des commits)

### Étape 1 : Lancer le rebase interactif
```bash
# Réviser les 10 derniers commits
git rebase -i HEAD~10

# Ou réviser depuis un commit spécifique
git rebase -i <commit-hash>
```

### Étape 2 : Dans l'éditeur qui s'ouvre
- Remplacez `pick` par `drop` pour **supprimer** un commit
- Remplacez `pick` par `squash` ou `fixup` pour **combiner** avec le commit précédent
- Sauvegardez et fermez l'éditeur

### Étape 3 : Force push (⚠️ DANGEREUX)
```bash
git push --force origin main
# OU (plus sûr, évite d'écraser les commits des autres)
git push --force-with-lease origin main
```

---

## Option 2 : Reset (Pour revenir à un commit antérieur)

### Soft Reset (garde les modifications)
```bash
# Revenir au commit 155d59d5 (garde les modifications en staging)
git reset --soft 155d59d5

# Puis créer un nouveau commit
git commit -m "Nouveau message"
```

### Hard Reset (⚠️ SUPPRIME les modifications)
```bash
# Revenir au commit 155d59d5 (SUPPRIME toutes les modifications)
git reset --hard 155d59d5

# Force push
git push --force origin main
```

---

## Option 3 : Créer un nouveau commit de correction (RECOMMANDÉ)

**Au lieu de supprimer les commits, créez un nouveau commit qui corrige :**

```bash
# Faire vos modifications
git add .
git commit -m "fix: Correction des erreurs d'inscription"
git push origin main
```

**Avantages :**
- ✅ Pas de risque pour les autres développeurs
- ✅ Historique complet conservé
- ✅ Plus sûr en production

---

## Option 4 : Supprimer seulement les commits locaux (pas encore poussés)

Si vous avez des commits locaux non poussés :

```bash
# Voir les commits locaux non poussés
git log origin/main..HEAD

# Supprimer les N derniers commits (garde les modifications)
git reset --soft HEAD~N

# OU supprimer complètement (⚠️ supprime les modifications)
git reset --hard HEAD~N
```

---

## Exemples pratiques

### Exemple 1 : Supprimer les 2 derniers commits
```bash
git rebase -i HEAD~2
# Dans l'éditeur : changer 'pick' en 'drop' pour les commits à supprimer
git push --force-with-lease origin main
```

### Exemple 2 : Combiner les 3 derniers commits en un seul
```bash
git rebase -i HEAD~3
# Dans l'éditeur : 
# - Laisser 'pick' pour le premier commit
# - Changer 'pick' en 'squash' pour les 2 autres
git push --force-with-lease origin main
```

### Exemple 3 : Revenir à un commit spécifique
```bash
# Revenir au commit "Mise à jour des endpoints de l'API"
git reset --soft 155d59d5
git commit -m "Nouveau commit combiné"
git push --force-with-lease origin main
```

---

## ⚠️ Commandes DANGEREUSES

Ces commandes peuvent **détruire votre travail** :

```bash
# ⛔ SUPPRIME TOUT (modifications + commits)
git reset --hard <commit>

# ⛔ ÉCRASE l'historique sur GitHub
git push --force origin main

# ⛔ SUPPRIME les commits non poussés
git reset --hard origin/main
```

**Toujours utiliser `--force-with-lease` au lieu de `--force` :**
```bash
# ✅ Plus sûr : échoue si quelqu'un d'autre a poussé entre-temps
git push --force-with-lease origin main
```

---

## Récupérer après une erreur

Si vous avez supprimé des commits par erreur :

```bash
# Voir l'historique complet (y compris les commits supprimés)
git reflog

# Revenir à un commit spécifique
git reset --hard <commit-hash-from-reflog>
```

---

## Recommandation pour votre projet

**Vu que vous travaillez seul sur ce projet :**

1. **Pour nettoyer l'historique** : Utilisez `git rebase -i` pour combiner les commits de correction
2. **Pour supprimer des commits** : Utilisez `git reset --soft` puis créez un nouveau commit
3. **Toujours utiliser** : `git push --force-with-lease` au lieu de `--force`

**Exemple de nettoyage :**
```bash
# Combiner les commits de correction en un seul
git rebase -i HEAD~5
# Dans l'éditeur, garder le premier et mettre 'squash' pour les autres
git push --force-with-lease origin main
```

