# Opérations

## Démarrer en local
```bash
pip install -r comparateur_prix/requirements.txt
# Copier .env.example vers .env et ajuster
python comparateur_prix/manage.py migrate
python comparateur_prix/manage.py runserver
```

## Celery
- Worker:
```bash
celery -A config.celery:app worker -l info
```
- Beat (planification):
```bash
celery -A config.celery:app beat -l info
```
- Broker/Backend: `REDIS_URL` ou `CELERY_BROKER_URL` (voir `.env.example`)

## Import DGCCRF
- Dry-run:
```bash
python comparateur_prix/manage.py import_dgccrf --dry-run --limit 20
```
- Réel:
```bash
python comparateur_prix/manage.py import_dgccrf --limit 200
```
- Export via script:
```bash
python comparateur_prix/scripts/scraper_dgccrf.py --out comparateur_prix/data/dgccrf_export.json --limit 100
```

## Initialisation base PostgreSQL (optionnel)
Si vous utilisez PostgreSQL localement, vous pouvez initialiser via `init_db.sql` (psql requis):
```bash
psql -U postgres -h localhost -p 5432 -f init_db.sql \
  -v DB=compare_easy -v USER=postgres -v PASSWORD='change-me'
```

## Fichiers statiques
- Dev: assets dans `static/` et `templates/`
- Prod: `python manage.py collectstatic` → `staticfiles/`

## Logs
- Config via `config.optimizations.logging.get_logging_config()`.
- Passer `LOG_JSON=true` (si supporté) pour logs JSON.

## Déploiement
- Définir `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`.
- CORS/CSRF: restreindre `CORS_ALLOWED_ORIGINS` et `CSRF_TRUSTED_ORIGINS`.
- Lancer migrations, collectstatic, worker Celery et beat.

## Authentification sociale
Renseigner les variables d’environnement dans `.env` (voir `.env.example`) :
- Google: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Facebook: `FACEBOOK_APP_ID`, `FACEBOOK_APP_SECRET`
- Apple (facultatif): `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, `APPLE_PRIVATE_KEY_PEM`

Endpoints d’intégration via `social_django` (callback): configurez les URLs de redirection chez les fournisseurs avec votre domaine/ports.

## Géocodage des magasins (HERE Maps)
- Configurer dans `.env`:
  - `HERE_API_KEY` (obligatoire)
  - `HERE_GEOCODE_ENDPOINT` (optionnel, défaut: https://geocode.search.hereapi.com/v1/geocode)
  - `HERE_TIMEOUT`, `HERE_CACHE_TTL`, `DEFAULT_COUNTRY_NAME`
- Lancer le géocodage en lot:
```bash
python comparateur_prix/manage.py geocode_magasins --only-missing --limit 500
```
Le provider de géocodage stocké dans `Magasin.geocoding_provider` est désormais `"here"`.
