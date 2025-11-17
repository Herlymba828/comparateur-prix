# 📝 Fichier .env de Production - Version Corrigée

## 🔧 Corrections apportées

1. ✅ **BACKEND_URL** : Mis à jour pour Railway (`comparo.up.railway.app`)
2. ✅ **DJANGO_ALLOWED_HOSTS** : Ajout du domaine Railway
3. ✅ **CSRF_TRUSTED_ORIGINS** : Ajout du domaine Railway
4. ✅ **SITE_URL** : Mis à jour pour Railway
5. ✅ **CORS_ALLOWED_ORIGINS** : Suppression de la duplication, consolidation en une seule ligne complète
6. ✅ **Nettoyage** : Suppression des lignes dupliquées
7. ✅ **Optimisation** : Organisation et commentaires améliorés

---

## 📄 Fichier .env complet corrigé

```bash
# ============================================
# DJANGO CONFIGURATION
# ============================================
# En production: définissez OBLIGATOIREMENT DJANGO_SECRET_KEY (valeur forte et secrète)
DJANGO_SECRET_KEY=TmbjAfKjFXpor5UXwUbTN4Sna_JbwoXxwb_Clkgtv_ktJH2IOfhvMoAdfClV4eKiZKI
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=comparo.up.railway.app,*.railway.app,comparateurdeprix.com,www.comparateurdeprix.com,localhost,127.0.0.1

# CSRF Protection
CSRF_TRUSTED_ORIGINS=https://comparo.up.railway.app,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001

# CORS Configuration
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000

# ============================================
# DATABASE CONFIGURATION (MySQL)
# ============================================
DB_ENGINE=mysql
DB_NAME=rs2694021ez6eg8n_soutenance2.0
DB_USER=rs2694021ez6eg8n_db_user
DB_PASSWORD=BlackEurtz8282@
DB_HOST=localhost
DB_PORT=3306

# ============================================
# JWT AUTHENTICATION
# ============================================
USE_JWT_AUTH=true
JWT_ACCESS_MIN=15
JWT_REFRESH_DAYS=7
SITE_URL=https://comparo.up.railway.app
PUBLIC_BASE_URL=https://comparateurdeprix.com

# Algorithme de signature JWT
# - RS256 (recommandé en multi-services) avec clés PEM
# - HS256 (clé secrète partagée) si plus simple pour un seul backend
JWT_ALGORITHM=RS256

# RS256: chemins vers les clés PEM (ne pas commiter ces fichiers)
JWT_PRIVATE_KEY_PATH=secrets/jwt_private.pem
JWT_PUBLIC_KEY_PATH=secrets/jwt_public.pem

# HS256 (alternative): définir une clé forte si vous utilisez HS256
# JWT_SIGNING_KEY=

# ============================================
# REDIS & CELERY
# ============================================
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_URL=redis://127.0.0.1:6379/1

# Celery Configuration
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True

# ============================================
# DRF (Django REST Framework)
# ============================================
DRF_THROTTLE_ANON=100/min
DRF_THROTTLE_USER=1000/min

# ============================================
# FRONTEND/BACKEND URLs
# ============================================
FRONTEND_URL=https://comparateurdeprix.com
BACKEND_URL=https://comparo.up.railway.app
PUBLIC_BASE_URL=https://comparateurdeprix.com

# ============================================
# EMAIL CONFIGURATION (SMTP)
# ============================================
EMAIL_HOST=mail.comparateurdeprix.com
EMAIL_PORT=587
EMAIL_HOST_USER=no-reply@comparateurdeprix.com
EMAIL_HOST_PASSWORD=BlackEurtz8282@
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=no-reply@comparateurdeprix.com

# ============================================
# SOCIAL AUTHENTICATION
# ============================================
# Google OAuth
GOOGLE_CLIENT_ID=139484318993-npf1ptnr9ih9k1got5b4fgl3qt3c3mn6.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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

# Facebook OAuth
FACEBOOK_APP_ID=YOUR_FACEBOOK_APP_ID
FACEBOOK_APP_SECRET=YOUR_FACEBOOK_APP_SECRET

# Apple OAuth (tous requis pour activer AppleIdAuth)
APPLE_CLIENT_ID=YOUR_APPLE_SERVICE_ID_OR_APP_ID
APPLE_TEAM_ID=YOUR_APPLE_TEAM_ID
APPLE_KEY_ID=YOUR_APPLE_KEY_ID
# Mettre la clé privée Apple sur UNE SEULE LIGNE (les retours à la ligne cassent python-dotenv)
# Remplacez <YOUR_APPLE_PRIVATE_KEY> par votre clé sans retours à la ligne
APPLE_PRIVATE_KEY_PEM=-----BEGIN PRIVATE KEY-----<YOUR_APPLE_PRIVATE_KEY>-----END PRIVATE KEY-----

# ============================================
# GOOGLE SERVICES
# ============================================
# Géocodage (Google Geocoding API)
GOOGLE_API_KEY=AQ.Ab8RN6JDaSlCNOMXZ3GbXDuqWt2XO1X6V0MLgwcJm4W_XzFnmw
GOOGLE_GEOCODE_ENDPOINT=https://maps.googleapis.com/maps/api/geocode/json
GOOGLE_TIMEOUT=5
GOOGLE_CACHE_TTL=86400
DEFAULT_COUNTRY_NAME=Gabon

# Google Maps (Distance Matrix + JS Maps)
GOOGLE_MAPS_API_KEY=

# ============================================
# ELASTICSEARCH (Optionnel)
# ============================================
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_SCHEME=http
ELASTICSEARCH_USERNAME=
ELASTICSEARCH_PASSWORD=
ELASTICSEARCH_VERIFY_CERTS=false
ELASTICSEARCH_INDEX_PRODUCTS=produits
ELASTICSEARCH_INDEX_SUGGEST=produits_suggest

# ============================================
# DGCCRF SCRAPING CONFIGURATION
# ============================================
DGCCRF_BASE_URL=https://example.dgccrf.fr/editions/
DGCCRF_USER_AGENT=ComparateurPrixBot/1.0 (+contact@example.com)
DGCCRF_REQUEST_DELAY=1.0
# Délai maximum (s), retries et backoff exponentiel
DGCCRF_TIMEOUT=30
DGCCRF_MAX_RETRIES=3
DGCCRF_BACKOFF=1.5
DGCCRF_SAVE_TO_DB=true
# n'insérer que les changements détectés
DGCCRF_SKIP_UNCHANGED=true
DGCCRF_REPORT_OUT=data/dgccrf_report.json
DGCCRF_LOG_FILE=logs/dgccrf_scraper.log
DGCCRF_RAW_DIR=data/raw/dgccrf
# Proxy HTTP/HTTPS (laisser vide si non utilisé)
DGCCRF_PROXY=
# Fichiers d'état et de checkpoint pour détection de changements et reprise
DGCCRF_STATE_FILE=.dgccrf_state.json
DGCCRF_CHECKPOINT_PATH=.dgccrf_checkpoint.json
# URLs spécifiques (peuvent surcharger les défauts du scraper)
DGCCRF_PRIX_HOMOLOGUE_URL=https://www.dgccrf.ga/echo-prix-homologue
DGCCRF_LISTE_PRODUIT_URL=https://www.dgccrf.ga/echo-liste-produit
DGCCRF_PRODUIT_PETROLIER_URL=https://www.dgccrf.ga/echo-produit-petrolier
DGCCRF_RESPECT_ROBOTS=true

# ============================================
# DJANGO ADMIN & SEARCH
# ============================================
# Admin URL paramétrable (obfuscation basique en prod)
DJANGO_ADMIN_URL=admin/

# Désactiver l'indexation Elasticsearch pendant les imports (signaux produits)
SEARCH_INDEX_ENABLED=false

# Recommandations ML
RECO_INIT_MODELS_ON_STARTUP=False
```

---

## 🔄 Changements principaux

### 1. BACKEND_URL mis à jour pour Railway
```diff
- BACKEND_URL=https://ftp.navixtechnology.com
+ BACKEND_URL=https://comparo.up.railway.app
```

### 2. CORS_ALLOWED_ORIGINS consolidé
```diff
- CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000  (première occurrence)
- CORS_ALLOWED_ORIGINS=https://ftp.navixtechnology.com,... (deuxième occurrence)
+ CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000
```

### 3. DJANGO_ALLOWED_HOSTS mis à jour pour Railway
```diff
- DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,ftp.navixtechnology.com,www.ftp.navixtechnology.com,comparateurdeprix.com,www.comparateurdeprix.com
+ DJANGO_ALLOWED_HOSTS=comparo.up.railway.app,*.railway.app,comparateurdeprix.com,www.comparateurdeprix.com,localhost,127.0.0.1
```
*(Inclut maintenant le domaine Railway : comparo.up.railway.app)*

### 4. CSRF_TRUSTED_ORIGINS mis à jour pour Railway
```diff
- CSRF_TRUSTED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,...
+ CSRF_TRUSTED_ORIGINS=https://comparo.up.railway.app,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001
```

---

## 📋 Instructions d'utilisation

### Sur le serveur (via SSH)

1. **Sauvegarder l'ancien fichier** :
```bash
cd /home/rs2694021ez6eg8n/public_html/comparer
cp .env .env.backup
```

2. **Modifier le fichier .env** :
```bash
nano .env
```

3. **Appliquer les changements** (copiez-collez le contenu corrigé ci-dessus)

4. **Vérifier la configuration** :
```bash
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate
python manage.py check --deploy
```

5. **Redémarrer l'application** :
   - Dans cPanel → **Setup Python App** → **Restart**

6. **Tester** :
   - Railway : `https://comparo.up.railway.app/api/health/`
   - cPanel : `https://comparateurdeprix.com/api/health/`
   - `https://comparateurdeprix.com/api/docs/`

---

## ⚠️ Notes importantes

1. **BACKEND_URL** : Maintenant pointé vers `comparo.up.railway.app` pour Railway (ou `comparateurdeprix.com` pour cPanel)
2. **Domaines** : Les références à `ftp.navixtechnology.com` ont été supprimées (sauf si vous en avez vraiment besoin)
3. **CORS** : Consolidé en une seule ligne complète
4. **Sécurité** : Tous les domaines de production utilisent HTTPS

---

## 🎯 Si vous utilisez un sous-domaine API

Si vous créez `api.comparateurdeprix.com`, modifiez :

```bash
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,api.comparateurdeprix.com,comparateurdeprix.com,www.comparateurdeprix.com
BACKEND_URL=https://api.comparateurdeprix.com
CSRF_TRUSTED_ORIGINS=https://api.comparateurdeprix.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,...
CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000
```

