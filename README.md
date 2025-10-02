# Comparateur de Prix (Gabon)

## Lancer en local

1. Créez un fichier `.env` à la racine en partant de `.env.example`.
2. Installez les dépendances: `pip install -r requirements.txt`.
3. Appliquez les migrations: `python manage.py migrate`.
4. Créez un superuser: `python manage.py createsuperuser` (optionnel).
5. Lancez le serveur: `python manage.py runserver`.

## Endpoints de test

- Admin: `/admin/`
- Health: `/api/health/`
- Documentation API: `/api/docs/` (Swagger) | `/api/schema/` (OpenAPI)

## Documentation des fonctionnalités

Consultez `docs/FONCTIONNALITES.md` pour la liste complète des fonctionnalités et endpoints clés (Utilisateurs, Produits, Magasins, Analyses, Recommandations, Recherche, Sécurité).

## PostgreSQL

Configurez vos variables d'environnement dans `.env`.

## Unpoly / Front

Vous pouvez intégrer Unpoly en consommant les endpoints `/api/*` et en rendant des fragments dans `templates/`.
