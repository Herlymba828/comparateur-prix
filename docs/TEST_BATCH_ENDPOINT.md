# Test de l'endpoint Batch Prix

## PowerShell (Windows)

### Méthode 1 : Invoke-WebRequest (recommandé)

```powershell
$body = @{
    produit_ids = @(1, 2, 3)
    include_stats = $true
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/api/produits/prix/batch/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body `
    | Select-Object -ExpandProperty Content
```

### Méthode 2 : Invoke-RestMethod (plus simple)

```powershell
$body = @{
    produit_ids = @(1, 2, 3)
    include_stats = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/produits/prix/batch/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Méthode 3 : Avec magasin_ids

```powershell
$body = @{
    produit_ids = @(1, 2, 3)
    magasin_ids = @(10, 20)
    include_stats = $true
    filters = @{
        est_promotion = $true
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/produits/prix/batch/" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### Méthode 4 : curl.exe (si curl est installé)

Si vous avez curl.exe installé (pas l'alias PowerShell), utilisez :

```powershell
curl.exe -X POST http://localhost:8000/api/produits/prix/batch/ `
    -H "Content-Type: application/json" `
    -d '{\"produit_ids\": [1, 2, 3], \"include_stats\": true}'
```

## Python (avec requests)

```python
import requests
import json

url = "http://localhost:8000/api/produits/prix/batch/"
data = {
    "produit_ids": [1, 2, 3],
    "include_stats": True
}

response = requests.post(url, json=data)
print(response.json())
```

## Exemple de réponse attendue

```json
{
    "count": 3,
    "results": [
        {
            "prix_id": 1,
            "produit_id": 1,
            "produit_nom": "Produit 1",
            "magasin_id": 10,
            "magasin_nom": "Magasin A",
            "prix_actuel": 1500.00,
            "prix_origine": null,
            "est_promotion": false,
            "pourcentage_promotion": 0,
            "devise": "FCFA",
            "date_modification": "2025-11-14T10:30:00Z",
            "disponible": true,
            "stats": {
                "produit_id": 1,
                "prix_min": 1500.00,
                "prix_max": 2000.00,
                "prix_moyen": 1750.00,
                "nombre_magasins": 5,
                "nombre_promotions": 1,
                "last_update": "2025-11-14T10:30:00Z"
            },
            "position_relative": 0.0
        },
        ...
    ]
}
```

## Erreurs possibles

### 400 Bad Request - Validation
```json
{
    "produit_ids": ["Ce champ est requis."]
}
```

### 400 Bad Request - Trop de produits
```json
{
    "error": "Maximum 100 produits par requête batch"
}
```

### 500 Internal Server Error
Vérifier les logs Django pour plus de détails.

