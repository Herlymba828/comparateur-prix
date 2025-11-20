# Script de redémarrage du serveur Django
# Usage: .\restart_django.ps1

Write-Host "🔄 Redémarrage du serveur Django..." -ForegroundColor Cyan

# Trouver le processus Django qui écoute sur le port 8000
$port = 8000
$process = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique

if ($process) {
    Write-Host "📌 Processus trouvé sur le port $port : PID $process" -ForegroundColor Yellow
    try {
        Stop-Process -Id $process -Force -ErrorAction Stop
        Write-Host "✅ Processus arrêté avec succès" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "⚠️  Impossible d'arrêter le processus automatiquement. Veuillez l'arrêter manuellement (Ctrl+C dans le terminal Django)" -ForegroundColor Red
        Write-Host "   Puis relancez: python manage.py runserver" -ForegroundColor Yellow
        exit 1
    }
} else {
    Write-Host "ℹ️  Aucun processus trouvé sur le port $port" -ForegroundColor Gray
}

# Vérifier si Python est disponible
$pythonCmd = "python"
if (-not (Get-Command $pythonCmd -ErrorAction SilentlyContinue)) {
    $pythonCmd = "python3"
    if (-not (Get-Command $pythonCmd -ErrorAction SilentlyContinue)) {
        Write-Host "❌ Python n'est pas trouvé dans le PATH" -ForegroundColor Red
        exit 1
    }
}

Write-Host "🚀 Démarrage du serveur Django..." -ForegroundColor Cyan
Write-Host "   Commande: $pythonCmd manage.py runserver 0.0.0.0:8000" -ForegroundColor Gray
Write-Host ""
Write-Host "📋 La stacktrace complète s'affichera ci-dessous lors des erreurs" -ForegroundColor Yellow
Write-Host "   Appuyez sur Ctrl+C pour arrêter le serveur" -ForegroundColor Yellow
Write-Host ""

# Démarrer le serveur Django
& $pythonCmd manage.py runserver 0.0.0.0:8000

