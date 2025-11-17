# 🗄️ Configuration de la Base de Données sur Railway

Guide complet pour configurer PostgreSQL sur Railway pour votre application Django Comparateur de Prix.

---

## 📋 Table des matières

1. [Créer le service PostgreSQL](#créer-le-service-postgresql)
2. [Vérifier DATABASE_URL](#vérifier-database_url)
3. [Configurer les variables d'environnement](#configurer-les-variables-denvironnement)
4. [Appliquer les migrations](#appliquer-les-migrations)
5. [Vérifier la connexion](#vérifier-la-connexion)
6. [Dépannage](#dépannage)

---

## 🚀 Étape 1 : Créer le service PostgreSQL

### Méthode 1 : Via l'interface Railway (Recommandé)

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

### Méthode 2 : Via Railway CLI

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

---

## ✅ Étape 2 : Vérifier DATABASE_URL

Railway configure automatiquement `DATABASE_URL` pour votre service Django.

### Vérification via l'interface Railway

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

### Vérification via Railway CLI

```bash
# Voir toutes les variables d'environnement
railway variables

# Voir spécifiquement DATABASE_URL
railway variables | grep DATABASE_URL
```

---

## ⚙️ Étape 3 : Configurer les variables d'environnement

### Variables obligatoires

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

# CORS (si vous avez un frontend)
CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com
CSRF_TRUSTED_ORIGINS=https://comparo.up.railway.app,https://comparateurdeprix.com
```

### Variables optionnelles (mais recommandées)

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
```

### Comment ajouter des variables

1. **Via l'interface Railway**
   - Allez dans votre service Django
   - Cliquez sur l'onglet **"Variables"**
   - Cliquez sur **"+ New Variable"**
   - Entrez le nom et la valeur
   - Cliquez sur **"Add"**

2. **Via Railway CLI**
   ```bash
   # Ajouter une variable
   railway variables set DJANGO_SECRET_KEY=votre_clé
   
   # Voir toutes les variables
   railway variables
   ```

---

## 🔄 Étape 4 : Appliquer les migrations

Une fois que `DATABASE_URL` est configuré, vous devez créer les tables dans la base de données.

### Méthode 1 : Via Railway CLI (Recommandé)

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

### Méthode 2 : Via l'interface Railway

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

### Méthode 3 : Via le service Railway (Automatique)

Vous pouvez configurer Railway pour exécuter automatiquement les migrations au démarrage.

**Créez un fichier `railway.json` à la racine :**

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

**Ou créez un script de démarrage `start.sh` :**

```bash
#!/bin/bash
set -e

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting server..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

Puis dans Railway → Variables, ajoutez :
```
RAILWAY_START_COMMAND=./start.sh
```

---

## ✅ Étape 5 : Vérifier la connexion

### Test 1 : Via Railway CLI

```bash
# Tester la connexion à la base de données
railway run python manage.py dbshell

# Si ça fonctionne, vous verrez le prompt PostgreSQL
# Tapez \q pour quitter
```

### Test 2 : Via l'interface Railway

1. **Voir les logs**
   - Allez dans votre service Django
   - Cliquez sur **"View Logs"**
   - Cherchez les messages de connexion à la base de données
   - Vous devriez voir : `✅ Connected to database`

2. **Tester l'API**
   - Allez sur `https://comparo.up.railway.app/api/health/`
   - Si la réponse est `{"status": "ok"}`, tout fonctionne !

### Test 3 : Via Python

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

### Problème : Migrations ne s'appliquent pas

**Solutions :**
1. Vérifiez que vous êtes dans le bon projet Railway
2. Vérifiez que `DATABASE_URL` est bien défini
3. Vérifiez les logs pour voir les erreurs exactes
4. Essayez de forcer les migrations :
   ```bash
   railway run python manage.py migrate --run-syncdb
   ```

---

## 📊 Vérification complète

### Checklist de configuration

- [ ] Service PostgreSQL créé sur Railway
- [ ] `DATABASE_URL` visible dans les variables du service Django
- [ ] `DJANGO_SECRET_KEY` défini
- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_ALLOWED_HOSTS` inclut votre domaine Railway
- [ ] Migrations appliquées avec succès
- [ ] Connexion à la base de données testée et fonctionnelle
- [ ] Superutilisateur créé (si nécessaire)
- [ ] Fichiers statiques collectés

### Commandes de vérification rapide

```bash
# Vérifier les variables d'environnement
railway variables

# Vérifier la connexion
railway run python manage.py dbshell

# Vérifier les migrations
railway run python manage.py showmigrations

# Vérifier la configuration Django
railway run python manage.py check --deploy
```

---

## 🎯 Configuration automatique

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

## 📚 Ressources supplémentaires

- [Documentation Railway - Databases](https://docs.railway.app/databases/postgresql)
- [Documentation Railway - Variables](https://docs.railway.app/develop/variables)
- [Documentation Django - Database](https://docs.djangoproject.com/en/stable/ref/databases/)
- [Documentation dj-database-url](https://github.com/jacobian/dj-database-url)

---

## 💡 Conseils

1. **Ne modifiez jamais manuellement `DATABASE_URL`** - Railway le gère automatiquement
2. **Faites des sauvegardes régulières** - Utilisez Railway's backup feature
3. **Surveillez l'utilisation** - Railway affiche l'utilisation de la base de données dans le dashboard
4. **Utilisez les migrations** - Ne modifiez jamais directement la structure de la base de données
5. **Testez localement** - Utilisez les mêmes migrations en local et en production

---

**Besoin d'aide ?** Consultez les autres documents dans le dossier `docs/` ou ouvrez une issue.

