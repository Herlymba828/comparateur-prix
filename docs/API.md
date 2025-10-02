# API

Base: `/api/`

## Utilitaires
- `GET /api/health/` → `{ status: "ok" }`
- `GET /api/search/produits?q=&categorie=&marque=&page=&page_size=`
  - Résultat: `[{ id, nom, marque, categorie_id, categorie_nom, min_prix, devise }]`
- `GET /api/search/autocomplete?q=`
  - Résultat: `{ results: [{ id, label }] }`
- `GET /api/homologations-stats/` → stats synthétiques

## Produits
- Routage: `apps/produits/urls.py` sous `/api/produits/`
- Endpoints CRUD (DRF ViewSets) selon implémentation.

## Magasins
- Routage: `apps/magasins/urls.py` sous `/api/magasins/`
- Endpoints CRUD (DRF ViewSets) selon implémentation.

## Prix
- Routage: `apps/prix/urls.py` sous `/api/prix/`
- Principaux ViewSets:
  - `GET /api/prix/prix/` liste des prix
  - `GET /api/prix/alertes-prix/` alertes
  - `GET /api/prix/comparaisons-prix/` comparaisons
  - `GET /api/prix/statistiques-prix/` stats prix
  - `GET /api/prix/homologations-stats/` stats homologations

## Authentification
- JWT (optionnel):
  - `POST /api/auth/token/` → access/refresh
  - `POST /api/auth/token/refresh/`
- Social login (Google/Facebook; Apple si clés configurées): `/oauth/`

## Documentation OpenAPI
- Schéma: `GET /api/schema/`
- Swagger UI: `GET /api/docs/`
