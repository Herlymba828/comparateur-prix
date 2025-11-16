# 🔐 Configuration des Variables d'Environnement sur Railway

## 🚨 Erreur actuelle

```
django.core.exceptions.ImproperlyConfigured: DJANGO_SECRET_KEY must be set in production
```

**Cause** : La variable d'environnement `DJANGO_SECRET_KEY` n'est pas configurée sur Railway.

---

## ✅ Solution : Configurer les variables d'environnement

### Étape 1 : Accéder aux variables d'environnement

1. Dans Railway, allez dans votre projet
2. Cliquez sur votre service Django
3. Allez dans l'onglet **"Variables"**

### Étape 2 : Ajouter les variables obligatoires

#### 1. DJANGO_SECRET_KEY (OBLIGATOIRE)

**Générer une clé secrète** :

```bash
# Sur votre machine locale
python -c "from secrets import token_urlsafe; print(token_urlsafe(50))"
```

**Ou utilisez cette clé** (générez-en une nouvelle pour la production) :
```
TmbjAfKjFXpor5UXwUbTN4Sna_JbwoXxwb_Clkgtv_ktJH2IOfhvMoAdfClV4eKiZKI
```

**Dans Railway** :
- **Variable** : `DJANGO_SECRET_KEY`
- **Valeur** : (collez la clé générée)

#### 2. DJANGO_DEBUG

- **Variable** : `DJANGO_DEBUG`
- **Valeur** : `False`

#### 3. DJANGO_ALLOWED_HOSTS

- **Variable** : `DJANGO_ALLOWED_HOSTS`
- **Valeur** : `votre-projet.railway.app,*.railway.app`

Pour trouver votre domaine Railway :
1. Dans Railway → votre service
2. Onglet **"Settings"**
3. Section **"Domains"** → notez votre domaine

---

### Étape 3 : Variables optionnelles mais recommandées

#### URLs

```bash
BACKEND_URL=https://votre-projet.railway.app
FRONTEND_URL=https://votre-frontend.com
SITE_URL=https://votre-projet.railway.app
PUBLIC_BASE_URL=https://votre-projet.railway.app
```

#### CORS (si vous avez un frontend)

```bash
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://votre-frontend.com,https://www.votre-frontend.com
```

#### CSRF

```bash
CSRF_TRUSTED_ORIGINS=https://votre-projet.railway.app,https://votre-frontend.com
```

---

## 📋 Checklist complète des variables

### Variables OBLIGATOIRES

- [ ] `DJANGO_SECRET_KEY` : Clé secrète générée
- [ ] `DJANGO_DEBUG` : `False`
- [ ] `DJANGO_ALLOWED_HOSTS` : Votre domaine Railway

### Variables automatiques (fournies par Railway)

- [x] `DATABASE_URL` : Automatiquement fourni par Railway PostgreSQL
- [x] `PORT` : Automatiquement fourni par Railway

### Variables optionnelles

- [ ] `BACKEND_URL` : URL de votre backend
- [ ] `FRONTEND_URL` : URL de votre frontend
- [ ] `SITE_URL` : URL du site
- [ ] `CORS_ALLOWED_ORIGINS` : Origines autorisées pour CORS
- [ ] `CSRF_TRUSTED_ORIGINS` : Origines de confiance pour CSRF

---

## 🔧 Configuration dans Railway

### Méthode 1 : Via l'interface web

1. **Railway** → Votre projet → Votre service
2. Onglet **"Variables"**
3. Cliquez sur **"+ New Variable"**
4. Ajoutez chaque variable :
   - **Name** : `DJANGO_SECRET_KEY`
   - **Value** : (votre clé)
5. Cliquez sur **"Add"**
6. Répétez pour toutes les variables

### Méthode 2 : Via Railway CLI

```bash
# Installer Railway CLI
npm i -g @railway/cli

# Se connecter
railway login

# Lier le projet
railway link

# Ajouter les variables
railway variables set DJANGO_SECRET_KEY="votre_clé_secrète"
railway variables set DJANGO_DEBUG="False"
railway variables set DJANGO_ALLOWED_HOSTS="votre-projet.railway.app,*.railway.app"
```

---

## 🚀 Après configuration

### 1. Redéployer

Railway redéploiera automatiquement après avoir ajouté les variables, ou :

```bash
# Via CLI
railway up
```

### 2. Vérifier les logs

Dans Railway → **Deployments** → **View Logs**, vous devriez voir :
- ✅ Application démarrée
- ✅ Pas d'erreur `DJANGO_SECRET_KEY`
- ✅ Connexion à PostgreSQL réussie

### 3. Tester l'application

- `https://votre-projet.railway.app/api/health/`
- `https://votre-projet.railway.app/api/docs/`

---

## 🔍 Vérification rapide

### Vérifier que les variables sont bien configurées

```bash
# Via Railway CLI
railway variables
```

Vous devriez voir :
- `DJANGO_SECRET_KEY` : (présent)
- `DJANGO_DEBUG` : `False`
- `DJANGO_ALLOWED_HOSTS` : (votre domaine)
- `DATABASE_URL` : (automatique, fourni par Railway)

---

## 🚨 Dépannage

### Erreur persiste après avoir ajouté les variables

1. **Vérifiez l'orthographe** : `DJANGO_SECRET_KEY` (pas `DJANGO_SECRET` ou autre)
2. **Redéployez manuellement** : Railway → Deployments → Redeploy
3. **Vérifiez les logs** : Railway → View Logs

### Comment trouver votre domaine Railway

1. Railway → Votre service
2. Onglet **"Settings"**
3. Section **"Domains"**
4. Copiez le domaine (ex: `votre-projet-production.up.railway.app`)

---

## 📝 Exemple complet de configuration

Voici un exemple de toutes les variables à configurer :

```bash
# Django (OBLIGATOIRE)
DJANGO_SECRET_KEY=TmbjAfKjFXpor5UXwUbTN4Sna_JbwoXxwb_Clkgtv_ktJH2IOfhvMoAdfClV4eKiZKI
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=votre-projet.railway.app,*.railway.app

# Database (automatique via Railway PostgreSQL)
# DATABASE_URL est automatiquement fourni par Railway

# URLs
BACKEND_URL=https://votre-projet.railway.app
FRONTEND_URL=https://votre-frontend.com
SITE_URL=https://votre-projet.railway.app
PUBLIC_BASE_URL=https://votre-projet.railway.app

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://votre-frontend.com,https://www.votre-frontend.com

# CSRF
CSRF_TRUSTED_ORIGINS=https://votre-projet.railway.app,https://votre-frontend.com

# JWT (si utilisé)
USE_JWT_AUTH=true
JWT_ALGORITHM=RS256

# Redis (si vous utilisez Celery)
# Créez un service Redis sur Railway, il fournira automatiquement REDIS_URL
```

---

## ✅ Checklist finale

- [ ] `DJANGO_SECRET_KEY` configuré
- [ ] `DJANGO_DEBUG=False` configuré
- [ ] `DJANGO_ALLOWED_HOSTS` configuré avec votre domaine Railway
- [ ] `DATABASE_URL` présent (automatique)
- [ ] Application redéployée
- [ ] Logs vérifiés (pas d'erreur)
- [ ] Application accessible : `/api/health/`

---

## 🎯 Résumé

**Problème** : `DJANGO_SECRET_KEY must be set in production`

**Solution** : Ajouter `DJANGO_SECRET_KEY` dans Railway → Variables

**Action immédiate** :
1. Railway → Votre service → Variables
2. Ajouter `DJANGO_SECRET_KEY` avec une clé générée
3. Ajouter `DJANGO_DEBUG=False`
4. Ajouter `DJANGO_ALLOWED_HOSTS` avec votre domaine Railway
5. Railway redéploiera automatiquement

Une fois ces variables ajoutées, l'application devrait démarrer correctement !

