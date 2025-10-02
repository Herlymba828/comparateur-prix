# Installation

## Prérequis
- Python 3.11+
- PostgreSQL 13+
- Redis 6+ (pour Celery et cache)
- Opc.: ElasticSearch si la recherche avancée est activée

## Étapes
1. Cloner le dépôt.
2. Créer et activer un venv Python.
3. Installer les dépendances:
   ```bash
   pip install -r comparateur_prix/requirements.txt
   ```
4. Configurer les variables d’environnement: copier `comparateur_prix/.env.example` en `.env` et compléter les valeurs (ne pas commiter `.env`).
5. Créer la base PostgreSQL et l’utilisateur si nécessaire.
6. Appliquer les migrations:
   ```bash
   python comparateur_prix/manage.py migrate
   ```
7. Créer un super utilisateur (optionnel):
   ```bash
   python comparateur_prix/manage.py createsuperuser
   ```
8. Lancer le serveur de dev:
   ```bash
   python comparateur_prix/manage.py runserver
   ```

## Variables d’environnement principales
- Django: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`
- DB: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`
- DRF/JWT: `USE_JWT_AUTH`, `JWT_*`
- CORS/CSRF: `CORS_ALLOW_ALL_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`
- Redis/Celery: `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`
- Google Maps: `GOOGLE_MAPS_API_KEY` (laisser vide par défaut)
- DGCCRF Scraper: `DGCCRF_BASE_URL`, `DGCCRF_USER_AGENT`, `DGCCRF_REQUEST_DELAY`
