# 🔧 Corrections du fichier .env pour la production

## ❌ Problèmes identifiés dans votre fichier .env actuel

1. **DJANGO_DEBUG=True** → Doit être `False` en production
2. **POSTGRES_SSL_REQUIRE=True** → Sur cPanel, généralement `False`
3. **DJANGO_ALLOWED_HOSTS** → Manque le domaine de production
4. **CORS_ALLOWED_ORIGINS** → Ne contient que localhost, pas le domaine de production
5. **CSRF_TRUSTED_ORIGINS** → Ne contient pas le domaine de production
6. **CORS_ALLOW_ALL_ORIGINS** → Défini deux fois avec des valeurs contradictoires

## ✅ Fichier .env corrigé pour la production

Voici les **modifications à apporter** à votre fichier `.env` :

### 1. Modifier DJANGO_DEBUG

**AVANT :**
```bash
DJANGO_DEBUG=True
```

**APRÈS :**
```bash
DJANGO_DEBUG=False
```

### 2. Modifier POSTGRES_SSL_REQUIRE

**AVANT :**
```bash
POSTGRES_SSL_REQUIRE=True
```

**APRÈS :**
```bash
POSTGRES_SSL_REQUIRE=False
```

### 3. Modifier DJANGO_ALLOWED_HOSTS

**AVANT :**
```bash
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.67
```

**APRÈS :**
```bash
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.67,ftp.navixtechnology.com,www.ftp.navixtechnology.com
```

### 4. Modifier CSRF_TRUSTED_ORIGINS

**AVANT :**
```bash
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://192.168.1.67:8001,http://127.0.0.1:8001,http://localhost:8001
```

**APRÈS :**
```bash
CSRF_TRUSTED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,http://localhost:8000,http://127.0.0.1:8000,http://192.168.1.67:8001,http://127.0.0.1:8001,http://localhost:8001
```

### 5. Modifier CORS_ALLOWED_ORIGINS

**AVANT :**
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**APRÈS :**
```bash
CORS_ALLOWED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000
```

### 6. Supprimer la duplication de CORS_ALLOW_ALL_ORIGINS

**SUPPRIMER cette ligne** (elle apparaît deux fois) :
```bash
CORS_ALLOW_ALL_ORIGINS=True
```

**GARDER uniquement :**
```bash
CORS_ALLOW_ALL_ORIGINS=False
```

### 7. Modifier BACKEND_URL et FRONTEND_URL (optionnel mais recommandé)

**AVANT :**
```bash
FRONTEND_URL=http://127.0.0.1:3000
BACKEND_URL=http://127.0.0.1:8001
```

**APRÈS :**
```bash
FRONTEND_URL=https://comparateurdeprix.com
BACKEND_URL=https://ftp.navixtechnology.com
```

## 📋 Fichier .env complet corrigé

Voici un fichier `.env` complet et corrigé pour la production :

```bash
# Base de données PostgreSQL
POSTGRES_DB=rs2694021ez6eg8n_soutenance2.0
POSTGRES_USER=rs2694021ez6eg8n_db_user
POSTGRES_PASSWORD=BlackEurtz8282@
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_SSL_REQUIRE=False

# Django
DJANGO_SECRET_KEY=TmbjAfKjFXpor5UXwUbTN4Sna_JbwoXxwb_Clkgtv_ktJH2IOfhvMoAdfClV4eKiZKI
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,192.168.1.67,ftp.navixtechnology.com,www.ftp.navixtechnology.com

# CSRF
CSRF_TRUSTED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,http://localhost:8000,http://127.0.0.1:8000,http://192.168.1.67:8001,http://127.0.0.1:8001,http://localhost:8001

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000

# JWT Auth
USE_JWT_AUTH=true
JWT_ACCESS_MIN=15
JWT_REFRESH_DAYS=7
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=secrets/jwt_private.pem
JWT_PUBLIC_KEY_PATH=secrets/jwt_public.pem

# Redis
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_URL=redis://127.0.0.1:6379/1

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True

# DRF
DRF_THROTTLE_ANON=100/min
DRF_THROTTLE_USER=1000/min

# Frontend/Backend
FRONTEND_URL=https://comparateurdeprix.com
BACKEND_URL=https://ftp.navixtechnology.com
PUBLIC_BASE_URL=https://comparateurdeprix.com

# SMTP
EMAIL_HOST=smtp.ComparateurPrixBot.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_smtp_user
EMAIL_HOST_PASSWORD=your_smtp_password
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=no-reply@ComparateurPrixBot.com

# Réseaux sociaux
GOOGLE_CLIENT_ID=139484318993-npf1ptnr9ih9k1got5b4fgl3qt3c3mn6.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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
FACEBOOK_APP_ID=YOUR_FACEBOOK_APP_ID
FACEBOOK_APP_SECRET=YOUR_FACEBOOK_APP_SECRET
APPLE_CLIENT_ID=YOUR_APPLE_SERVICE_ID_OR_APP_ID
APPLE_TEAM_ID=YOUR_APPLE_TEAM_ID
APPLE_KEY_ID=YOUR_APPLE_KEY_ID
APPLE_PRIVATE_KEY_PEM=-----BEGIN PRIVATE KEY-----<YOUR_APPLE_PRIVATE_KEY>-----END PRIVATE KEY-----

# Géocodage
GOOGLE_API_KEY=AQ.Ab8RN6JDaSlCNOMXZ3GbXDuqWt2XO1X6V0MLgwcJm4W_XzFnmw
GOOGLE_GEOCODE_ENDPOINT=https://maps.googleapis.com/maps/api/geocode/json
GOOGLE_TIMEOUT=5
GOOGLE_CACHE_TTL=86400
DEFAULT_COUNTRY_NAME=Gabon

# Elasticsearch
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_SCHEME=http
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_VERIFY_CERTS=false
ELASTICSEARCH_INDEX_PRODUCTS=produits
ELASTICSEARCH_INDEX_SUGGEST=produits_suggest

# Scraping DGCCRF
DGCCRF_BASE_URL=https://example.dgccrf.fr/editions/
DGCCRF_USER_AGENT=ComparateurPrixBot/1.0 (+contact@example.com)
DGCCRF_REQUEST_DELAY=1.0
DGCCRF_TIMEOUT=30
DGCCRF_MAX_RETRIES=3
DGCCRF_BACKOFF=1.5
DGCCRF_SAVE_TO_DB=true
DGCCRF_SKIP_UNCHANGED=true
DGCCRF_REPORT_OUT=data/dgccrf_report.json
DGCCRF_LOG_FILE=logs/dgccrf_scraper.log
DGCCRF_RAW_DIR=data/raw/dgccrf
DGCCRF_PROXY=
DGCCRF_STATE_FILE=.dgccrf_state.json
DGCCRF_CHECKPOINT_PATH=.dgccrf_checkpoint.json
DGCCRF_PRIX_HOMOLOGUE_URL=https://www.dgccrf.ga/echo-prix-homologue
DGCCRF_LISTE_PRODUIT_URL=https://www.dgccrf.ga/echo-liste-produit
DGCCRF_PRODUIT_PETROLIER_URL=https://www.dgccrf.ga/echo-produit-petrolier
DGCCRF_RESPECT_ROBOTS=true

# Google Maps
GOOGLE_MAPS_API_KEY=

# Admin URL
DJANGO_ADMIN_URL=admin/

# Recherche
SEARCH_INDEX_ENABLED=false
RECO_INIT_MODELS_ON_STARTUP=False
```

## 🚀 Commandes à exécuter après modification

```bash
# 1. Vérifier que le fichier .env est bien modifié
cat .env | grep -E "DJANGO_DEBUG|POSTGRES_SSL_REQUIRE|DJANGO_ALLOWED_HOSTS"

# 2. Tester la connexion à la base de données
python manage.py dbshell

# 3. Appliquer les migrations
python manage.py migrate

# 4. Vérifier la configuration
python manage.py check --deploy

# 5. Redémarrer l'application (Railway redémarre automatiquement après déploiement)
```

## ⚠️ Notes importantes

1. **POSTGRES_SSL_REQUIRE** : Sur Railway, SSL est généralement requis. En développement local, vous pouvez le mettre à `False` si nécessaire.

2. **DJANGO_DEBUG=False** : **OBLIGATOIRE** en production pour la sécurité. Les paramètres de sécurité (HSTS, SSL redirect, etc.) s'activeront automatiquement.

3. **Domaines** : Assurez-vous que `ftp.navixtechnology.com` est bien votre domaine de production. Si vous utilisez un autre domaine, remplacez-le dans les configurations.

4. **HTTPS vs HTTP** : Si votre site utilise HTTPS, privilégiez les URLs `https://` dans `CORS_ALLOWED_ORIGINS` et `CSRF_TRUSTED_ORIGINS`. J'ai inclus les deux (http et https) pour la transition.

