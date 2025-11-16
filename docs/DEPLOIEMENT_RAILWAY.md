# 🚂 Guide de Déploiement sur Railway

Ce guide explique comment déployer votre application Django sur Railway avec PostgreSQL.

---

## 🚨 Problème résolu

**Erreur** : `connection to server at "127.0.0.1", port 5432 failed: Connection refused`

**Cause** : Django cherchait PostgreSQL sur localhost, mais Railway fournit PostgreSQL via un service externe avec `DATABASE_URL`.

**Solution** : Configuration mise à jour pour utiliser `DATABASE_URL` en priorité (Railway) avec fallback sur les variables individuelles (cPanel/local).

---

## 📋 Prérequis

1. Compte Railway : https://railway.app
2. Projet Django configuré
3. Git repository

---

## 🚀 Étapes de déploiement

### Étape 1 : Préparer le projet

#### 1.1 Ajouter les fichiers nécessaires

**Procfile** (à la racine du projet) :
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A config worker -l info
beat: celery -A config beat -l info
```

**runtime.txt** (si pas déjà présent) :
```
python-3.11.0
```

**railway.json** (optionnel, pour la configuration Railway) :
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn config.wsgi:application --bind 0.0.0.0:$PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

#### 1.2 Mettre à jour requirements.txt

Assurez-vous que `dj-database-url` est présent :
```txt
dj-database-url==2.1.0
gunicorn==21.2.0
```

---

### Étape 2 : Créer le projet sur Railway

1. Allez sur https://railway.app
2. Cliquez sur **"New Project"**
3. Sélectionnez **"Deploy from GitHub repo"** (ou uploader directement)
4. Connectez votre repository GitHub
5. Sélectionnez votre projet

---

### Étape 3 : Ajouter PostgreSQL

1. Dans votre projet Railway, cliquez sur **"+ New"**
2. Sélectionnez **"Database"** → **"Add PostgreSQL"**
3. Railway créera automatiquement une base de données PostgreSQL
4. Railway fournira automatiquement la variable `DATABASE_URL`

---

### Étape 4 : Configurer les variables d'environnement

Dans Railway → **Variables**, ajoutez :

#### Variables obligatoires

```bash
# Django
DJANGO_SECRET_KEY=votre_clé_secrète_forte
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=votre-domaine.railway.app,*.railway.app

# Database (automatique via DATABASE_URL fourni par Railway)
# DATABASE_URL est automatiquement fourni par Railway

# Redis (si vous utilisez Celery)
REDIS_URL=redis://default:password@redis.railway.internal:6379
# Ou créez un service Redis sur Railway

# URLs
BACKEND_URL=https://votre-domaine.railway.app
FRONTEND_URL=https://votre-frontend.com
SITE_URL=https://votre-domaine.railway.app
```

#### Variables optionnelles

```bash
# CORS
CORS_ALLOWED_ORIGINS=https://votre-frontend.com,https://www.votre-frontend.com

# JWT
USE_JWT_AUTH=true
JWT_ALGORITHM=RS256
JWT_PRIVATE_KEY_PATH=secrets/jwt_private.pem
JWT_PUBLIC_KEY_PATH=secrets/jwt_public.pem

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

---

### Étape 5 : Déployer

1. Railway détectera automatiquement que c'est un projet Django
2. Il installera les dépendances depuis `requirements.txt`
3. Il lancera l'application avec la commande du Procfile

---

### Étape 6 : Appliquer les migrations

Une fois déployé, dans Railway → **Deployments** → Cliquez sur votre service → **"View Logs"**, ou utilisez Railway CLI :

```bash
# Installer Railway CLI
npm i -g @railway/cli

# Se connecter
railway login

# Lier le projet
railway link

# Appliquer les migrations
railway run python manage.py migrate

# Créer un superutilisateur
railway run python manage.py createsuperuser

# Collecter les fichiers statiques
railway run python manage.py collectstatic --noinput
```

---

## 🔍 Vérification

### Vérifier la connexion à la base de données

```bash
railway run python manage.py dbshell
```

Si ça fonctionne, la connexion est correcte !

### Vérifier les logs

Dans Railway → **Deployments** → **View Logs**, vous devriez voir :
- ✅ Application démarrée
- ✅ Connexion à PostgreSQL réussie
- ✅ Pas d'erreur de connexion

---

## 🚨 Dépannage

### Erreur : "Connection refused"

**Cause** : `DATABASE_URL` n'est pas configuré ou incorrect.

**Solution** :
1. Vérifiez que PostgreSQL est ajouté dans Railway
2. Vérifiez que `DATABASE_URL` est présent dans les variables d'environnement
3. Railway le fournit automatiquement, ne le modifiez pas manuellement

### Erreur : "Module not found"

**Solution** :
```bash
# Vérifier que toutes les dépendances sont dans requirements.txt
railway run pip list
```

### Erreur : "ALLOWED_HOSTS"

**Solution** :
Ajoutez votre domaine Railway dans `DJANGO_ALLOWED_HOSTS` :
```bash
DJANGO_ALLOWED_HOSTS=votre-domaine.railway.app,*.railway.app
```

### Erreur : "Static files not found"

**Solution** :
```bash
# Collecter les fichiers statiques
railway run python manage.py collectstatic --noinput

# Ou utiliser WhiteNoise (recommandé pour Railway)
# Ajoutez dans settings.py :
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## 📊 Configuration recommandée

### WhiteNoise pour les fichiers statiques

Ajoutez dans `config/settings.py` :

```python
# Middleware (ajouter en premier)
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Ajouter ici
    'django.middleware.security.SecurityMiddleware',
    # ... reste du middleware
]

# Configuration WhiteNoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

Ajoutez dans `requirements.txt` :
```
whitenoise==6.6.0
```

### Redis pour Celery

1. Dans Railway, ajoutez un service **Redis**
2. Railway fournira automatiquement `REDIS_URL`
3. Utilisez cette URL pour Celery

---

## 🔄 Workflow de déploiement

1. **Push vers GitHub** :
   ```bash
   git add .
   git commit -m "Mise à jour"
   git push origin main
   ```

2. **Railway déploie automatiquement**

3. **Vérifier les logs** dans Railway

4. **Tester l'application** :
   - `https://votre-domaine.railway.app/api/health/`
   - `https://votre-domaine.railway.app/api/docs/`

---

## 📋 Checklist

- [ ] ✅ `dj-database-url` dans `requirements.txt`
- [ ] ✅ `Procfile` créé
- [ ] ✅ `runtime.txt` créé (optionnel)
- [ ] ✅ Projet créé sur Railway
- [ ] ✅ PostgreSQL ajouté
- [ ] ✅ Variables d'environnement configurées
- [ ] ✅ `DATABASE_URL` présent (automatique)
- [ ] ✅ Migrations appliquées
- [ ] ✅ Superutilisateur créé
- [ ] ✅ Application accessible
- [ ] ✅ Tests passent

---

## 🎯 Résumé

**Configuration automatique** :
- ✅ `DATABASE_URL` est utilisé en priorité (Railway)
- ✅ Fallback sur variables individuelles (cPanel/local)
- ✅ Support PostgreSQL et MySQL
- ✅ Configuration SSL automatique

**Railway fournit automatiquement** :
- `DATABASE_URL` : URL complète de connexion PostgreSQL
- `PORT` : Port pour l'application
- Variables d'environnement du service

**Vous devez configurer** :
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_DEBUG=False`
- Autres variables spécifiques à votre application

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs dans Railway
2. Vérifiez que `DATABASE_URL` est présent
3. Vérifiez les variables d'environnement
4. Consultez la documentation Railway : https://docs.railway.app

