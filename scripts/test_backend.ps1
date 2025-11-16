# Script de test du backend - PowerShell
# Usage: .\scripts\test_backend.ps1

$BASE_URL = "https://ftp.navixtechnology.com"
$testsPassed = 0
$testsFailed = 0

Write-Host "🔍 Test du backend Django..." -ForegroundColor Cyan
Write-Host "URL de base: $BASE_URL" -ForegroundColor Gray
Write-Host ""

# Fonction pour tester un endpoint
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Method = "GET",
        [string]$Description,
        [hashtable]$Headers = @{},
        [string]$Body = $null
    )
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            Headers = $Headers
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = $Body
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-WebRequest @params
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq 200 -or $statusCode -eq 201) {
            Write-Host "✅ $Description : OK (Status: $statusCode)" -ForegroundColor Green
            if ($response.Content) {
                try {
                    $json = $response.Content | ConvertFrom-Json
                    Write-Host "   Réponse: $($json | ConvertTo-Json -Compress)" -ForegroundColor Gray
                } catch {
                    Write-Host "   Réponse: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))..." -ForegroundColor Gray
                }
            }
            return $true
        } else {
            Write-Host "❌ $Description : ÉCHEC (Status: $statusCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "❌ $Description : ÉCHEC (Status: $statusCode)" -ForegroundColor Red
        Write-Host "   Erreur: $($_.Exception.Message)" -ForegroundColor Yellow
        return $false
    }
}

# Test 1: Health Check
Write-Host "1. Test Health Check..." -ForegroundColor Yellow
if (Test-Endpoint -Url "$BASE_URL/api/health/" -Description "Health Check") {
    $testsPassed++
} else {
    $testsFailed++
}
Write-Host ""

# Test 2: Test Connection
Write-Host "2. Test Connection..." -ForegroundColor Yellow
if (Test-Endpoint -Url "$BASE_URL/api/test-connection/" -Description "Test Connection") {
    $testsPassed++
} else {
    $testsFailed++
}
Write-Host ""

# Test 3: Swagger Documentation
Write-Host "3. Test Swagger Documentation..." -ForegroundColor Yellow
if (Test-Endpoint -Url "$BASE_URL/api/docs/" -Description "Swagger UI") {
    $testsPassed++
} else {
    $testsFailed++
}
Write-Host ""

# Test 4: API Produits
Write-Host "4. Test API Produits..." -ForegroundColor Yellow
if (Test-Endpoint -Url "$BASE_URL/api/produits/produits/" -Description "API Produits") {
    $testsPassed++
} else {
    $testsFailed++
}
Write-Host ""

# Test 5: Recherche de produits
Write-Host "5. Test Recherche Produits..." -ForegroundColor Yellow
if (Test-Endpoint -Url "$BASE_URL/api/search/produits/?q=eau" -Description "Recherche Produits") {
    $testsPassed++
} else {
    $testsFailed++
}
Write-Host ""

# Test 6: Autocomplete
Write-Host "6. Test Autocomplete..." -ForegroundColor Yellow
if (Test-Endpoint -Url "$BASE_URL/api/search/autocomplete/?q=eau" -Description "Autocomplete") {
    $testsPassed++
} else {
    $testsFailed++
}
Write-Host ""

# Test 7: Admin Django
Write-Host "7. Test Admin Django..." -ForegroundColor Yellow
if (Test-Endpoint -Url "$BASE_URL/admin/" -Description "Admin Django") {
    $testsPassed++
} else {
    $testsFailed++
}
Write-Host ""

# Test 8: Authentification (si credentials fournis)
$username = Read-Host "Voulez-vous tester l'authentification? (o/n)"
if ($username -eq "o" -or $username -eq "O") {
    $testUsername = Read-Host "Username"
    $testPassword = Read-Host "Password" -AsSecureString
    $plainPassword = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($testPassword)
    )
    
    $body = @{
        username = $testUsername
        password = $plainPassword
    } | ConvertTo-Json
    
    Write-Host "8. Test Authentification JWT..." -ForegroundColor Yellow
    if (Test-Endpoint -Url "$BASE_URL/api/auth/token/" -Method "POST" -Description "Authentification JWT" -Body $body) {
        $testsPassed++
    } else {
        $testsFailed++
    }
    Write-Host ""
}

# Résumé
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📊 Résumé des tests" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ Tests réussis: $testsPassed" -ForegroundColor Green
Write-Host "❌ Tests échoués: $testsFailed" -ForegroundColor $(if ($testsFailed -gt 0) { "Red" } else { "Green" })
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "🎉 Tous les tests sont passés! Le backend est fonctionnel." -ForegroundColor Green
} else {
    Write-Host "⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Conseils de dépannage:" -ForegroundColor Cyan
    Write-Host "   1. Vérifiez que le serveur est en ligne" -ForegroundColor Gray
    Write-Host "   2. Vérifiez les logs d'erreur sur le serveur" -ForegroundColor Gray
    Write-Host "   3. Vérifiez la configuration dans cPanel" -ForegroundColor Gray
    Write-Host "   4. Vérifiez le fichier .env sur le serveur" -ForegroundColor Gray
}

