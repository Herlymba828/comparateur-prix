# Architecture

## Aperçu
Application Django modulaire avec plusieurs apps:
- `apps.utilisateurs`: modèle utilisateur personnalisé, profils, fidélité.
- `apps.produits`: produits, catégories, marques, unités.
- `apps.magasins`: régions, villes, magasins.
- `apps.prix`: prix par magasin/produit, historiques, alertes, homologations.
- `apps.analyses`: graph analytics (NetworkX, Louvain).
- `apps.api`: endpoints utilitaires (health, search, autocomplete).

Fichiers clés:
- `config/settings.py`: configuration (DB, DRF, CORS, Celery, cache, sécurité).
- `config/urls.py`: routage global + docs OpenAPI.
- `config/celery.py`: planification des tâches.
- `templates/` et `static/`: UI statique légère pour tests/démo.

## Flux de données
- Scraping DGCCRF via `scripts/scraper_dgccrf.py`.
- Import en base via `apps/prix/management/commands/import_dgccrf.py` -> `HomologationProduit`/`PrixHomologue`.
- Prix courants en `apps.prix.models.Prix`, exposés via ViewSets (`apps/prix/urls.py`).
- Recherche produits avec annotation du prix min côté `apps/api/views.py`.

## Schéma haut-niveau
- Produit(1) — Prix(*) — Magasin(1)
- Produit(1) — Avis(*), Caractéristiques(*), HistoriquePrixProduit(*)
- Magasin(1) — Ville(1) — Région(1)
- HomologationProduit(1) — PrixHomologue(*)

## Analyses/Graphes
- Commande `analyser_graphes` crée des snapshots magasin–magasin.
- Tâche périodique Celery pour génération automatique.
