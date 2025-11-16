# Script PowerShell pour vérifier la qualité du code

Write-Host "🔍 Vérification de la qualité du code..." -ForegroundColor Cyan
Write-Host ""

$errors = 0

# Fonction pour vérifier le résultat
function Check-Result {
    param(
        [string]$Message,
        [int]$ExitCode
    )
    
    if ($ExitCode -eq 0) {
        Write-Host "✅ $Message" -ForegroundColor Green
    } else {
        Write-Host "❌ $Message" -ForegroundColor Red
        $script:errors++
    }
}

# 1. Black (formatage)
Write-Host "📝 Vérification du formatage avec Black..." -ForegroundColor Yellow
black --check .
Check-Result "Black: Code bien formaté" $LASTEXITCODE

# 2. isort (tri des imports)
Write-Host "📦 Vérification du tri des imports avec isort..." -ForegroundColor Yellow
isort --check-only .
Check-Result "isort: Imports bien triés" $LASTEXITCODE

# 3. Flake8 (linting)
Write-Host "🔍 Vérification avec Flake8..." -ForegroundColor Yellow
flake8 .
Check-Result "Flake8: Pas d'erreurs" $LASTEXITCODE

# 4. Pylint (analyse statique)
Write-Host "🔎 Analyse statique avec Pylint..." -ForegroundColor Yellow
pylint apps config --disable=C0111,C0103,R0903
Write-Host "⚠️  Pylint terminé (certaines erreurs peuvent être ignorées)" -ForegroundColor Yellow

# 5. Radon (complexité)
Write-Host "📊 Analyse de la complexité avec Radon..." -ForegroundColor Yellow
Write-Host "Complexité cyclomatique:"
radon cc . --min B --show-complexity
Write-Host ""
Write-Host "Indice de maintenabilité:"
radon mi . --min B

# 6. MyPy (vérification de types)
Write-Host "🔬 Vérification de types avec MyPy..." -ForegroundColor Yellow
mypy . --ignore-missing-imports
Write-Host "⚠️  MyPy terminé (certaines erreurs peuvent être ignorées)" -ForegroundColor Yellow

# 7. Bandit (sécurité)
Write-Host "🔒 Analyse de sécurité avec Bandit..." -ForegroundColor Yellow
bandit -r . -ll
Check-Result "Bandit: Analyse de sécurité terminée" $LASTEXITCODE

# 8. pip-audit (vulnérabilités des dépendances)
Write-Host "🛡️  Vérification des vulnérabilités des dépendances..." -ForegroundColor Yellow
pip-audit --requirement requirements.txt
Check-Result "pip-audit: Vérification terminée" $LASTEXITCODE

Write-Host ""
if ($errors -eq 0) {
    Write-Host "✨ Toutes les vérifications sont terminées!" -ForegroundColor Green
} else {
    Write-Host "⚠️  $errors erreur(s) détectée(s)" -ForegroundColor Red
    exit 1
}

