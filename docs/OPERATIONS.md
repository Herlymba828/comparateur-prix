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

### Dépannage Celery/Redis
- Si les commandes `.delay()` semblent bloquer (erreurs de connexion Redis), vérifiez que Redis est démarré et accessible, et que le worker Celery tourne.
- Exemple Windows (PowerShell): lancez Redis, puis dans un autre terminal lancez le worker.

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

## Géocodage des magasins (Google Geocoding API)
- Configurer dans `.env`:
  - `GOOGLE_API_KEY` (obligatoire)
  - `GOOGLE_GEOCODE_ENDPOINT` (optionnel, défaut: https://maps.googleapis.com/maps/api/geocode/json)
  - `GOOGLE_TIMEOUT`, `GOOGLE_CACHE_TTL`, `DEFAULT_COUNTRY_NAME`
- Lancer le géocodage en lot:
```bash
python comparateur_prix/manage.py geocode_magasins --only-missing --limit 500
# Pour regéocoder même ceux déjà géocodés (enrichir formatted_address/place_id):
python comparateur_prix/manage.py geocode_magasins --force --limit 500
```
Le provider de géocodage stocké dans `Magasin.geocoding_provider` est désormais `"Google"`.

## Modèles ML (recommandations/prix)
- Initialiser/entraîner en local (synchrone):
```bash
python comparateur_prix/manage.py shell -c "from apps.recommandations.modeles_ml import GestionnaireRecommandations as G; g=G(); g.initialiser_modeles(); print('init:', g.est_initialise)"
```
- Entraîner via Celery (asynchrone):
```bash
python comparateur_prix/manage.py shell -c "from apps.recommandations.tasks import entrainer_modele_recommandation as t; t.delay('contenu')"
python comparateur_prix/manage.py shell -c "from apps.recommandations.tasks import entrainer_modele_recommandation as t; t.delay('prix')"
```
- Artefacts: sauvegardés par défaut dans `ml_models/artifacts/` (`*_latest.joblib`). Vous pouvez définir `ML_ARTIFACTS_DIR` dans les settings.
- Cache: un registry des chemins d’artefacts est conservé dans le cache (`ml_registry`).

### Troubleshooting ML
- scikit-learn TF‑IDF: certaines versions n’acceptent que `stop_words='english'`. Le code utilise `stop_words=None` pour compatibilité.
- Numpy/Decimal: la cible prix est convertie en float avant `np.log1p` pour éviter l’erreur `Decimal`.
- Embeddings optionnels: si `sentence-transformers` n’est pas installé ou le modèle indisponible, fallback automatique en TF‑IDF+SVD.

## Audit des homologations (qualité des données)
- Générer un rapport des `HomologationProduit` avec `sous_categorie` vide:
```bash
python comparateur_prix/manage.py audit_homologations --stats
python comparateur_prix/manage.py audit_homologations --limit 50 --offset 0
python comparateur_prix/manage.py audit_homologations --csv comparateur_prix/data/homologations_sans_sous_categorie.csv
```
