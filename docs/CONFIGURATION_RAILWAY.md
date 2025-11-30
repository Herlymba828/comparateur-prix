# ⚙️ Configuration Railway

Guide complet pour configurer votre application Django sur Railway, incluant les variables d'environnement, la base de données, les domaines et les guides rapides.

## 📋 Table des matières

- [Démarrage Rapide](#démarrage-rapide)
- [Configuration Base de Données](#configuration-base-de-données)
- [Variables d'Environnement](#variables-denvironnement)
- [Configuration Domaine](#configuration-domaine)
- [Dépannage](#dépannage)

---

## ⚡ Démarrage Rapide

### 1️⃣ Créer le service PostgreSQL (2 minutes)

1. Allez sur https://railway.app
2. Ouvrez votre projet
3. Cliquez sur **"+ New"** → **"Database"** → **"Add PostgreSQL"**
4. Attendez 1-2 minutes que Railway crée la base de données

✅ **C'est tout !** Railway configure automatiquement `DATABASE_URL`.

### 2️⃣ Configurer les variables d'environnement (3 minutes)

Dans Railway → Votre service Django → **Variables**, ajoutez :

```bash
# OBLIGATOIRE
DJANGO_SECRET_KEY=votre_clé_secrète_générée
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=comparo.up.railway.app,*.railway.app

# URLs
SITE_URL=https://comparo.up.railway.app
BACKEND_URL=https://comparo.up.railway.app
```

**Générer une clé secrète :**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3️⃣ Appliquer les migrations (1 minute)

**Option A : Via Railway CLI (Recommandé)**
```bash
npm i -g @railway/cli
railway login
railway link
railway run python manage.py migrate
```

**Option B : Via l'interface Railway**
- Allez dans votre service Django
- Cliquez sur **"Deployments"** → **"View Logs"**
- Ou utilisez le shell Railway

### 4️⃣ Vérifier que tout fonctionne

1. Allez sur `https://comparo.up.railway.app/api/health/`
2. Vous devriez voir : `{"status": "ok"}`

✅ **Terminé !** Votre application est configurée.

---

## 🗄️ Configuration Base de Données

### Créer le service PostgreSQL

**Méthode 1 : Via l'interface Railway (Recommandé)**

1. **Connectez-vous à Railway**
   - Allez sur https://railway.app
   - Connectez-vous avec votre compte

2. **Sélectionnez votre projet**
   - Cliquez sur votre projet dans le tableau de bord

3. **Ajoutez PostgreSQL**
   - Cliquez sur le bouton **"+ New"** (en haut à droite)
   - Dans le menu déroulant, sélectionnez **"Database"**
   - Cliquez sur **"Add PostgreSQL"**

4. **Attendez la création**
   - Railway va créer automatiquement une instance PostgreSQL
   - Cela prend généralement 1-2 minutes
   - Vous verrez un nouveau service "Postgres" dans votre projet

**Méthode 2 : Via Railway CLI**

```bash
# Installer Railway CLI (si pas déjà fait)
npm i -g @railway/cli

# Se connecter
railway login

# Lier votre projet
railway link

# Créer PostgreSQL
railway add postgresql
```

### Vérifier DATABASE_URL

Railway configure automatiquement `DATABASE_URL` pour votre service Django.

**Vérification via l'interface Railway :**

1. **Dans votre projet Railway**
   - Cliquez sur votre service **Django** (pas PostgreSQL)
   - Allez dans l'onglet **"Variables"**

2. **Vérifiez que DATABASE_URL existe**
   - Cherchez la variable `DATABASE_URL`
   - Elle devrait ressembler à :
     ```
     postgresql://postgres:password@hostname.railway.internal:5432/railway
     ```

3. **Si DATABASE_URL n'apparaît pas**
   - Cliquez sur le service **PostgreSQL**
   - Allez dans l'onglet **"Variables"**
   - Copiez la valeur de `DATABASE_URL`
   - Retournez dans votre service Django
   - Ajoutez manuellement la variable `DATABASE_URL` avec la valeur copiée

**Vérification via Railway CLI :**

```bash
# Voir toutes les variables d'environnement
railway variables

# Voir spécifiquement DATABASE_URL
railway variables | grep DATABASE_URL
```

### Appliquer les migrations

**Méthode 1 : Via Railway CLI (Recommandé)**

```bash
# Installer Railway CLI (si pas déjà fait)
npm i -g @railway/cli

# Se connecter
railway login

# Lier votre projet
railway link

# Appliquer les migrations
railway run python manage.py migrate

# Créer un superutilisateur (optionnel)
railway run python manage.py createsuperuser

# Collecter les fichiers statiques
railway run python manage.py collectstatic --noinput
```

**Méthode 2 : Via l'interface Railway**

1. **Ouvrir un shell**
   - Allez dans votre service Django
   - Cliquez sur l'onglet **"Deployments"**
   - Cliquez sur le dernier déploiement
   - Cliquez sur **"View Logs"** ou **"Shell"**

2. **Exécuter les commandes**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

**Méthode 3 : Automatique au démarrage**

Créez un fichier `railway.json` à la racine :

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Vérifier la connexion

**Test 1 : Via Railway CLI**

```bash
# Tester la connexion à la base de données
railway run python manage.py dbshell

# Si ça fonctionne, vous verrez le prompt PostgreSQL
# Tapez \q pour quitter
```

**Test 2 : Via l'interface Railway**

1. **Voir les logs**
   - Allez dans votre service Django
   - Cliquez sur **"View Logs"**
   - Cherchez les messages de connexion à la base de données
   - Vous devriez voir : `✅ Connected to database`

2. **Tester l'API**
   - Allez sur `https://comparo.up.railway.app/api/health/`
   - Si la réponse est `{"status": "ok"}`, tout fonctionne !

**Test 3 : Via Python**

```bash
# Exécuter un script de test
railway run python manage.py shell

# Dans le shell Python :
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("✅ Connexion réussie!")
>>> exit()
```

---

## 🔧 Variables d'Environnement

### Variables Obligatoires

Dans Railway → Votre service Django → **Variables**, assurez-vous d'avoir :

```bash
# Django (OBLIGATOIRE)
DJANGO_SECRET_KEY=votre_clé_secrète_générée
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=comparo.up.railway.app,*.railway.app,localhost,127.0.0.1

# Base de données (AUTOMATIQUE - Railway le configure)
# DATABASE_URL est automatiquement fourni par Railway
# Aucune action nécessaire !

# URLs (OBLIGATOIRE)
SITE_URL=https://comparo.up.railway.app
BACKEND_URL=https://comparo.up.railway.app
PUBLIC_BASE_URL=https://comparateurdeprix.com
```

### Variables Optionnelles (mais recommandées)

```bash
# Redis (si vous utilisez Celery ou le cache)
REDIS_URL=redis://default:password@redis.railway.internal:6379
# Ou créez un service Redis sur Railway

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# JWT
USE_JWT_AUTH=true
JWT_ALGORITHM=HS256
# Ou RS256 avec des clés PEM

# CORS (si vous avez un frontend)
CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com
CSRF_TRUSTED_ORIGINS=https://comparo.up.railway.app,https://comparateurdeprix.com
```

### Comment ajouter des variables

**Via l'interface Railway :**

1. Allez dans votre service Django
2. Cliquez sur l'onglet **"Variables"**
3. Cliquez sur **"+ New Variable"**
4. Entrez le nom et la valeur
5. Cliquez sur **"Add"**

**Via Railway CLI :**

```bash
# Ajouter une variable
railway variables set DJANGO_SECRET_KEY=votre_clé

# Voir toutes les variables
railway variables
```

### Variables Partagées Automatiquement

Railway partage automatiquement certaines variables entre services du même projet :

- `DATABASE_URL` (si service PostgreSQL présent)
- `REDIS_URL` (si service Redis présent)

Cependant, `DATABASE_PUBLIC_URL` et `REDIS_PUBLIC_URL` ne sont **pas** partagées automatiquement. Vous devez les copier manuellement.

### Problème Courant : "connection to server at 127.0.0.1:5432 failed"

Si vous voyez cette erreur, cela signifie que `DATABASE_URL` ou `DATABASE_PUBLIC_URL` ne sont pas définies dans votre service Django sur Railway.

**Solution :**

1. Allez dans le service PostgreSQL Railway
2. Copiez `DATABASE_PUBLIC_URL` ou `DATABASE_URL`
3. Allez dans le service Django Railway
4. Ajoutez la variable `DATABASE_PUBLIC_URL` ou `DATABASE_URL` avec la valeur copiée
5. Redéployez le service Django

---

## 🌐 Configuration Domaine

### Option 1 : Utiliser le domaine principal (Simple)

Utilisez `comparateurdeprix.com` ou `www.comparateurdeprix.com` directement pour votre backend.

**Étapes :**

1. **Configurer le domaine sur Railway**
   - Dans Railway, allez dans votre projet
   - Ajoutez un domaine personnalisé : `comparateurdeprix.com`
   - Railway configure automatiquement le certificat SSL via Let's Encrypt

2. **Mettre à jour les variables d'environnement**
   ```bash
   # Django
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,comparateurdeprix.com,www.comparateurdeprix.com
   
   # CSRF
   CSRF_TRUSTED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:8000,http://127.0.0.1:8000
   
   # CORS
   CORS_ALLOW_ALL_ORIGINS=False
   CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000
   
   # Frontend/Backend
   FRONTEND_URL=https://comparateurdeprix.com
   BACKEND_URL=https://comparateurdeprix.com
   PUBLIC_BASE_URL=https://comparateurdeprix.com
   SITE_URL=https://comparateurdeprix.com
   ```

3. **Tester**
   - `https://comparateurdeprix.com/api/health/`
   - `https://comparateurdeprix.com/api/docs/`
   - `https://www.comparateurdeprix.com/api/health/`

### Option 2 : Créer un sous-domaine API (Recommandé pour séparation)

Créez un sous-domaine dédié pour l'API : `api.comparateurdeprix.com`

**Étapes :**

1. **Créer le sous-domaine sur Railway**
   - Dans Railway, allez dans votre projet
   - Ajoutez un domaine personnalisé : `api.comparateurdeprix.com`
   - Railway configure automatiquement le certificat SSL via Let's Encrypt

2. **Mettre à jour les variables d'environnement**
   ```bash
   # Django
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,api.comparateurdeprix.com,comparateurdeprix.com,www.comparateurdeprix.com
   
   # CSRF
   CSRF_TRUSTED_ORIGINS=https://api.comparateurdeprix.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:8000,http://127.0.0.1:8000
   
   # CORS
   CORS_ALLOW_ALL_ORIGINS=False
   CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000
   
   # Frontend/Backend
   FRONTEND_URL=https://comparateurdeprix.com
   BACKEND_URL=https://api.comparateurdeprix.com
   PUBLIC_BASE_URL=https://comparateurdeprix.com
   SITE_URL=https://comparateurdeprix.com
   ```

3. **Tester**
   - `https://api.comparateurdeprix.com/api/health/`
   - `https://api.comparateurdeprix.com/api/docs/`

**Recommandation :** L'Option 2 (Sous-domaine API) est recommandée car :
- ✅ Séparation claire entre frontend et backend
- ✅ Meilleure organisation
- ✅ Plus facile à maintenir
- ✅ Permet d'avoir le frontend sur `comparateurdeprix.com` et l'API sur `api.comparateurdeprix.com`

---

## 🔍 Dépannage

### Problème : "DATABASE_URL not found"

**Solution :**
1. Vérifiez que le service PostgreSQL est bien créé
2. Vérifiez que les services sont dans le même projet Railway
3. Railway devrait automatiquement partager `DATABASE_URL`
4. Si nécessaire, copiez manuellement `DATABASE_URL` depuis le service PostgreSQL vers le service Django

### Problème : "Connection refused" ou "Connection timeout"

**Solutions :**
1. Vérifiez que le service PostgreSQL est démarré (pas en pause)
2. Vérifiez que `DATABASE_URL` est correct
3. Vérifiez que `DJANGO_DEBUG=False` (en production)
4. Vérifiez les logs Railway pour plus de détails

### Problème : "relation does not exist" ou "table does not exist"

**Solution :**
```bash
# Appliquer les migrations
railway run python manage.py migrate
```

### Problème : "SSL connection required"

**Solution :**
Railway utilise SSL par défaut. Votre configuration Django devrait déjà gérer cela automatiquement. Si vous avez des erreurs :

1. Vérifiez que `dj-database-url` est dans `requirements.txt`
2. Vérifiez que `ssl_require=True` est dans la configuration (déjà fait dans `settings.py`)

### Problème : "password authentication failed"

**Solution :**
1. Vérifiez que `DATABASE_URL` n'a pas été modifié manuellement
2. Si vous avez modifié le mot de passe PostgreSQL, Railway devrait mettre à jour `DATABASE_URL` automatiquement
3. Redéployez votre service Django après avoir modifié `DATABASE_URL`

### Problème : Le certificat SSL n'est pas valide

**Solution :**
1. Dans Railway, vérifiez la configuration du domaine
2. Railway gère automatiquement les certificats SSL via Let's Encrypt
3. Si nécessaire, supprimez et réajoutez le domaine

### Problème : Erreur 404 sur les nouvelles URLs

**Solution :**
1. Vérifiez que le domaine est bien configuré dans Railway
2. Vérifiez que le service est déployé et actif
3. Attendez quelques minutes pour la propagation DNS

### Problème : Erreur ALLOWED_HOSTS

**Solution :**
Vérifiez que le nouveau domaine est dans `DJANGO_ALLOWED_HOSTS` dans les variables d'environnement Railway.

---

## 📋 Checklist de Configuration

### Configuration de Base

- [ ] Service PostgreSQL créé sur Railway
- [ ] `DATABASE_URL` visible dans les variables du service Django (automatique)
- [ ] `DJANGO_SECRET_KEY` défini
- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_ALLOWED_HOSTS` inclut votre domaine Railway
- [ ] Migrations appliquées avec succès
- [ ] Connexion à la base de données testée et fonctionnelle
- [ ] Superutilisateur créé (si nécessaire)
- [ ] Fichiers statiques collectés

### Configuration Domaine

**Pour Option 1 (Domaine principal)**
- [ ] `comparateurdeprix.com` pointe vers le bon répertoire
- [ ] Certificat SSL installé pour `comparateurdeprix.com`
- [ ] Certificat SSL installé pour `www.comparateurdeprix.com`
- [ ] Domaine configuré sur Railway pour `comparateurdeprix.com`
- [ ] Variables d'environnement mises à jour avec les nouveaux domaines
- [ ] Application redéployée
- [ ] Test réussi : `https://comparateurdeprix.com/api/health/`

**Pour Option 2 (Sous-domaine API)**
- [ ] Sous-domaine `api.comparateurdeprix.com` créé
- [ ] Certificat SSL installé pour `api.comparateurdeprix.com`
- [ ] Domaine configuré sur Railway pour `api.comparateurdeprix.com`
- [ ] Variables d'environnement mises à jour avec le sous-domaine
- [ ] Application redéployée
- [ ] Test réussi : `https://api.comparateurdeprix.com/api/health/`

### Configuration Avancée

- [ ] Service Redis créé (si nécessaire)
- [ ] `REDIS_URL` configuré
- [ ] Variables Celery configurées (si nécessaire)
- [ ] Variables JWT configurées (si nécessaire)
- [ ] CORS configuré pour le frontend

---

## 🎯 Configuration Automatique

Votre application Django est déjà configurée pour utiliser `DATABASE_URL` automatiquement !

Dans `config/settings.py`, la configuration détecte automatiquement `DATABASE_URL` :

```python
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }
```

**Aucune configuration supplémentaire nécessaire !** Railway fait tout automatiquement.

---

## 📚 Ressources

- [Documentation Railway - Databases](https://docs.railway.app/databases/postgresql)
- [Documentation Railway - Variables](https://docs.railway.app/develop/variables)
- [Documentation Railway - Domains](https://docs.railway.app/develop/domains)
- [Guide de déploiement Railway](./DEPLOIEMENT_RAILWAY.md)
- [Guide de dépannage](./TROUBLESHOOTING.md)

---

## 💡 Conseils

1. **Ne modifiez jamais manuellement `DATABASE_URL`** - Railway le gère automatiquement
2. **Faites des sauvegardes régulières** - Utilisez Railway's backup feature
3. **Surveillez l'utilisation** - Railway affiche l'utilisation de la base de données dans le dashboard
4. **Utilisez les migrations** - Ne modifiez jamais directement la structure de la base de données
5. **Testez localement** - Utilisez les mêmes migrations en local et en production

---

*Dernière mise à jour : 2025-11-26*

