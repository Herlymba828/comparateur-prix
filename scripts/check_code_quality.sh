#!/bin/bash
# Script pour vérifier la qualité du code

set -e

echo "🔍 Vérification de la qualité du code..."
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les résultats
check_result() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# 1. Black (formatage)
echo "📝 Vérification du formatage avec Black..."
black --check .
check_result "Black: Code bien formaté"

# 2. isort (tri des imports)
echo "📦 Vérification du tri des imports avec isort..."
isort --check-only .
check_result "isort: Imports bien triés"

# 3. Flake8 (linting)
echo "🔍 Vérification avec Flake8..."
flake8 .
check_result "Flake8: Pas d'erreurs"

# 4. Pylint (analyse statique)
echo "🔎 Analyse statique avec Pylint..."
pylint apps config --disable=C0111,C0103,R0903 || true
echo -e "${YELLOW}⚠️  Pylint terminé (certaines erreurs peuvent être ignorées)${NC}"

# 5. Radon (complexité)
echo "📊 Analyse de la complexité avec Radon..."
echo "Complexité cyclomatique:"
radon cc . --min B --show-complexity
echo ""
echo "Indice de maintenabilité:"
radon mi . --min B
check_result "Radon: Analyse terminée"

# 6. MyPy (vérification de types)
echo "🔬 Vérification de types avec MyPy..."
mypy . --ignore-missing-imports || true
echo -e "${YELLOW}⚠️  MyPy terminé (certaines erreurs peuvent être ignorées)${NC}"

# 7. Bandit (sécurité)
echo "🔒 Analyse de sécurité avec Bandit..."
bandit -r . -ll || true
check_result "Bandit: Analyse de sécurité terminée"

# 8. pip-audit (vulnérabilités des dépendances)
echo "🛡️  Vérification des vulnérabilités des dépendances..."
pip-audit --requirement requirements.txt || true
check_result "pip-audit: Vérification terminée"

echo ""
echo -e "${GREEN}✨ Toutes les vérifications sont terminées!${NC}"

