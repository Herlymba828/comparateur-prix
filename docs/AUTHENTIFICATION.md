# 🔐 Guide Complet : Authentification

Guide complet pour l'authentification : tokens JWT, OAuth Google, et dépannage.

## 📋 Table des matières

- [Tokens API](#tokens-api)
- [Dépannage OAuth Google](#dépannage-oauth-google)
- [Configuration JWT](#configuration-jwt)
- [Utilisation Frontend](#utilisation-frontend)

---

## 🎫 Tokens API

### Vue d'ensemble

Ce document décrit tous les types de tokens envoyés par l'API et dans quels endpoints ils sont retournés.

### Types de Tokens

#### 1. **JWT Access Token** (`access`)
- **Durée de vie** : 1 heure (60 minutes)
- **Usage** : Authentification pour les requêtes API protégées
- **Format** : `Bearer <token>` dans le header `Authorization`

#### 2. **JWT Refresh Token** (`refresh`)
- **Durée de vie** : 30 jours
- **Usage** : Obtenir un nouveau access token quand l'ancien expire
- **Rotation** : Activée (`ROTATE_REFRESH_TOKENS=True`)
  - Chaque refresh génère un **nouveau refresh token**
  - L'ancien refresh token est **blacklisté**

#### 3. **Code d'Activation** (activation code)
- **Durée de vie** : 15 minutes
- **Usage** : Activer un compte utilisateur après inscription
- **Format** : Code à 6 chiffres (ex: `123456`)
- **Envoi** : Par email uniquement (pas dans la réponse API pour la sécurité)

### Endpoints qui Retournent des Tokens

#### ✅ 1. Inscription (`POST /api/auth/register/`)

**Réponse (201 Created)** :
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john.doe@example.com",
    ...
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "activation_pending": true,
  "user_id": 1
}
```

**Tokens envoyés** :
- ✅ `refresh` : Token JWT de rafraîchissement
- ✅ `access` : Token JWT d'accès
- ✅ Code d'activation : Envoyé par email (pas dans la réponse)
- ✅ `user_id` : ID utilisateur pour vérifier le code d'activation

---

#### ✅ 2. Création Utilisateur (`POST /api/utilisateurs/`)

**Réponse (201 Created)** :
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john.doe@example.com",
  ...
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "activation_pending": true,
  "user_id": 1
}
```

**Tokens envoyés** :
- ✅ `refresh` : Token JWT de rafraîchissement
- ✅ `access` : Token JWT d'accès
- ✅ Code d'activation : Envoyé par email (pas dans la réponse)
- ✅ `user_id` : ID utilisateur pour vérifier le code d'activation

---

#### ✅ 3. Connexion (`POST /api/auth/login/`)

**Réponse (200 OK)** :
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    ...
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Tokens envoyés** :
- ✅ `refresh` : Token JWT de rafraîchissement
- ✅ `access` : Token JWT d'accès

---

#### ✅ 4. Obtenir Token JWT (`POST /api/auth/token/`)

**Requête** :
```json
{
  "username": "john_doe",
  "password": "password123"
}
```

**Réponse (200 OK)** :
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Tokens envoyés** :
- ✅ `refresh` : Token JWT de rafraîchissement
- ✅ `access` : Token JWT d'accès

---

#### ✅ 5. Rafraîchir Token (`POST /api/auth/token/refresh/`)

**Requête** :
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Réponse (200 OK)** :
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."  // Nouveau refresh token (rotation activée)
}
```

**Tokens envoyés** :
- ✅ `access` : Nouveau token JWT d'accès
- ✅ `refresh` : Nouveau token JWT de rafraîchissement (si rotation activée)

**⚠️ IMPORTANT** : Avec `ROTATE_REFRESH_TOKENS=True`, un **nouveau refresh token** est généré à chaque refresh. Le frontend **DOIT** sauvegarder le nouveau refresh token.

---

#### ✅ 6. Connexion Apple (`POST /api/auth/apple/`)

**Réponse (200 OK)** :
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    ...
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Tokens envoyés** :
- ✅ `refresh` : Token JWT de rafraîchissement
- ✅ `access` : Token JWT d'accès

---

### 🔐 Code d'Activation

#### Comment ça fonctionne

1. **Génération** : Lors de l'inscription, un code à 6 chiffres est généré
2. **Stockage** : Le code est stocké dans Redis (cache Django) avec une expiration de 15 minutes
3. **Envoi** : Le code est envoyé par email via Celery (tâche asynchrone)
4. **Vérification** : L'utilisateur envoie le code via `POST /api/auth/activate/`

#### ⚠️ Sécurité

Le code d'activation **N'EST PAS** retourné dans la réponse API pour des raisons de sécurité. Il est uniquement envoyé par email.

#### Endpoint de Vérification

**`POST /api/auth/activate/`**

**Requête** :
```json
{
  "user_id": 1,
  "code": "123456"
}
```

**Réponse (200 OK)** :
```json
{
  "detail": "Compte activé avec succès.",
  "user": {
    "id": 1,
    "est_verifie": true,
    ...
  }
}
```

### 📊 Tableau Récapitulatif

| Endpoint | `access` | `refresh` | Code Activation | `user_id` |
|----------|----------|-----------|-----------------|-----------|
| `POST /api/auth/register/` | ✅ | ✅ | 📧 Email | ✅ |
| `POST /api/utilisateurs/` | ✅ | ✅ | 📧 Email | ✅ |
| `POST /api/auth/login/` | ✅ | ✅ | ❌ | ❌ |
| `POST /api/auth/token/` | ✅ | ✅ | ❌ | ❌ |
| `POST /api/auth/token/refresh/` | ✅ | ✅* | ❌ | ❌ |
| `POST /api/auth/apple/` | ✅ | ✅ | ❌ | ❌ |

*Nouveau refresh token si rotation activée

### ✅ Vérification

#### Tous les tokens sont bien envoyés

- ✅ **Access Token** : Envoyé dans toutes les réponses d'authentification
- ✅ **Refresh Token** : Envoyé dans toutes les réponses d'authentification
- ✅ **Code d'Activation** : Envoyé par email (sécurité)
- ✅ **Rotation des Tokens** : Activée et fonctionnelle

#### Points d'attention pour le frontend

1. **Sauvegarder le nouveau refresh token** après chaque refresh (rotation activée)
2. **Utiliser le nouveau access token** immédiatement après le refresh
3. **Ne pas exposer le code d'activation** dans les logs ou le stockage local
4. **Vérifier le code d'activation** avec `user_id` et `code` via `POST /api/auth/activate/`

---

## 🔧 Dépannage OAuth Google

### 📍 Endpoint

**POST** `/api/auth/google/`

**Body** :
```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6Ij..."
}
```

---

### ✅ Vérifications à Faire

#### 1. Endpoint Disponible

Vérifier que l'endpoint est bien configuré dans les URLs :
- ✅ `/api/auth/google/` doit être dans `apps/utilisateurs/urls.py`

#### 2. Configuration Google OAuth

Vérifier les variables d'environnement :
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

**Où trouver ces valeurs** :
1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Sélectionner votre projet
3. Aller dans "APIs & Services" > "Credentials"
4. Créer ou utiliser un "OAuth 2.0 Client ID"
5. Copier le Client ID et Client Secret

#### 3. Configuration OAuth dans Google Cloud Console

**Authorized JavaScript origins** :
- `http://localhost:19000` (développement)
- `https://votre-domaine.com` (production)

**Authorized redirect URIs** :
- `http://localhost:19000/oauth/callback/google`
- `https://votre-domaine.com/oauth/callback/google`

#### 4. Format du Token

Le frontend doit envoyer un `id_token` (pas un `access_token`).

**Exemple avec Expo** :
```javascript
import * as Google from 'expo-auth-session/providers/google';

const [request, response, promptAsync] = Google.useAuthRequest({
  clientId: 'YOUR_GOOGLE_CLIENT_ID',
  scopes: ['openid', 'profile', 'email'],
});

// Après la connexion
const { id_token } = await promptAsync();
```

#### 5. Vérification du Token

Le backend vérifie le token via :
- `https://oauth2.googleapis.com/tokeninfo?id_token=...`

**Erreurs possibles** :
- Token expiré → Demander un nouveau token
- Token invalide → Vérifier la configuration OAuth
- Audience non autorisée → Vérifier que `GOOGLE_CLIENT_ID` correspond

---

### 🐛 Erreurs Courantes

#### Erreur 404 : Endpoint non trouvé

**Problème** : L'endpoint `/api/auth/google/` n'existe pas.

**Solution** : Vérifier que les URLs sont correctement configurées dans `apps/utilisateurs/urls.py`.

#### Erreur 400 : "id_token requis"

**Problème** : Le frontend n'envoie pas le `id_token`.

**Solution** : Vérifier que le frontend envoie bien `{"id_token": "..."}` dans le body de la requête.

#### Erreur 400 : "Token Google invalide"

**Problème** : Le token n'est pas valide ou a expiré.

**Solutions** :
1. Vérifier que le token n'a pas expiré (généralement valide 1 heure)
2. Vérifier que le token est bien un `id_token` et non un `access_token`
3. Vérifier la configuration OAuth dans Google Cloud Console

#### Erreur 403 : "Audience non autorisée"

**Problème** : Le `GOOGLE_CLIENT_ID` ne correspond pas à celui utilisé pour générer le token.

**Solution** : Vérifier que `GOOGLE_CLIENT_ID` dans les variables d'environnement correspond exactement au Client ID utilisé par le frontend.

#### Erreur 400 : "Email Google manquant"

**Problème** : Le token Google ne contient pas d'email.

**Solution** : Vérifier que les scopes incluent `email` :
```javascript
scopes: ['openid', 'profile', 'email']
```

#### Erreur 500 : "Erreur réseau lors de la vérification"

**Problème** : Le backend ne peut pas contacter l'API Google.

**Solutions** :
1. Vérifier la connexion internet
2. Vérifier que le serveur peut accéder à `https://oauth2.googleapis.com`
3. Vérifier les timeouts (défaut : 10 secondes)

---

### 🔍 Debug

#### Activer les logs

Dans `apps/utilisateurs/views.py`, les erreurs sont loggées avec :
```python
logger.error(f"Erreur Google OAuth: {e}", exc_info=True)
```

Vérifier les logs du serveur pour plus de détails.

#### Tester l'endpoint manuellement

```bash
curl -X POST https://api.example.com/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{"id_token": "YOUR_ID_TOKEN"}'
```

#### Vérifier le token Google

Vous pouvez vérifier manuellement le token :
```bash
curl "https://oauth2.googleapis.com/tokeninfo?id_token=YOUR_ID_TOKEN"
```

---

### 📱 Configuration Frontend (Expo/React Native)

#### 1. Installer les dépendances

```bash
npx expo install expo-auth-session expo-crypto
```

#### 2. Configuration

```javascript
import * as Google from 'expo-auth-session/providers/google';

const [request, response, promptAsync] = Google.useAuthRequest({
  clientId: process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID,
  scopes: ['openid', 'profile', 'email'],
  redirectUri: makeRedirectUri(),
});
```

#### 3. Appel de l'API

```javascript
const handleGoogleLogin = async () => {
  try {
    const result = await promptAsync();
    
    if (result.type === 'success') {
      const { id_token } = result.params;
      
      // Envoyer au backend
      const response = await fetch('https://api.example.com/api/auth/google/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ id_token }),
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Sauvegarder les tokens
        await saveTokens(data.access, data.refresh);
      } else {
        console.error('Erreur:', data.detail);
      }
    }
  } catch (error) {
    console.error('Erreur Google login:', error);
  }
};
```

---

## ⚙️ Configuration JWT

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

---

## 💻 Utilisation Frontend

### Format du Header Authorization

Le header **DOIT** être exactement dans ce format :

```
Authorization: Bearer <token>
```

**Points importants** :
- Le mot "Bearer" (avec majuscule B)
- Un espace après "Bearer"
- Pas de guillemets autour du token
- Pas d'espaces supplémentaires

### Exemple Complet (JavaScript/React)

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

---

## 🐛 Dépannage

### Le code d'activation n'arrive pas par email

1. Vérifier que Celery/Redis est configuré et fonctionne
2. Vérifier les logs Celery pour les erreurs d'envoi
3. Vérifier la configuration email (SMTP, etc.)

### Les tokens ne sont pas retournés

1. Vérifier que `USE_JWT_AUTH=True` dans les settings
2. Vérifier que `rest_framework_simplejwt` est installé
3. Vérifier les logs Django pour les erreurs de génération de tokens

### Le refresh token ne fonctionne pas

1. Vérifier que le nouveau refresh token est sauvegardé après le refresh
2. Vérifier que l'ancien refresh token n'est pas utilisé (blacklist activée)
3. Vérifier que le format du header est correct : `Authorization: Bearer <token>`

---

## ✅ Checklist

### Configuration
- [ ] Endpoint `/api/auth/google/` configuré dans les URLs
- [ ] Variables d'environnement `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET` définies
- [ ] OAuth 2.0 Client ID créé dans Google Cloud Console
- [ ] Authorized JavaScript origins configurés
- [ ] Authorized redirect URIs configurés
- [ ] `USE_JWT_AUTH=True` dans les settings

### Frontend
- [ ] Frontend envoie `id_token` (pas `access_token`)
- [ ] Scopes incluent `email`
- [ ] Le `GOOGLE_CLIENT_ID` correspond entre frontend et backend
- [ ] Le nouveau refresh token est sauvegardé après chaque refresh
- [ ] Le nouveau access token est utilisé immédiatement après le refresh
- [ ] Le format du header est correct : `Authorization: Bearer <token>`

---

## 📚 Ressources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Expo AuthSession Documentation](https://docs.expo.dev/guides/authentication/#google)
- [Google Cloud Console](https://console.cloud.google.com/)
- [Django REST Framework JWT](https://django-rest-framework-simplejwt.readthedocs.io/)

---

*Dernière mise à jour : 2025-01-17*

