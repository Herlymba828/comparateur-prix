# 🔧 Corrections du fichier .env pour la production

## ❌ Problèmes critiques identifiés dans votre fichier .env actuel

### 1. **DJANGO_DEBUG=True** ⚠️ CRITIQUE
- **Problème** : Le mode debug est activé en production, ce qui expose des informations sensibles et désactive les protections de sécurité
- **Impact** : Risque de sécurité majeur, exposition d'informations sensibles dans les erreurs

### 2. **POSTGRES_SSL_REQUIRE=True** alors que vous utilisez MySQL
- **Problème** : Vous utilisez `DB_ENGINE=mysql` mais avez `POSTGRES_SSL_REQUIRE=True`
- **Impact** : Variable inutile et potentiellement source de confusion

### 3. **DJANGO_ALLOWED_HOSTS** - Valeur tronquée
- **Problème** : La valeur semble tronquée (se termine par `$`)
- **Impact** : Le domaine de production pourrait ne pas être correctement configuré

### 4. **CSRF_TRUSTED_ORIGINS** - Valeur tronquée
- **Problème** : La valeur semble tronquée (se termine par `$`)
- **Impact** : Les requêtes CSRF depuis le frontend de production pourraient être rejetées

### 5. **CORS_ALLOWED_ORIGINS** - Manque les domaines de production
- **Problème** : Ne contient que `localhost` et `127.0.0.1`, pas les domaines de production
- **Impact** : Le frontend de production ne pourra pas faire de requêtes CORS vers l'API

### 6. **CORS_ALLOW_ALL_ORIGINS** - Défini deux fois
- **Problème** : Défini deux fois avec des valeurs contradictoires (`True` puis `False`)
- **Impact** : La dernière valeur prévaut (`False`), donc c'est correct mais redondant

### 7. **FRONTEND_URL et BACKEND_URL** - Pointent vers localhost
- **Problème** : Pointent vers `127.0.0.1` au lieu des URLs de production
- **Impact** : Les liens générés par l'application pointeront vers localhost

### 8. **SITE_URL vs PUBLIC_BASE_URL** - Incohérence
- **Problème** : `SITE_URL=https://ftp.navixtechnology.com` mais `PUBLIC_BASE_URL=https://comparateurdeprix.com`
- **Impact** : Confusion sur l'URL réelle du site

### 9. **EMAIL_HOST_USER** - Placeholder
- **Problème** : Contient `your_smtp_user` qui semble être un placeholder
- **Impact** : L'envoi d'emails ne fonctionnera pas

### 10. **EMAIL_HOST_PASSWORD** - Manquant
- **Problème** : Variable absente de l'extrait
- **Impact** : L'authentification SMTP ne fonctionnera pas

---

## ✅ Corrections à apporter

### Correction 1 : Désactiver DEBUG en production

**AVANT :**
```bash
DJANGO_DEBUG=True
```

**APRÈS :**
```bash
DJANGO_DEBUG=False
```

**⚠️ IMPORTANT** : Cette modification est **OBLIGATOIRE** pour la sécurité en production.

---

### Correction 2 : Supprimer ou corriger POSTGRES_SSL_REQUIRE

Puisque vous utilisez MySQL, vous pouvez soit :

**Option A : Supprimer la ligne** (recommandé)
```bash
# Supprimer cette ligne car vous utilisez MySQL
# POSTGRES_SSL_REQUIRE=True
```

**Option B : La garder mais la mettre à False** (si vous prévoyez de migrer vers PostgreSQL)
```bash
POSTGRES_SSL_REQUIRE=False
```

---

### Correction 3 : Corriger DJANGO_ALLOWED_HOSTS

**AVANT :**
```bash
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,ftp.navixtechnology.com,www.ftp.nav$
```

**APRÈS :**
```bash
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,ftp.navixtechnology.com,www.ftp.navixtechnology.com,comparateurdeprix.com,www.comparateurdeprix.com
```

**Note** : J'ai ajouté `comparateurdeprix.com` car c'est votre `PUBLIC_BASE_URL`. Si ce n'est pas le bon domaine, ajustez-le.

---

### Correction 4 : Corriger CSRF_TRUSTED_ORIGINS

**AVANT :**
```bash
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000,http://192.$
```

**APRÈS :**
```bash
CSRF_TRUSTED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001
```

**Note** : J'ai inclus à la fois HTTP et HTTPS pour permettre la transition. Une fois que tout fonctionne en HTTPS, vous pouvez supprimer les entrées HTTP.

---

### Correction 5 : Corriger CORS_ALLOWED_ORIGINS

**AVANT :**
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

**APRÈS :**
```bash
CORS_ALLOWED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000
```

---

### Correction 6 : Supprimer la duplication de CORS_ALLOW_ALL_ORIGINS

**SUPPRIMER cette ligne** (la première occurrence) :
```bash
CORS_ALLOW_ALL_ORIGINS=True
```

**GARDER uniquement :**
```bash
CORS_ALLOW_ALL_ORIGINS=False
```

---

### Correction 7 : Corriger FRONTEND_URL et BACKEND_URL

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

**Note** : Ajustez selon vos URLs réelles de production.

---

### Correction 8 : Harmoniser SITE_URL et PUBLIC_BASE_URL

**Option A : Si votre site principal est `comparateurdeprix.com`**
```bash
SITE_URL=https://comparateurdeprix.com
PUBLIC_BASE_URL=https://comparateurdeprix.com
```

**Option B : Si votre site principal est `ftp.navixtechnology.com`**
```bash
SITE_URL=https://ftp.navixtechnology.com
PUBLIC_BASE_URL=https://ftp.navixtechnology.com
```

**Note** : Choisissez l'option qui correspond à votre architecture réelle.

---

### Correction 9 : Corriger EMAIL_HOST_USER

**AVANT :**
```bash
EMAIL_HOST_USER=your_smtp_user
```

**APRÈS :**
```bash
EMAIL_HOST_USER=votre_utilisateur_smtp_reel
```

**Note** : Remplacez par votre véritable nom d'utilisateur SMTP.

---

### Correction 10 : Ajouter EMAIL_HOST_PASSWORD

**AJOUTER :**
```bash
EMAIL_HOST_PASSWORD=votre_mot_de_passe_smtp_reel
```

**Note** : Ajoutez le mot de passe SMTP réel. Assurez-vous que ce fichier `.env` a les bonnes permissions (`chmod 600 .env`).

---

## 📋 Fichier .env complet corrigé (extrait des sections critiques)

Voici les sections critiques corrigées :

```bash
# Django
# En production: définissez OBLIGATOIREMENT DJANGO_SECRET_KEY (valeur forte)
DJANGO_SECRET_KEY=TmbjAfKjFXpor5UXwUbTN4Sna_JbwoXxwb_Clkgtv_ktJH2IOfhvMoAdfC$
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,ftp.navixtechnology.com,www.ftp.navixtechnology.com,comparateurdeprix.com,www.comparateurdeprix.com
CSRF_TRUSTED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001
RECO_INIT_MODELS_ON_STARTUP=False

# Database (MySQL)
# En production: définissez OBLIGATOIREMENT DB_PASSWORD
DB_ENGINE=mysql
DB_NAME=rs2694021ez6eg8n_soutenance2.0
DB_USER=rs2694021ez6eg8n_db_user
DB_PASSWORD=BlackEurtz8282@
DB_HOST=localhost
DB_PORT=3306
# Note: POSTGRES_SSL_REQUIRE n'est pas nécessaire avec MySQL

# CORS/CSRF (mettre des valeurs plus strictes en production)
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://ftp.navixtechnology.com,http://ftp.navixtechnology.com,https://www.ftp.navixtechnology.com,http://www.ftp.navixtechnology.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000

# JWT Auth
USE_JWT_AUTH=true
JWT_ACCESS_MIN=15
JWT_REFRESH_DAYS=7
SITE_URL=https://ftp.navixtechnology.com

# Algorithme de signature JWT
JWT_ALGORITHM=RS256

# RS256: chemins vers les clés PEM (ne pas commiter ces fichiers)
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

# Public base URL for activation links
PUBLIC_BASE_URL=https://comparateurdeprix.com

# SMTP
EMAIL_HOST=smtp.ComparateurPrixBot.com
EMAIL_PORT=587
EMAIL_HOST_USER=votre_utilisateur_smtp_reel
EMAIL_HOST_PASSWORD=votre_mot_de_passe_smtp_reel
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=no-reply@ComparateurPrixBot.com
```

---

## 🚀 Commandes à exécuter après modification

### 1. Vérifier que le fichier .env est bien modifié

```bash
cd /home/rs2694021ez6eg8n/comparer1/comparateur-prix
cat .env | grep -E "DJANGO_DEBUG|DJANGO_ALLOWED_HOSTS|CORS_ALLOWED_ORIGINS"
```

### 2. Vérifier les permissions du fichier .env

```bash
chmod 600 .env
ls -la .env
# Doit afficher: -rw------- (seul le propriétaire peut lire/écrire)
```

### 3. Tester la connexion à la base de données

```bash
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate
python manage.py dbshell
# Si cela fonctionne, tapez \q pour quitter
```

### 4. Vérifier la configuration Django

```bash
python manage.py check --deploy
```

Cette commande vérifiera :
- Que DEBUG est bien False
- Que SECRET_KEY est défini
- Que les paramètres de sécurité sont corrects
- Que la base de données est accessible

### 5. Redémarrer l'application

Via cPanel :
- Allez dans **"Setup Python App"** ou **"Passenger"**
- Cliquez sur **"Restart"** ou **"Reload"**

Ou via SSH :
```bash
# Toucher le fichier passenger_wsgi.py pour forcer le redémarrage
touch passenger_wsgi.py
```

---

## ⚠️ Notes importantes

1. **DJANGO_DEBUG=False** : **OBLIGATOIRE** en production. Une fois modifié, les paramètres de sécurité (HSTS, SSL redirect, etc.) s'activeront automatiquement.

2. **Domaines** : Assurez-vous que les domaines dans `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` et `CORS_ALLOWED_ORIGINS` correspondent à vos vrais domaines de production.

3. **HTTPS vs HTTP** : J'ai inclus les deux (http et https) pour permettre la transition. Une fois que tout fonctionne en HTTPS, vous pouvez supprimer les entrées HTTP.

4. **SMTP** : Remplacez `votre_utilisateur_smtp_reel` et `votre_mot_de_passe_smtp_reel` par vos vraies credentials SMTP.

5. **Sauvegarde** : Avant de modifier le fichier `.env`, faites une copie de sauvegarde :
   ```bash
   cp .env .env.backup
   ```

---

## 🔍 Vérification post-modification

Après avoir appliqué les corrections, testez :

1. **Accès à l'API** :
   - `https://ftp.navixtechnology.com/api/docs/` (Swagger UI)
   - `https://ftp.navixtechnology.com/api/produits/produits/` (Liste des produits)

2. **Accès à l'admin** :
   - `https://ftp.navixtechnology.com/admin/`

3. **Vérifier les logs** :
   ```bash
   tail -f logs/*.log
   # ou
   tail -f /usr/local/apache/logs/error_log
   ```

4. **Tester depuis le frontend** :
   - Vérifiez que les requêtes CORS fonctionnent
   - Vérifiez que les requêtes CSRF fonctionnent

---

## 📞 En cas de problème

Si après les modifications vous rencontrez des erreurs :

1. **Erreur 500** : Vérifiez les logs et que toutes les variables sont correctement définies
2. **Erreur CORS** : Vérifiez que le domaine du frontend est bien dans `CORS_ALLOWED_ORIGINS`
3. **Erreur CSRF** : Vérifiez que le domaine est bien dans `CSRF_TRUSTED_ORIGINS`
4. **Erreur ALLOWED_HOSTS** : Vérifiez que le domaine est bien dans `DJANGO_ALLOWED_HOSTS`

Si nécessaire, vous pouvez temporairement remettre `DJANGO_DEBUG=True` pour voir les erreurs détaillées, mais **remettez-le à False** dès que possible.

