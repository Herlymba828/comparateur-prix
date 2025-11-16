# 🔧 Résolution : Erreur d'environnement virtuel

## 🚨 Problème

```
Fatal error in launcher: Unable to create process using '"C:\Users\herly\Downloads\soutenance2.0\venv\Scripts\python.exe"'
```

**Cause** : L'environnement virtuel pointe vers un ancien chemin Python qui n'existe plus.

---

## ✅ Solutions

### Solution 1 : Utiliser python -m pip (Rapide)

Au lieu d'utiliser `pip` directement, utilisez :

```powershell
python -m pip install -r requirements-dev.txt
```

Cela utilise le Python de l'environnement virtuel actuel.

---

### Solution 2 : Réinstaller pip dans l'environnement virtuel

```powershell
# Activer l'environnement virtuel (si pas déjà fait)
.\venv\Scripts\Activate.ps1

# Réinstaller pip
python -m ensurepip --upgrade

# Puis installer les dépendances
python -m pip install -r requirements-dev.txt
```

---

### Solution 3 : Recréer l'environnement virtuel (Recommandé)

Si les solutions précédentes ne fonctionnent pas :

#### Étape 1 : Désactiver l'ancien environnement

```powershell
deactivate
```

#### Étape 2 : Supprimer l'ancien environnement

```powershell
# Supprimer le dossier venv
Remove-Item -Recurse -Force venv
```

#### Étape 3 : Créer un nouvel environnement virtuel

```powershell
# Créer un nouvel environnement virtuel
python -m venv venv

# Activer le nouvel environnement
.\venv\Scripts\Activate.ps1

# Vérifier que Python est correct
python --version
where python
# Doit afficher : C:\Users\herly\Videos\Projects\comparateur_prix\venv\Scripts\python.exe
```

#### Étape 4 : Mettre à jour pip

```powershell
python -m pip install --upgrade pip
```

#### Étape 5 : Installer les dépendances

```powershell
# D'abord les dépendances de base
python -m pip install -r requirements.txt

# Puis les dépendances de développement
python -m pip install -r requirements-dev.txt
```

---

## 🔍 Vérification

Après avoir résolu le problème, vérifiez :

```powershell
# Vérifier que pip fonctionne
pip --version

# Vérifier le chemin Python
where python
# Doit pointer vers : C:\Users\herly\Videos\Projects\comparateur_prix\venv\Scripts\python.exe

# Vérifier que les outils sont installés
black --version
isort --version
flake8 --version
```

---

## 🚨 Si l'erreur persiste

### Vérifier les permissions PowerShell

Si vous avez une erreur d'exécution de script :

```powershell
# Vérifier la politique d'exécution
Get-ExecutionPolicy

# Si nécessaire, changer temporairement
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Utiliser le terminal CMD

Si PowerShell pose problème, utilisez CMD :

```cmd
cd C:\Users\herly\Videos\Projects\comparateur_prix
venv\Scripts\activate.bat
python -m pip install -r requirements-dev.txt
```

---

## 📋 Checklist

- [ ] Environnement virtuel activé
- [ ] `python --version` fonctionne
- [ ] `where python` pointe vers le bon chemin
- [ ] `python -m pip --version` fonctionne
- [ ] Dépendances installées avec succès

---

## 💡 Prévention

Pour éviter ce problème à l'avenir :

1. **Ne pas déplacer** le dossier du projet après avoir créé l'environnement virtuel
2. **Recréer l'environnement virtuel** si vous déplacez le projet
3. **Utiliser `python -m pip`** au lieu de `pip` directement si vous avez des doutes

