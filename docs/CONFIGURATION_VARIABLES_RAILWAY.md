# Configuration des Variables d'Environnement sur Railway

Ce guide explique comment configurer les variables d'environnement nécessaires pour que votre application Django fonctionne correctement sur Railway.

## 🔴 Problème Courant : "connection to server at 127.0.0.1:5432 failed"

Si vous voyez cette erreur, cela signifie que `DATABASE_URL` ou `DATABASE_PUBLIC_URL` ne sont pas définies dans votre service Django sur Railway.

---

## ✅ Solution : Configurer les Variables d'Environnement

### Étape 1 : Vérifier les Variables Automatiques de Railway

Railway configure automatiquement certaines variables quand vous créez un service PostgreSQL :

1. **Allez dans votre projet Railway**
2. **Ouvrez votre service PostgreSQL**
3. **Cliquez sur l'onglet "Variables"**
4. **Notez les valeurs de :**
   - `DATABASE_URL` (URL interne Railway)
   - `DATABASE_PUBLIC_URL` (URL publique accessible depuis l'extérieur)

### Étape 2 : Ajouter les Variables au Service Django

1. **Allez dans votre service Django** (pas PostgreSQL)
2. **Cliquez sur l'onglet "Variables"**
3. **Vérifiez si `DATABASE_URL` ou `DATABASE_PUBLIC_URL` sont présentes**

#### Si elles sont absentes :

**Option A : Via l'Interface Railway (Recommandé)**

1. Dans le service PostgreSQL, copiez la valeur de `DATABASE_PUBLIC_URL`
2. Dans le service Django, cliquez sur **"+ New Variable"**
3. Nom : `DATABASE_PUBLIC_URL`
4. Valeur : Collez la valeur copiée
5. Cliquez sur **"Add"**
6. Répétez pour `DATABASE_URL` si nécessaire

**Option B : Via Railway CLI**

```bash
# Installer Railway CLI si nécessaire
npm i -g @railway/cli

# Se connecter
railway login

# Lier le projet
railway link

# Lister les services
railway service

# Ajouter DATABASE_PUBLIC_URL (remplacez <value> par la vraie valeur)
railway variables set DATABASE_PUBLIC_URL="<value>" --service <service-django-id>

# Ajouter DATABASE_URL (remplacez <value> par la vraie valeur)
railway variables set DATABASE_URL="<value>" --service <service-django-id>
```

---

## 📋 Variables Requises pour Railway

### Variables Obligatoires

| Variable | Description | Où la trouver |
|----------|-------------|---------------|
| `DATABASE_PUBLIC_URL` | URL publique PostgreSQL Railway | Service PostgreSQL → Variables |
| `DATABASE_URL` | URL interne PostgreSQL Railway | Service PostgreSQL → Variables |
| `DJANGO_SECRET_KEY` | Clé secrète Django | À générer |
| `DJANGO_DEBUG` | Mode debug (False en production) | `False` |

### Variables Optionnelles mais Recommandées

| Variable | Description | Valeur recommandée |
|----------|-------------|-------------------|
| `REDIS_PUBLIC_URL` | URL publique Redis Railway | Service Redis → Variables |
| `REDIS_URL` | URL interne Redis Railway | Service Redis → Variables |
| `DJANGO_ALLOWED_HOSTS` | Domaines autorisés | `comparo.up.railway.app,*.railway.app` |
| `SITE_URL` | URL du site | `https://comparo.up.railway.app` |

---

## 🔧 Configuration Complète

### 1. Variables de Base de Données

**Depuis le service PostgreSQL Railway :**

```bash
DATABASE_PUBLIC_URL=postgresql://postgres:password@shuttle.proxy.rlwy.net:PORT/database
DATABASE_URL=postgresql://postgres:password@postgres.railway.internal:5432/database
```

**À ajouter dans le service Django Railway.**

### 2. Variables Django

```bash
DJANGO_SECRET_KEY=<générer avec: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=comparo.up.railway.app,*.railway.app
```

### 3. Variables Redis (si vous utilisez Redis)

**Depuis le service Redis Railway :**

```bash
REDIS_PUBLIC_URL=redis://default:password@switchback.proxy.rlwy.net:PORT
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

**À ajouter dans le service Django Railway.**

---

## 🚀 Vérification

### 1. Vérifier les Variables

```bash
# Via Railway CLI
railway variables

# Vérifier qu'au moins DATABASE_PUBLIC_URL ou DATABASE_URL est défini
```

### 2. Tester la Connexion

```bash
# Via Railway CLI
railway run python manage.py dbshell

# Si ça fonctionne, vous verrez le prompt PostgreSQL
# Tapez \q pour quitter
```

### 3. Appliquer les Migrations

```bash
# Via Railway CLI
railway run python manage.py migrate
```

---

## 🔍 Dépannage

### Problème : "DATABASE_URL not found"

**Solution :**
1. Vérifiez que le service PostgreSQL est bien créé
2. Vérifiez que les services sont dans le même projet Railway
3. Railway devrait automatiquement partager `DATABASE_URL`, mais si ce n'est pas le cas :
   - Copiez manuellement `DATABASE_PUBLIC_URL` depuis le service PostgreSQL
   - Ajoutez-la dans le service Django

### Problème : "connection to server at 127.0.0.1:5432 failed"

**Cause :** `DATABASE_URL` ou `DATABASE_PUBLIC_URL` ne sont pas définies.

**Solution :**
1. Allez dans le service PostgreSQL Railway
2. Copiez `DATABASE_PUBLIC_URL`
3. Allez dans le service Django Railway
4. Ajoutez la variable `DATABASE_PUBLIC_URL` avec la valeur copiée
5. Redéployez le service Django

### Problème : "relation does not exist"

**Solution :**
```bash
# Appliquer les migrations
railway run python manage.py migrate
```

---

## 📝 Checklist de Configuration

- [ ] Service PostgreSQL créé sur Railway
- [ ] `DATABASE_PUBLIC_URL` copiée depuis PostgreSQL vers Django
- [ ] `DATABASE_URL` copiée depuis PostgreSQL vers Django (optionnel, mais recommandé)
- [ ] `DJANGO_SECRET_KEY` défini
- [ ] `DJANGO_DEBUG=False` défini
- [ ] `DJANGO_ALLOWED_HOSTS` configuré
- [ ] `REDIS_PUBLIC_URL` et `REDIS_URL` configurés (si Redis est utilisé)
- [ ] Migrations appliquées avec succès
- [ ] Application accessible et fonctionnelle

---

## 💡 Astuce : Variables Partagées Automatiquement

Railway partage automatiquement certaines variables entre services du même projet :

- `DATABASE_URL` (si service PostgreSQL présent)
- `REDIS_URL` (si service Redis présent)

Cependant, `DATABASE_PUBLIC_URL` et `REDIS_PUBLIC_URL` ne sont **pas** partagées automatiquement. Vous devez les copier manuellement.

---

## 🔗 Ressources

- [Documentation Railway - Variables d'environnement](https://docs.railway.app/develop/variables)
- [Documentation Railway - Services](https://docs.railway.app/develop/services)
- [Guide de déploiement Railway](./DEPLOIEMENT_RAILWAY.md)
