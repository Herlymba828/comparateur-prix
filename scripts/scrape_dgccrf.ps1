# Script PowerShell pour lancer le scraping DGCCRF et sauvegarder les données
# Usage: .\scripts\scrape_dgccrf.ps1
#        .\scripts\scrape_dgccrf.ps1 -Limit 50
#        .\scripts\scrape_dgccrf.ps1 -Sources "liste_produit,prix_homologue"

param(
    [int]$Limit = $null,
    [string]$Sources = "liste_produit",
    [switch]$NoSave,
    [switch]$OnlyChanged
)

# Force UTF-8
try { chcp 65001 > $null } catch { }
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

# Trouver le répertoire du projet
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

# Trouver l'environnement virtuel
$VenvActivate = $null
$VenvCandidates = @(
    (Join-Path $ProjectDir "venv\Scripts\Activate.ps1"),
    (Join-Path (Split-Path -Parent $ProjectDir) "venv\Scripts\Activate.ps1")
)

foreach ($cand in $VenvCandidates) {
    if (Test-Path $cand) {
        $VenvActivate = $cand
        break
    }
}

if (-not $VenvActivate) {
    Write-Warning "Environnement virtuel non trouvé. Activez-le manuellement."
} else {
    Write-Host "[INFO] Activation de l'environnement virtuel: $VenvActivate" -ForegroundColor Cyan
    . $VenvActivate
}

# Changer vers le répertoire du projet
Set-Location $ProjectDir

# Construire la commande
$cmdArgs = @("manage.py", "scrape_dgccrf")
if ($Limit) {
    $cmdArgs += "--limit", $Limit
}
if ($Sources) {
    $cmdArgs += "--sources", $Sources
}
if ($NoSave) {
    $cmdArgs += "--no-save"
}
if ($OnlyChanged) {
    $cmdArgs += "--only-changed"
}

Write-Host "[INFO] Lancement du scraping DGCCRF..." -ForegroundColor Cyan
Write-Host "[INFO] Commande: python $($cmdArgs -join ' ')" -ForegroundColor Gray

# Exécuter la commande
python $cmdArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Scraping terminé avec succès!" -ForegroundColor Green
} else {
    Write-Host "`n[ERROR] Le scraping a échoué (code: $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

