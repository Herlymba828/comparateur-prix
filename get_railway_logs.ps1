# Script pour récupérer les logs Railway et filtrer les erreurs
# Usage: .\get_railway_logs.ps1

Write-Host "📋 Récupération des logs Railway..." -ForegroundColor Cyan
Write-Host ""

# Vérifier si Railway CLI est installé
if (-not (Get-Command railway -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Railway CLI n'est pas installé" -ForegroundColor Red
    Write-Host "   Installez-le avec: npm install -g @railway/cli" -ForegroundColor Yellow
    Write-Host "   Ou téléchargez depuis: https://railway.app/cli" -ForegroundColor Yellow
    exit 1
}

Write-Host "🔍 Récupération des 200 dernières lignes de logs..." -ForegroundColor Yellow
Write-Host "   Filtrant les erreurs liées à /api/utilisateurs/" -ForegroundColor Gray
Write-Host ""

# Récupérer les logs et filtrer les erreurs
railway logs --tail 200 | Select-String -Pattern "utilisateurs|ERROR|Exception|Traceback|500" -CaseSensitive:$false

Write-Host ""
Write-Host "💡 Pour voir tous les logs en temps réel:" -ForegroundColor Cyan
Write-Host "   railway logs --tail 0" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 Pour sauvegarder les logs dans un fichier:" -ForegroundColor Cyan
Write-Host "   railway logs --tail 500 > railway_logs.txt" -ForegroundColor Gray

