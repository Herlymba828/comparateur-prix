# 🔴 Guide Rapide : Configuration Redis

Guide étape par étape pour configurer Redis sur Railway en 3 minutes.

---

## ⚡ Configuration sur Railway

### 1️⃣ Ajouter le service Redis (1 minute)

1. Allez sur https://railway.app
2. Ouvrez votre projet
3. Cliquez sur **"+ New"** → **"Database"** → **"Add Redis"**
4. Attendez 1-2 minutes que Railway crée l'instance Redis

✅ **C'est tout !** Railway configure automatiquement `REDIS_URL`.

---

### 2️⃣ Vérifier la configuration (30 secondes)

1. Dans Railway → Votre service Django → **Variables**
2. Cherchez `REDIS_URL`
3. Vous devriez voir : `redis://default:password@redis.railway.internal:6379`

**Note :** Railway ajoute automatiquement `REDIS_URL` à votre service Django.

---

### 3️⃣ Redéployer (1 minute)

Railway redéploiera automatiquement votre application, ou :

```bash
railway up
```

---

## ✅ Vérification

### Tester la connexion Redis

**Via Railway CLI :**
```bash
railway run python -c "import redis; import os; r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0')); print('✅ Redis connecté!' if r.ping() else '❌ Erreur')"
```

### Tester Celery

```bash
railway run celery -A config inspect ping
```

---

## 🔧 Configuration locale (développement)

### Installer Redis

**Windows :**
1. Téléchargez depuis https://github.com/microsoftarchive/redis/releases
2. Installez et démarrez Redis
3. Ou utilisez WSL : `sudo apt install redis-server`

**Linux/macOS :**
```bash
# Linux
sudo apt install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis
```

### Configuration dans .env

```bash
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_URL=redis://127.0.0.1:6379/1
```

---

## 📋 Checklist

- [ ] Service Redis créé dans Railway
- [ ] `REDIS_URL` visible dans les variables d'environnement
- [ ] Application redéployée
- [ ] Connexion Redis vérifiée

---

## 🎯 Résumé

1. **Créer Redis** : Railway → "+ New" → "Database" → "Add Redis"
2. **Vérifier** : `REDIS_URL` est automatiquement ajouté
3. **Redéployer** : Railway le fait automatiquement

**Votre application utilise Redis automatiquement !** 🎉

---

## 📚 Documentation complète

Pour plus de détails, consultez :
- `docs/CONFIGURATION_REDIS_RAILWAY.md` - Guide complet
- `docs/CONFIGURATION_REDIS_DATABASE.md` - Configuration générale

