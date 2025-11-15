# 🔐 Guide d'Authentification JWT - Résolution des Erreurs 401

## ⚠️ Problème Identifié

Les erreurs 401 persistent même après un refresh token réussi. Cela indique généralement que **le frontend n'utilise pas le nouveau token** retourné par l'endpoint de refresh.

## 🔍 Diagnostic

### Logs à vérifier

Les logs suivants vous aideront à diagnostiquer le problème :

1. **Token refresh réussi** : `POST /api/auth/token/refresh/ HTTP/1.1" 200`
2. **Requête suivante échoue** : `POST /api/produits/produits/5/like/ HTTP/1.1" 401`

### Causes possibles

1. **Le frontend n'utilise pas le nouveau token** après le refresh
2. **Le token est envoyé dans le mauvais format** (manque "Bearer", espaces, etc.)
3. **Le token est expiré** avant d'être utilisé
4. **Problème de synchronisation** entre le refresh et l'utilisation du token

## ✅ Solution : Utilisation Correcte du Token Refresh

### 1. Format de la Requête de Refresh

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "votre_refresh_token_ici"
}
```

### 2. Réponse du Refresh

```json
{
  "access": "nouveau_access_token_ici",
  "refresh": "nouveau_refresh_token_ici"  // Si ROTATE_REFRESH_TOKENS=True
}
```

### 3. ⚠️ IMPORTANT : Utiliser le Nouveau Token

**Le frontend DOIT utiliser le nouveau `access` token** retourné dans la réponse :

```javascript
// ❌ MAUVAIS - Utiliser l'ancien token
const response = await fetch('/api/auth/token/refresh/', {
  method: 'POST',
  body: JSON.stringify({ refresh: refreshToken })
});
const data = await response.json();
// Ne pas utiliser le nouveau token !
fetch('/api/produits/produits/5/like/', {
  headers: {
    'Authorization': `Bearer ${oldAccessToken}` // ❌ ERREUR
  }
});

// ✅ CORRECT - Utiliser le nouveau token
const response = await fetch('/api/auth/token/refresh/', {
  method: 'POST',
  body: JSON.stringify({ refresh: refreshToken })
});
const data = await response.json();
// Utiliser le nouveau token immédiatement
fetch('/api/produits/produits/5/like/', {
  headers: {
    'Authorization': `Bearer ${data.access}` // ✅ CORRECT
  }
});
```

### 4. Format du Header Authorization

Le header **DOIT** être exactement dans ce format :

```
Authorization: Bearer <token>
```

**Points importants** :
- Le mot "Bearer" (avec majuscule B)
- Un espace après "Bearer"
- Pas de guillemets autour du token
- Pas d'espaces supplémentaires

### 5. Exemple Complet (JavaScript/React)

```javascript
// Fonction pour rafraîchir le token
async function refreshToken(refreshToken) {
  const response = await fetch('/api/auth/token/refresh/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh: refreshToken })
  });
  
  if (response.ok) {
    const data = await response.json();
    // ⚠️ IMPORTANT : Sauvegarder le nouveau token
    localStorage.setItem('access_token', data.access);
    if (data.refresh) {
      localStorage.setItem('refresh_token', data.refresh);
    }
    return data.access;
  } else {
    throw new Error('Token refresh failed');
  }
}

// Fonction pour faire une requête authentifiée
async function authenticatedFetch(url, options = {}) {
  let accessToken = localStorage.getItem('access_token');
  
  // Ajouter le token au header
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
    ...options.headers
  };
  
  let response = await fetch(url, { ...options, headers });
  
  // Si 401, essayer de rafraîchir le token
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        // Rafraîchir le token
        accessToken = await refreshToken(refreshToken);
        // Réessayer la requête avec le nouveau token
        headers['Authorization'] = `Bearer ${accessToken}`;
        response = await fetch(url, { ...options, headers });
      } catch (error) {
        // Rediriger vers la page de connexion
        window.location.href = '/login';
        throw error;
      }
    }
  }
  
  return response;
}

// Utilisation
async function likeProduct(productId) {
  const response = await authenticatedFetch(
    `/api/produits/produits/${productId}/like/`,
    { method: 'POST' }
  );
  return response.json();
}
```

## 🔧 Configuration JWT Actuelle

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 1 heure
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),   # 30 jours
    'ROTATE_REFRESH_TOKENS': True,                  # Rotation activée
    'BLACKLIST_AFTER_ROTATION': True,               # Blacklist activée
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### ⚠️ Important : Rotation des Tokens

Avec `ROTATE_REFRESH_TOKENS=True` et `BLACKLIST_AFTER_ROTATION=True` :
- Chaque refresh génère un **nouveau refresh token**
- L'ancien refresh token est **blacklisté** (ne peut plus être utilisé)
- Le frontend **DOIT** sauvegarder le nouveau refresh token

## 🐛 Débogage

### Vérifier si le token est bien envoyé

Ajoutez ces logs côté frontend :

```javascript
console.log('Token utilisé:', accessToken);
console.log('Header Authorization:', `Bearer ${accessToken}`);
```

### Vérifier les logs backend

Les logs Django afficheront :
- `[JWT] Authentification réussie` - Token valide
- `[JWT] Token invalide` - Token invalide/expiré
- `[PRODUITS] Requête 'like'` - Détails de la requête

### Tester avec curl

```bash
# 1. Obtenir un token
curl -X POST http://localhost:8001/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "votre_username", "password": "votre_password"}'

# Réponse :
# {"access": "eyJ0eXAiOiJKV1QiLCJhbGc...", "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."}

# 2. Utiliser le token pour liker un produit
curl -X POST http://localhost:8001/api/produits/produits/5/like/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json"

# 3. Si 401, rafraîchir le token
curl -X POST http://localhost:8001/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "votre_refresh_token"}'

# Réponse :
# {"access": "nouveau_token_ici", "refresh": "nouveau_refresh_token_ici"}

# 4. Utiliser le NOUVEAU token
curl -X POST http://localhost:8001/api/produits/produits/5/like/ \
  -H "Authorization: Bearer nouveau_token_ici" \
  -H "Content-Type: application/json"
```

## 📋 Checklist Frontend

- [ ] Le token refresh retourne bien un nouveau `access` token
- [ ] Le nouveau token est sauvegardé immédiatement après le refresh
- [ ] Le nouveau token est utilisé dans toutes les requêtes suivantes
- [ ] Le format du header est exactement : `Authorization: Bearer <token>`
- [ ] Pas d'espaces supplémentaires ou de guillemets
- [ ] Si `ROTATE_REFRESH_TOKENS=True`, le nouveau `refresh` token est aussi sauvegardé
- [ ] L'ancien refresh token n'est plus utilisé après rotation

## 🎯 Endpoints d'Authentification

### Obtenir un token
```
POST /api/auth/token/
Body: {"username": "...", "password": "..."}
Response: {"access": "...", "refresh": "..."}
```

### Rafraîchir un token
```
POST /api/auth/token/refresh/
Body: {"refresh": "..."}
Response: {"access": "...", "refresh": "..."}  // Nouveau refresh si rotation activée
```

### Endpoints protégés (nécessitent le token)
- `POST /api/produits/produits/{id}/like/`
- `DELETE /api/produits/produits/{id}/like/`
- `GET /api/produits/produits/mes_likes/`
- `GET /api/recommandations/pour_moi/`

## 💡 Solution Rapide

Si le problème persiste, vérifiez que votre frontend :

1. **Capture bien le nouveau token** après le refresh
2. **Met à jour immédiatement** le token stocké (localStorage, state, etc.)
3. **Utilise le nouveau token** dans toutes les requêtes suivantes
4. **Gère la rotation** du refresh token si activée

Le problème est très probablement côté frontend : le token est rafraîchi mais l'ancien token continue d'être utilisé.


