# 🚀 Démarrage Rapide - Améliorations du Code

Guide rapide pour utiliser tous les outils d'amélioration du code.

---

## 📦 Installation

```bash
# Installer les dépendances de développement
pip install -r requirements-dev.txt

# Installer les hooks pre-commit
pre-commit install
```

---

## 🔧 Utilisation quotidienne

### Formater le code automatiquement

```bash
# Formater tout le code
black .
isort .

# Ou utiliser pre-commit (automatique avant chaque commit)
pre-commit run --all-files
```

### Vérifier la qualité du code

**Linux/Mac** :
```bash
bash scripts/check_code_quality.sh
```

**Windows** :
```powershell
.\scripts\check_code_quality.ps1
```

### Exécuter les tests

```bash
# Tous les tests
pytest

# Avec coverage
pytest --cov=. --cov-report=html

# Tests spécifiques
pytest apps/produits/tests/
```

### Vérifier la sécurité

```bash
# Scanner le code
bandit -r . -ll

# Scanner les dépendances
pip-audit --requirement requirements.txt
safety check
```

---

## 📋 Commandes utiles

### Qualité de code

```bash
# Black (formatage)
black .                    # Formater
black --check .            # Vérifier

# isort (imports)
isort .                    # Trier
isort --check-only .       # Vérifier

# Flake8 (linting)
flake8 .

# Pylint (analyse)
pylint apps config

# Radon (complexité)
radon cc . --min B         # Complexité
radon mi . --min B         # Maintenabilité

# MyPy (types)
mypy . --ignore-missing-imports
```

### Sécurité

```bash
# Bandit
bandit -r . -ll

# pip-audit
pip-audit --requirement requirements.txt

# Safety
safety check
```

### Tests

```bash
# Tests avec coverage
pytest --cov=. --cov-report=html

# Tests spécifiques
pytest apps/produits/tests/test_services.py

# Tests avec markers
pytest -m "not slow"
```

---

## 🔄 Workflow recommandé

1. **Avant de commiter** :
   ```bash
   # Les hooks pre-commit s'exécutent automatiquement
   git add .
   git commit -m "Votre message"
   ```

2. **Avant de push** :
   ```bash
   # Vérifier manuellement si nécessaire
   bash scripts/check_code_quality.sh
   pytest
   ```

3. **Avant une PR** :
   - Exécuter tous les checks
   - Vérifier que les tests passent
   - Vérifier la coverage (> 80%)
   - Vérifier la sécurité

---

## 📚 Documentation complète

- **Guide complet** : `docs/AMELIORATION_CODE.md`
- **Guide de refactoring** : `docs/REFACTORING_GUIDE.md`
- **Configuration CI/CD** : `.github/workflows/ci.yml`

---

## 🎯 Objectifs de qualité

- **Coverage** : > 80%
- **Complexité cyclomatique** : < 10 par fonction
- **Indice de maintenabilité** : > 70
- **Pas de vulnérabilités** : Bandit, pip-audit, safety

---

## 🆘 Problèmes courants

### Pre-commit échoue

```bash
# Réinstaller les hooks
pre-commit uninstall
pre-commit install
```

### Tests échouent

```bash
# Vérifier la base de données de test
python manage.py migrate --run-syncdb
```

### Coverage trop bas

```bash
# Voir le rapport détaillé
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

---

## ✅ Checklist avant commit

- [ ] Code formaté (Black)
- [ ] Imports triés (isort)
- [ ] Pas d'erreurs Flake8
- [ ] Tests passent
- [ ] Coverage maintenu
- [ ] Pas de vulnérabilités (Bandit)
- [ ] Documentation à jour

