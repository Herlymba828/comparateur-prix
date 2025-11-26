# Guide API d'Inscription Utilisateur

Ce guide explique comment utiliser l'API d'inscription (`POST /api/utilisateurs/`).

## 📋 Endpoint

```
POST /api/utilisateurs/
```

## ✅ Champs Requis

| Champ | Type | Description | Validation |
|-------|------|-------------|------------|
| `username` | string | Nom d'utilisateur unique | Requis, unique |
| `email` | string | Adresse email | Requis, unique, format email valide |
| `password` | string | Mot de passe | Requis, **minimum 8 caractères** |
| `password_confirmation` | string | Confirmation du mot de passe | Requis, doit correspondre à `password` |

## 📝 Champs Optionnels

| Champ | Type | Description |
|-------|------|-------------|
| `first_name` | string | Prénom |
| `last_name` | string | Nom de famille |
| `type_utilisateur` | string | Type d'utilisateur (`particulier`, `professionnel`, `administrateur`) |
| `telephone` | string | Numéro de téléphone (format international recommandé) |
| `code_postal` | string | Code postal |
| `ville` | string | Ville |
| `date_naissance` | string | Date de naissance (format ISO: `YYYY-MM-DD`) |

---

## 📤 Exemple de Requête Valide

### Exemple 1 : Inscription Minimale

```json
{
  "username": "john_doe",
  "email": "john.doe@example.com",
  "password": "motdepasse123",
  "password_confirmation": "motdepasse123"
}
```

### Exemple 2 : Inscription Complète

```json
{
  "username": "jane_smith",
  "email": "jane.smith@example.com",
  "password": "SecurePass123!",
  "password_confirmation": "SecurePass123!",
  "first_name": "Jane",
  "last_name": "Smith",
  "type_utilisateur": "particulier",
  "telephone": "+33612345678",
  "code_postal": "75001",
  "ville": "Paris",
  "date_naissance": "1990-01-15"
}
```

### Exemple 3 : Via cURL

```bash
curl -X POST https://comparo.up.railway.app/api/utilisateurs/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_user",
    "email": "test@example.com",
    "password": "password123",
    "password_confirmation": "password123"
  }'
```

### Exemple 4 : Via JavaScript (fetch)

```javascript
const response = await fetch('https://comparo.up.railway.app/api/utilisateurs/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    username: 'test_user',
    email: 'test@example.com',
    password: 'password123',
    password_confirmation: 'password123'
  })
});

const data = await response.json();
```

---

## ❌ Erreurs Courantes

### Erreur 1 : Mot de passe trop court

**Requête :**
```json
{
  "username": "user",
  "email": "user@example.com",
  "password": "123456",
  "password_confirmation": "123456"
}
```

**Réponse (400 Bad Request) :**
```json
{
  "password": ["Assurez-vous que ce champ comporte au moins 8 caractères."]
}
```

**Solution :** Utiliser un mot de passe d'au moins 8 caractères.

---

### Erreur 2 : `password_confirmation` manquant

**Requête :**
```json
{
  "username": "user",
  "email": "user@example.com",
  "password": "password123"
}
```

**Réponse (400 Bad Request) :**
```json
{
  "password_confirmation": ["Ce champ est obligatoire."]
}
```

**Solution :** Ajouter le champ `password_confirmation` avec la même valeur que `password`.

---

### Erreur 3 : `username` manquant

**Requête :**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "password_confirmation": "password123"
}
```

**Réponse (400 Bad Request) :**
```json
{
  "username": ["Ce champ est obligatoire."]
}
```

**Solution :** Ajouter le champ `username`.

---

### Erreur 4 : Mots de passe ne correspondent pas

**Requête :**
```json
{
  "username": "user",
  "email": "user@example.com",
  "password": "password123",
  "password_confirmation": "different123"
}
```

**Réponse (400 Bad Request) :**
```json
{
  "password_confirmation": ["Les mots de passe ne correspondent pas."]
}
```

**Solution :** S'assurer que `password` et `password_confirmation` ont exactement la même valeur.

---

### Erreur 5 : Email déjà utilisé

**Requête :**
```json
{
  "username": "new_user",
  "email": "existing@example.com",
  "password": "password123",
  "password_confirmation": "password123"
}
```

**Réponse (400 Bad Request) :**
```json
{
  "email": ["Un utilisateur avec cet email existe déjà."]
}
```

**Solution :** Utiliser un email différent ou se connecter avec le compte existant.

---

### Erreur 6 : Username déjà utilisé

**Requête :**
```json
{
  "username": "existing_user",
  "email": "new@example.com",
  "password": "password123",
  "password_confirmation": "password123"
}
```

**Réponse (400 Bad Request) :**
```json
{
  "username": ["Un utilisateur avec ce nom d'utilisateur existe déjà."]
}
```

**Solution :** Utiliser un nom d'utilisateur différent.

---

## ✅ Réponse de Succès (201 Created)

```json
{
  "user": {
    "id": 1,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john.doe@example.com",
    "first_name": "",
    "last_name": "",
    "type_utilisateur": "particulier",
    "telephone": "",
    "date_naissance": null,
    "code_postal": "",
    "ville": "",
    "date_creation": "2025-11-26T23:00:00Z",
    "derniere_connexion": null,
    "est_verifie": false,
    "points_fidelite": 0,
    "niveau_fidelite": 0,
    "total_achats": "0.00",
    "nombre_commandes": 0
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "activation_pending": true
}
```

### Champs de la Réponse

- **`user`** : Objet utilisateur créé
- **`refresh`** : Token JWT de rafraîchissement (si JWT activé)
- **`access`** : Token JWT d'accès (si JWT activé)
- **`activation_pending`** : `true` si l'email d'activation doit être vérifié

---

## 📱 Format pour Applications Mobiles

### React Native / Expo

```javascript
import axios from 'axios';

const registerUser = async (userData) => {
  try {
    const response = await axios.post(
      'https://comparo.up.railway.app/api/utilisateurs/',
      {
        username: userData.username,
        email: userData.email,
        password: userData.password,
        password_confirmation: userData.password, // Même valeur que password
        first_name: userData.firstName,
        last_name: userData.lastName,
        // ... autres champs optionnels
      }
    );
    
    // Sauvegarder les tokens JWT
    await AsyncStorage.setItem('access_token', response.data.access);
    await AsyncStorage.setItem('refresh_token', response.data.refresh);
    
    return response.data;
  } catch (error) {
    if (error.response) {
      // Erreurs de validation
      console.error('Erreurs:', error.response.data);
    } else {
      console.error('Erreur réseau:', error.message);
    }
    throw error;
  }
};
```

### Flutter / Dart

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

Future<Map<String, dynamic>> registerUser({
  required String username,
  required String email,
  required String password,
  String? firstName,
  String? lastName,
}) async {
  final response = await http.post(
    Uri.parse('https://comparo.up.railway.app/api/utilisateurs/'),
    headers: {'Content-Type': 'application/json'},
    body: jsonEncode({
      'username': username,
      'email': email,
      'password': password,
      'password_confirmation': password, // Même valeur que password
      if (firstName != null) 'first_name': firstName,
      if (lastName != null) 'last_name': lastName,
    }),
  );

  if (response.statusCode == 201) {
    return jsonDecode(response.body);
  } else {
    throw Exception('Erreur d\'inscription: ${response.body}');
  }
}
```

---

## 🔐 Bonnes Pratiques

1. **Mot de passe fort** : Utilisez au moins 8 caractères avec majuscules, minuscules, chiffres et caractères spéciaux
2. **Validation côté client** : Validez les champs avant d'envoyer la requête
3. **Gestion des erreurs** : Affichez les messages d'erreur de manière claire à l'utilisateur
4. **Sécurité** : Ne stockez jamais les mots de passe en clair côté client
5. **Activation email** : Vérifiez l'email d'activation après l'inscription

---

## 🔗 Endpoints Liés

- **Connexion** : `POST /api/utilisateurs/connexion/`
- **Activation compte** : `GET /api/utilisateurs/activer/<uidb64>/<token>/`
- **Réinitialisation mot de passe** : `POST /api/utilisateurs/reset-password/`

---

## 📚 Ressources

- [Documentation API complète](./ENDPOINTS_API.md)
- [Guide de déploiement Railway](./DEPLOIEMENT_RAILWAY.md)

