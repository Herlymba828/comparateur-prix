# Script de test pour l'endpoint batch des prix
# Usage: .\scripts\test_batch_endpoint.ps1
#        .\scripts\test_batch_endpoint.ps1 -ProduitIds 1,2,3,4,5 -MagasinIds 10,20

param(
    [int[]]$ProduitIds = @(1, 2, 3),
    [int[]]$MagasinIds = $null,
    [bool]$IncludeStats = $true,
    [string]$BaseUrl = "http://localhost:8000"
)

Write-Host "[INFO] Test de l'endpoint batch des prix" -ForegroundColor Cyan
Write-Host "[INFO] Produit IDs: $($ProduitIds -join ', ')" -ForegroundColor Gray

# Construire le body
$body = @{
    produit_ids = $ProduitIds
    include_stats = $IncludeStats
}

if ($MagasinIds) {
    $body['magasin_ids'] = $MagasinIds
    Write-Host "[INFO] Magasin IDs: $($MagasinIds -join ', ')" -ForegroundColor Gray
}

$jsonBody = $body | ConvertTo-Json -Depth 10
$url = "$BaseUrl/api/produits/prix/batch/"

Write-Host "[INFO] URL: $url" -ForegroundColor Gray
Write-Host "[INFO] Body: $jsonBody" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $url `
        -Method POST `
        -ContentType "application/json" `
        -Body $jsonBody `
        -ErrorAction Stop
    
    Write-Host "[SUCCESS] Requête réussie!" -ForegroundColor Green
    Write-Host "[INFO] Nombre de résultats: $($response.count)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Résultats:" -ForegroundColor Yellow
    $response | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "[ERROR] Erreur lors de la requête" -ForegroundColor Red
    Write-Host "Status Code: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response Body: $responseBody" -ForegroundColor Red
    } else {
        Write-Host "Exception: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    exit 1
}

