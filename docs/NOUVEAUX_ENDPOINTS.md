# 📋 Liste des Nouveaux Endpoints API

## 🔐 Endpoints Requérant une Authentification (JWT)

### 1. **Likes de Produits**

#### Liker un produit
```
POST /api/produits/produits/{id}/like/
```
**Authentification** : ✅ Requis (JWT)  
**Description** : Ajoute un produit aux favoris de l'utilisateur connecté  
**Réponse 201** :
```json
{
  "message": "Produit ajouté aux favoris",
  "liked": true,
  "produit_id": 123
}
```
**Réponse 200** (déjà liké) :
```json
{
  "message": "Produit déjà dans vos favoris",
  "liked": true,
  "produit_id": 123
}
```
**Erreur 401** (non authentifié) :
```json
{
  "detail": "Authentification requise. Veuillez fournir un token JWT valide dans le header Authorization.",
  "code": "authentication_required",
  "hint": "Format attendu: Authorization: Bearer <votre_token>"
}
```

#### Unliker un produit
```
DELETE /api/produits/produits/{id}/like/
```
**Authentification** : ✅ Requis (JWT)  
**Description** : Retire un produit des favoris de l'utilisateur connecté  
**Réponse 200** :
```json
{
  "message": "Produit retiré des favoris",
  "liked": false,
  "produit_id": 123
}
```

#### Liste des produits likés
```
GET /api/produits/produits/mes_likes/
```
**Authentification** : ✅ Requis (JWT)  
**Description** : Retourne tous les produits likés par l'utilisateur connecté  
**Pagination** : ✅ Oui  
**Réponse** :
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "nom": "Produit 1",
      "code_barre": "1234567890123",
      "prix_moyen_agg": 1500.00,
      ...
    }
  ]
}
```

### 2. **Recommandations Personnalisées**

#### Produits likés (pour_moi)
```
GET /api/recommandations/pour_moi/
```
**Authentification** : ✅ Requis (JWT)  
**Description** : Retourne tous les produits likés par l'utilisateur connecté  
**Query params** :
- `n_recommandations` (optionnel, défaut: 10) : Nombre de recommandations

**Réponse** :
```json
{
  "produits_likes": [
    {
      "id": 1,
      "nom": "Produit liké",
      "code_barre": "1234567890123",
      "prix_moyen_agg": 1500.00,
      ...
    }
  ],
  "total": 5,
  "message": "Produits likés par l'utilisateur"
}
```

**Alias disponibles** :
- `GET /api/recommandations/reco/pour-vous/`
- `GET /api/reco/pour-vous/` (legacy)
- `GET /api/recommandations/recommandations/utilisateur/` (legacy)

---

## 🌐 Endpoints Publics (Sans Authentification)

### 3. **Recommandations Publiques**

#### Produits populaires
```
GET /api/recommandations/populaires/
```
**Authentification** : ❌ Public  
**Cache** : ✅ 15 minutes  
**Query params** :
- `n_recommandations` (optionnel, défaut: 10)

**Alias disponibles** :
- `GET /api/recommandations/reco/tendances/`
- `GET /api/reco/tendances/` (legacy)

#### Recommandations par produit
```
GET /api/recommandations/pour_produit/?produit_id={id}
```
**Authentification** : ❌ Public  
**Query params** :
- `produit_id` (requis) : ID du produit
- `n_recommandations` (optionnel, défaut: 10)

**Version avec ID dans l'URL** :
```
GET /api/reco/produits/{produit_id}/similaires/
```

### 4. **Liste des Produits**

#### Tous les produits (actifs + inactifs)
```
GET /api/produits/produits/tous/
```
**Authentification** : ❌ Public (lecture)  
**Pagination** : ✅ Oui  
**Description** : Retourne TOUS les produits de la base (actifs et inactifs)

#### Produits défiscalisés
```
GET /api/produits/produits/defiscalises/
```
**Authentification** : ❌ Public (lecture)  
**Pagination** : ✅ Oui  
**Description** : Retourne tous les produits défiscalisés (catégories: Alimentaire, Médicament, Équipement médical)

#### Produits homologués
```
GET /api/produits/produits/homologues/
```
**Authentification** : ❌ Public (lecture)  
**Pagination** : ✅ Oui  
**Description** : Retourne tous les produits homologués (correspondance avec HomologationProduit)

### 5. **Filtres de Produits**

#### Filtres disponibles sur `/api/produits/produits/`
```
GET /api/produits/produits/?est_defiscalise=true
GET /api/produits/produits/?est_homologue=true
GET /api/produits/produits/?prix_min=1000&prix_max=5000
GET /api/produits/produits/?categorie={id}&marque={id}
GET /api/produits/produits/?search=nom_produit
GET /api/produits/produits/?ordering=prix_moyen_agg
```

---

## 🔧 Endpoints Corrigés/Améliorés

### 6. **Comparaison de Prix**

#### Comparaison par produit (corrigé)
```
GET /api/produits/prix/comparaison_produit/?produit={id}
GET /api/produits/prix/comparaison_produit/?produit_id={id}
```
**Authentification** : ❌ Public (lecture)  
**Description** : Compare les prix d'un produit entre différents magasins  
**Note** : Accepte maintenant `produit` ou `produit_id` comme paramètre

**Réponse** :
```json
{
  "produit": {
    "id": 32,
    "nom": "Produit",
    "image": "http://..."
  },
  "statistiques": {
    "prix_min": 1000.00,
    "prix_max": 1500.00,
    "prix_moyen": 1250.00,
    "nombre_magasins": 5,
    "promotions": 2
  },
  "prix_par_magasin": [...]
}
```

---

## 📊 Résumé des Endpoints par Catégorie

### 🔐 Authentification Requise
1. `POST /api/produits/produits/{id}/like/` - Liker un produit
2. `DELETE /api/produits/produits/{id}/like/` - Unliker un produit
3. `GET /api/produits/produits/mes_likes/` - Mes produits likés
4. `GET /api/recommandations/pour_moi/` - Produits likés (recommandations)

### 🌐 Accès Public
1. `GET /api/recommandations/populaires/` - Produits populaires
2. `GET /api/recommandations/pour_produit/` - Recommandations par produit
3. `GET /api/produits/produits/tous/` - Tous les produits
4. `GET /api/produits/produits/defiscalises/` - Produits défiscalisés
5. `GET /api/produits/produits/homologues/` - Produits homologués
6. `GET /api/produits/prix/comparaison_produit/` - Comparaison de prix

---

## 🔑 Authentification

Tous les endpoints nécessitant une authentification utilisent **JWT (JSON Web Token)**.

### Format du Header
```
Authorization: Bearer <votre_token_jwt>
```

### Obtenir un Token
```
POST /api/auth/token/
Body: {
  "username": "votre_username",
  "password": "votre_password"
}
```

### Rafraîchir un Token
```
POST /api/auth/token/refresh/
Body: {
  "refresh": "<votre_refresh_token>"
}
```

---

## ⚠️ Codes d'Erreur

### 401 Unauthorized
- **Cause** : Token JWT manquant, invalide ou expiré
- **Message** : "Authentification requise. Veuillez fournir un token JWT valide dans le header Authorization."

### 403 Forbidden
- **Cause** : Permissions insuffisantes
- **Message** : "Vous n'avez pas la permission d'effectuer cette action."

### 400 Bad Request
- **Cause** : Paramètres manquants ou invalides
- **Message** : Détails de l'erreur de validation

### 404 Not Found
- **Cause** : Ressource non trouvée
- **Message** : "Ressource non trouvée"

---

## 📝 Notes Importantes

1. **Sécurité** : Tous les endpoints de likes nécessitent une authentification JWT valide
2. **Logs** : Toutes les tentatives d'accès non authentifiées sont loggées
3. **Pagination** : La plupart des endpoints de liste supportent la pagination
4. **Cache** : Les endpoints publics de recommandations sont mis en cache (15 minutes)
5. **Unification DGCCRF** : Les produits scrappés du site DGCCRF sont automatiquement unifiés dans la table Produit principale

