# 🚀 Guide Rapide : Configuration Railway

Guide étape par étape pour configurer votre application Django sur Railway en 5 minutes.

---

## ⚡ Démarrage Rapide

### 1️⃣ Créer le service PostgreSQL (2 minutes)

1. Allez sur https://railway.app
2. Ouvrez votre projet
3. Cliquez sur **"+ New"** → **"Database"** → **"Add PostgreSQL"**
4. Attendez 1-2 minutes que Railway crée la base de données

✅ **C'est tout !** Railway configure automatiquement `DATABASE_URL`.

---

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

---

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

---

### 4️⃣ Vérifier que tout fonctionne

1. Allez sur `https://comparo.up.railway.app/api/health/`
2. Vous devriez voir : `{"status": "ok"}`

✅ **Terminé !** Votre application est configurée.

---

## 📋 Checklist Complète

- [ ] Service PostgreSQL créé
- [ ] `DATABASE_URL` visible dans les variables (automatique)
- [ ] `DJANGO_SECRET_KEY` défini
- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_ALLOWED_HOSTS` configuré
- [ ] Migrations appliquées
- [ ] Application accessible sur `https://comparo.up.railway.app`

---

## 🔧 Configuration Avancée

### Ajouter Redis (pour Celery/Cache)

1. Dans Railway, cliquez sur **"+ New"** → **"Database"** → **"Add Redis"**
2. Railway configure automatiquement `REDIS_URL`
3. Ajoutez dans les variables :
   ```bash
   CELERY_BROKER_URL=${REDIS_URL}
   CELERY_RESULT_BACKEND=${REDIS_URL}
   ```

### Créer un superutilisateur

```bash
railway run python manage.py createsuperuser
```

### Voir les logs

```bash
railway logs
```

---

## 🆘 Problèmes Courants

### "DATABASE_URL not found"
→ Vérifiez que PostgreSQL est créé dans le même projet

### "Connection refused"
→ Vérifiez que PostgreSQL n'est pas en pause

### "Table does not exist"
→ Exécutez : `railway run python manage.py migrate`

---

## 📚 Documentation Complète

Pour plus de détails, consultez :
- [Configuration Base de Données Railway](./CONFIGURATION_DATABASE_RAILWAY.md)
- [Configuration Redis et Base de Données](./CONFIGURATION_REDIS_DATABASE.md)
- [Déploiement Railway](./DEPLOIEMENT_RAILWAY.md)

---

**Besoin d'aide ?** Vérifiez les logs Railway ou consultez la documentation complète.

