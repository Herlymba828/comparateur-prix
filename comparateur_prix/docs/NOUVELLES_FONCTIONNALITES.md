# Nouvelles fonctionnalités: Guide d'utilisation et d'initialisation

Ce document explique comment configurer et utiliser les nouvelles fonctionnalités livrées récemment.

- Authentification avec vérification email et reset mot de passe
- 2FA (TOTP) avec QR code
- Gestion des sessions (liste/révocation/logout global + blacklist JWT)
- Rôles et permissions (admin, modérateur, premium)
- Connexion sociale: Google, Facebook, Apple
- Recherche Elasticsearch (indexation produits, recherche full-text et suggestions)

Toutes les routes ci-dessous sont préfixées par `apps/.../urls.py` (regardez votre `config/urls.py` pour le préfixe global), et utilisent par défaut la racine `/api/` déjà présente dans le projet.

---

## 1) Variables d'environnement (.env)

Ajoutez/complétez ces variables dans `.env` à la racine du projet `comparateur_prix/`:

```
# Front/Back
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000

# Social Auth
GOOGLE_CLIENT_ID=
FACEBOOK_APP_ID=
FACEBOOK_APP_SECRET=
APPLE_CLIENT_ID=

# Email (console en dev)
DEFAULT_FROM_EMAIL=noreply@example.com
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Redis / Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_SCHEME=http
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_VERIFY_CERTS=false
ELASTICSEARCH_INDEX_PRODUCTS=produits
ELASTICSEARCH_INDEX_SUGGEST=produits_suggest
```

---

## 2) Authentification: vérification email et reset mot de passe

Endpoints (dans `apps/utilisateurs/urls.py`):

- Inscription: `POST /api/auth/inscription/`
- Connexion: `POST /api/auth/connexion/`
- Changer mot de passe (auth requis): `POST /api/auth/changer-mot-de-passe/`
- Activer compte (lien email): `GET /api/auth/activation/confirmer/<token>/`
- Renvoyer email d'activation (auth requis): `POST /api/utilisateurs/renvoyer_activation/`
- Demander reset MDP: `POST /api/auth/mot-de-passe/demander/` `{ "email": "..." }`
- Confirmer reset MDP: `POST /api/auth/mot-de-passe/confirmer/<token>/` `{ "nouveau_mot_de_passe": "...", "confirmation_mot_de_passe":"..." }`

Notes:
- Le lien d'activation est construit depuis `FRONTEND_URL` s'il est présent, sinon un fallback vers l'endpoint API est utilisé (voir `apps/utilisateurs/utils.py`).
- En dev, les emails s'affichent en console via `EMAIL_BACKEND`.

---

## 3) 2FA TOTP (Google Authenticator, etc.)

Endpoints (auth requis):
- `POST /api/utilisateurs/twofa_setup/` → retourne `otpauth_url` et `qrcode_png_base64`
- `POST /api/utilisateurs/twofa_verify/` `{ "token": "123456" }` → confirme l'appareil
- `POST /api/utilisateurs/twofa_disable/` → supprime tous les appareils TOTP

Dépendances: `django-otp`, `qrcode`, `Pillow` (déjà ajoutées dans `requirements.txt`).

---

## 4) Gestion des sessions et JWT blacklist

Endpoints:
- `GET /api/auth/sessions/` (auth) → liste les sessions actives de l'utilisateur courant
- `POST /api/auth/sessions/revoke/` (auth) → `{ "session_key": "..." }` supprime une session
- `POST /api/auth/logout_all/` (auth) → supprime toutes les sessions et blackliste les refresh tokens (si SimpleJWT activé)

Pré-requis: `USE_JWT_AUTH=True` dans `.env` (si vous utilisez JWT).

---

## 5) Rôles et permissions

- Groupes: `admin`, `moderateur`, `premium`
- Commande d'initialisation (idempotente):

```
python manage.py init_roles
python manage.py init_roles --with-perms  # attache un set minimal de permissions Django
```

Endpoints (réservés admin/modérateur):
- `GET /api/utilisateurs/roles/` → liste des utilisateurs par rôle
- `POST /api/utilisateurs/assign_role/` `{ "user_id": 1, "role": "moderateur" }`
- `POST /api/utilisateurs/revoke_role/` `{ "user_id": 1, "role": "moderateur" }`

Permissions DRF: voir `apps/utilisateurs/permissions.py` (`IsAdminOrModerator`, `IsPremium`).

---

## 6) Connexion sociale: Google, Facebook, Apple

Endpoints:
- Google: `POST /api/auth/google/` `{ "id_token": "..." }`
- Facebook: `POST /api/auth/facebook/` `{ "access_token": "..." }`
- Apple: `POST /api/auth/apple/` `{ "id_token": "..." }`

Comportement:
- Vérifie les tokens côté fournisseur (Google tokeninfo, Facebook Graph API, Apple JWKS + `APPLE_CLIENT_ID`).
- Upsert utilisateur (active + `est_verifie=True`) et retourne les tokens JWT si SimpleJWT est actif.

---

## 7) Recherche Elasticsearch

Dépendance: `elasticsearch==8.12.1` (ajoutée dans `requirements.txt`).

Initialisation:

```
pip install -r requirements.txt
# Lancer Elasticsearch localement (http://localhost:9200)
python manage.py es_init --recreate --reindex
```

Fonctionnement:
- Index produit géré dans `apps/produits/search.py`
- Indexation automatique via signaux (`apps/produits/signals.py`) sur `post_save` / `post_delete`
- Endpoints:
  - `GET /api/produits/es_search/?q=iphone&size=20&offset=0` → full-text
  - `GET /api/produits/es_suggest/?q=iph&size=5` → suggestions (completion)

---

## 8) Exemples `curl`

Inscription:
```
curl -X POST http://localhost:8000/api/utilisateurs/api/auth/inscription/ \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com","password":"Passw0rd!","password_confirmation":"Passw0rd!"}'
```

Demande reset MDP:
```
curl -X POST http://localhost:8000/api/utilisateurs/api/auth/mot-de-passe/demander/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com"}'
```

2FA Setup (avec auth JWT):
```
curl -X POST http://localhost:8000/api/utilisateurs/api/utilisateurs/twofa_setup/ \
  -H 'Authorization: Bearer <ACCESS_TOKEN>'
```

Recherche ES:
```
curl 'http://localhost:8000/api/produits/api/produits/es_search/?q=iphone&size=10&offset=0'
```

---

## 9) Notes et dépannage

- Emails: en dev, utilisez `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`.
- Si vous utilisez un front séparé, définissez `FRONTEND_URL` pour que les liens d'activation/reset pointent vers votre application.
- Pour les connexions sociales, renseignez `GOOGLE_CLIENT_ID`, `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`, `APPLE_CLIENT_ID`.
- Assurez-vous que Elasticsearch est lancé avant `es_init`.
- Les signaux indexent automatiquement les produits actifs, mais vous pouvez relancer un index complet via `es_init --reindex`.

---

## 10) Roadmap (prochaines fonctionnalités suggérées)

- Alertes de prix et notifications (email/Celery) sur seuils personnalisés
- OCR/scan code-barres pour création rapide de produits (API + UI)
- Recherche avancée/filtrée intégrée à Elasticsearch (facettes, filtres multi-champs, tri)
- Tableau de bord Analytics (agrégations, top catégories/marques, KPIs)
- Recommandations ML (collaboratif + contenu) exposées via API
- Caching Redis et rate-limiting DRF (throttling) pour endpoints sensibles
- CI/CD (tests + lint) et documentation d’API (drf-spectacular UI)
