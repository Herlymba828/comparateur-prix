# Fonctionnalités du projet

## Vue d’ensemble

- Authentification et gestion des utilisateurs (inscription, connexion, activation email, reset MDP, 2FA, sessions, rôles)
- Produits, catégories, marques, unités de mesure (CRUD + stats)
- Gestion des prix par magasin, historique, alertes, suggestions et comparaisons
- Homologations et prix homologués (DGCCRF/EDIG)
- Magasins (listing/filtrage)
- Analyses et recommandations (endpoints exposés)
- Recherche (full-text/suggest, si Elasticsearch actif)
- Documentation OpenAPI (drf-spectacular)

## Utilisateurs

- Inscription: `POST /api/utilisateurs/api/auth/inscription/`
- Connexion: `POST /api/utilisateurs/api/auth/connexion/`
- Profil courant: `GET /api/utilisateurs/api/utilisateurs/moi/`
- Changer mot de passe: `POST /api/utilisateurs/api/auth/changer-mot-de-passe/`
- Activation: `GET /api/utilisateurs/api/auth/activation/confirmer/<token>/`
- Renvoyer activation: `POST /api/utilisateurs/api/utilisateurs/renvoyer_activation/`
- Reset MDP (demander): `POST /api/utilisateurs/api/auth/mot-de-passe/demander/`
- Reset MDP (confirmer): `POST /api/utilisateurs/api/auth/mot-de-passe/confirmer/<token>/`
- 2FA TOTP: `POST /api/utilisateurs/api/utilisateurs/twofa_setup/`, `twofa_verify/`, `twofa_disable/`
- Rôles: `GET /api/utilisateurs/api/utilisateurs/roles/`, `POST assign_role/`, `POST revoke_role/` (admin/modérateur)
- Sessions: `GET /api/utilisateurs/api/auth/sessions/`, `POST /api/utilisateurs/api/auth/sessions/revoke/`, `POST /api/utilisateurs/api/auth/logout_all/`
- Profils: `api/utilisateurs/api/profils/` (restreint propriétaire)
- Abonnements: `api/utilisateurs/api/abonnements/` (lecture)
- Fidélité: `GET /api/utilisateurs/api/utilisateurs/moi/statistiques-fidelite/`, `GET /api/utilisateurs/api/utilisateurs/moi/historique-remises/`, `POST /api/utilisateurs/api/utilisateurs/moi/appliquer-remise/`
- Social login: `POST /api/utilisateurs/api/auth/google/`, `facebook/`, `apple/`

## Produits

- Produits: `api/produits/api/produits/` (listing/détail/CRUD selon permissions)
- Catégories: `api/produits/api/categories/`
- Marques: `api/produits/api/marques/`
- Unités de mesure: `api/produits/api/unites-mesure/`
- Prix (ViewSet nested): `api/produits/api/prix/` (gestion des prix par magasin)
- Historique de prix: via `PrixDetailSerializer` (champ `historique_recent`)
- Alertes prix: `api/produits/api/alertes-prix/`
- Suggestions prix: `api/produits/api/suggestions-prix/`
- Comparaisons prix: `api/produits/api/comparaisons-prix/`
- Statistiques produits/prix: `api/produits/api/statistiques-produits/`, `api/produits/api/statistiques-prix/`
- Homologations: `api/produits/api/homologations/` + `api/produits/api/homologations-stats/`

## Magasins

- Magasins: `api/magasins/api/magasins/`

## Analyses

- Analyses: `api/analyses/` (voir `apps/analyses/urls.py` pour le détail)

## Recommandations

- Recommandations: `api/recommandations/` (voir `apps/recommandations/urls.py`)

## API publique/générique

- Recherche produits (si activé): `api/produits/api/produits/es_search/`, `es_suggest/`
- Autocomplete: voir `apps/api/urls.py`

## Documentation API

- OpenAPI schema: `/api/schema/`
- Swagger UI: `/api/docs/`

## Sécurité et configuration

- `SECURE_SSL_REDIRECT` activé par défaut (surcharge via env: `SECURE_SSL_REDIRECT`)
- Définir `DJANGO_SECRET_KEY` ou `SECRET_KEY` via variables d’environnement
- Activer JWT en définissant `USE_JWT_AUTH=True` si souhaité
