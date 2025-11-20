# Tests de l'endpoint POST /api/utilisateurs/

## Corrections apportées

### 1. Serializer (`InscriptionSerializer`)
- ✅ Validation améliorée du username (unicité)
- ✅ Validation améliorée de l'email (unicité, normalisation)
- ✅ Normalisation du numéro de téléphone
- ✅ Gestion d'erreurs plus robuste
- ✅ Hashage automatique du mot de passe

### 2. ViewSet (`UtilisateurViewSet`)
- ✅ Méthode `create` personnalisée avec gestion d'erreurs
- ✅ Transaction atomique pour garantir la cohérence
- ✅ Vérification et création manuelle du profil si nécessaire
- ✅ Support JWT automatique
- ✅ Queryset optimisé pour éviter les erreurs lors de la création

## Tests à effectuer

### 1. Test via cURL

#### Test de création d'utilisateur valide
```bash
curl -X POST http://localhost:8000/api/utilisateurs/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser123",
    "email": "test@example.com",
    "password": "MotDePasse123!",
    "password_confirmation": "MotDePasse123!",
    "first_name": "Test",
    "last_name": "User",
    "type_utilisateur": "particulier",
    "telephone": "0612345678",
    "code_postal": "75001",
    "ville": "Paris"
  }'
```

#### Test avec date de naissance
```bash
curl -X POST http://localhost:8000/api/utilisateurs/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser456",
    "email": "test2@example.com",
    "password": "SecurePass123!",
    "password_confirmation": "SecurePass123!",
    "first_name": "Jean",
    "last_name": "Dupont",
    "type_utilisateur": "particulier",
    "telephone": "+33612345678",
    "code_postal": "69001",
    "ville": "Lyon",
    "date_naissance": "1990-01-15"
  }'
```

### 2. Test via Postman

1. **Méthode**: POST
2. **URL**: `http://localhost:8000/api/utilisateurs/`
3. **Headers**:
   - `Content-Type: application/json`
4. **Body** (raw JSON):
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "Password123!",
  "password_confirmation": "Password123!",
  "first_name": "New",
  "last_name": "User",
  "type_utilisateur": "particulier",
  "telephone": "0612345678",
  "code_postal": "33000",
  "ville": "Bordeaux"
}
```

### 3. Test via navigateur (avec extension REST Client)

Si vous utilisez une extension comme "REST Client" dans VS Code ou un plugin navigateur :

```
POST http://localhost:8000/api/utilisateurs/
Content-Type: application/json

{
  "username": "browseruser",
  "email": "browser@example.com",
  "password": "Test1234!",
  "password_confirmation": "Test1234!",
  "first_name": "Browser",
  "last_name": "Test",
  "type_utilisateur": "particulier"
}
```

### 4. Test depuis React Native

```javascript
const createUser = async (userData) => {
  try {
    const response = await fetch('http://votre-api.com/api/utilisateurs/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: userData.username,
        email: userData.email,
        password: userData.password,
        password_confirmation: userData.password,
        first_name: userData.firstName,
        last_name: userData.lastName,
        type_utilisateur: 'particulier',
        telephone: userData.phone,
        code_postal: userData.postalCode,
        ville: userData.city,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Erreur lors de la création du compte');
    }

    const data = await response.json();
    console.log('Utilisateur créé:', data);
    return data;
  } catch (error) {
    console.error('Erreur:', error);
    throw error;
  }
};
```

## Tests d'erreurs à effectuer

### 1. Test email déjà existant
```bash
curl -X POST http://localhost:8000/api/utilisateurs/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser2",
    "email": "test@example.com",
    "password": "Password123!",
    "password_confirmation": "Password123!"
  }'
```
**Résultat attendu**: Erreur 400 avec message "Un utilisateur avec cet email existe déjà."

### 2. Test username déjà existant
```bash
curl -X POST http://localhost:8000/api/utilisateurs/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser123",
    "email": "different@example.com",
    "password": "Password123!",
    "password_confirmation": "Password123!"
  }'
```
**Résultat attendu**: Erreur 400 avec message "Un utilisateur avec ce nom d'utilisateur existe déjà."

### 3. Test mots de passe différents
```bash
curl -X POST http://localhost:8000/api/utilisateurs/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser3",
    "email": "test3@example.com",
    "password": "Password123!",
    "password_confirmation": "DifferentPass123!"
  }'
```
**Résultat attendu**: Erreur 400 avec message "Les mots de passe ne correspondent pas."

### 4. Test mot de passe trop court
```bash
curl -X POST http://localhost:8000/api/utilisateurs/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser4",
    "email": "test4@example.com",
    "password": "Short1!",
    "password_confirmation": "Short1!"
  }'
```
**Résultat attendu**: Erreur 400 avec message de validation sur la longueur minimale.

## Réponse attendue (succès)

```json
{
  "id": 1,
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "username": "testuser123",
  "email": "test@example.com",
  "first_name": "Test",
  "last_name": "User",
  "type_utilisateur": "particulier",
  "telephone": "+33612345678",
  "code_postal": "75001",
  "ville": "Paris",
  "date_creation": "2024-01-15T10:30:00Z",
  "est_verifie": false,
  "activation_pending": true,
  "profil": {
    "avatar": null,
    "bio": "",
    "notifications_actives": true,
    "newsletter_abonnement": false
  },
  "points_fidelite": 0,
  "niveau_fidelite": 1,
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Vérifications à faire

1. ✅ L'utilisateur est créé dans la base de données
2. ✅ Le profil utilisateur est créé automatiquement (par signal)
3. ✅ L'abonnement par défaut est créé (par signal)
4. ✅ Le mot de passe est hashé (pas en clair dans la DB)
5. ✅ La réponse JSON est valide et contient toutes les informations
6. ✅ Les tokens JWT sont générés si activé
7. ✅ Les erreurs retournent du JSON (pas du HTML)

## Notes importantes

- L'endpoint est accessible sans authentification (AllowAny pour l'action 'create')
- Le CSRF est désactivé pour cet endpoint (nécessaire pour React Native)
- Les signaux Django créent automatiquement le profil et l'abonnement
- Si le profil n'est pas créé par le signal, il est créé manuellement dans la méthode `create`

