# 🔧 Résolution : Erreur SSL avec Railway

## ❌ Erreur rencontrée

```
psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 5432 failed: server does not support SSL, but SSL was required
```

## 🔍 Cause du problème

1. **Connexion à localhost au lieu de Railway** : L'application essaie de se connecter à `127.0.0.1:5432` (votre machine locale) au lieu de la base de données Railway
2. **SSL forcé** : La configuration forçait SSL même pour les connexions locales qui ne supportent pas SSL

## ✅ Solutions

### Solution 1 : Vérifier que DATABASE_URL est défini (RECOMMANDÉ)

Quand vous utilisez `railway run`, Railway devrait automatiquement injecter `DATABASE_URL`. Vérifiez :

```bash
# Vérifier que DATABASE_URL est bien défini
railway run python scripts/check_railway_db.py
```

**Si DATABASE_URL n'est pas défini :**

1. Allez sur https://railway.app
2. Ouvrez votre projet
3. Cliquez sur le service **PostgreSQL**
4. Allez dans l'onglet **"Variables"**
5. Copiez la valeur de `DATABASE_URL`
6. Retournez dans votre service **Django**
7. Allez dans **"Variables"**
8. Ajoutez manuellement `DATABASE_URL` avec la valeur copiée

### Solution 2 : Utiliser Railway CLI correctement

Assurez-vous d'être dans le bon projet :

```bash
# Vérifier le projet actuel
railway status

# Si ce n'est pas le bon projet, lier le projet
railway link

# Vérifier les variables
railway variables | grep DATABASE_URL
```

### Solution 3 : Désactiver SSL pour localhost (si vous testez en local)

Si vous testez en local avec une base de données locale, ajoutez dans votre `.env` :

```bash
POSTGRES_SSL_REQUIRE=False
```

**Note :** Cette solution est seulement pour le développement local, pas pour Railway.

## 🔧 Corrections apportées au code

Le code a été mis à jour pour :

1. **Détecter automatiquement Railway** : SSL est requis seulement si l'URL contient "railway"
2. **Désactiver SSL pour localhost** : SSL est automatiquement désactivé pour les connexions locales
3. **Gérer les deux cas** : Railway (avec SSL) et local (sans SSL)

## 📋 Étapes pour résoudre

### Étape 1 : Vérifier la configuration Railway

```bash
# Exécuter le script de diagnostic
railway run python scripts/check_railway_db.py
```

### Étape 2 : Vérifier que PostgreSQL est créé

1. Allez sur Railway
2. Vérifiez que vous avez un service **PostgreSQL** dans votre projet
3. Si ce n'est pas le cas, créez-le : **"+ New"** → **"Database"** → **"Add PostgreSQL"**

### Étape 3 : Vérifier DATABASE_URL

```bash
# Voir toutes les variables
railway variables

# Voir spécifiquement DATABASE_URL
railway variables | grep DATABASE_URL
```

### Étape 4 : Appliquer les migrations

Une fois que `DATABASE_URL` est correctement configuré :

```bash
railway run python manage.py migrate
```

## 🎯 Configuration correcte

### Variables d'environnement Railway

Dans Railway → Votre service Django → Variables, vous devriez avoir :

```bash
# Automatique (fourni par Railway)
DATABASE_URL=postgresql://postgres:password@hostname.railway.internal:5432/railway

# Obligatoire
DJANGO_SECRET_KEY=votre_clé_secrète
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=comparo.up.railway.app,*.railway.app
```

### Format de DATABASE_URL Railway

Une URL Railway typique ressemble à :
```
postgresql://postgres:password@containers-us-west-xxx.railway.app:5432/railway
```

Ou :
```
postgresql://postgres:password@postgres.railway.internal:5432/railway
```

## 🆘 Dépannage supplémentaire

### Problème : "DATABASE_URL not found"

**Solution :**
1. Vérifiez que PostgreSQL est dans le même projet Railway
2. Railway partage automatiquement `DATABASE_URL` entre services du même projet
3. Si nécessaire, copiez manuellement `DATABASE_URL` depuis PostgreSQL vers Django

### Problème : Toujours connecté à localhost

**Solution :**
1. Vérifiez que vous n'avez pas de `.env` local qui surcharge `DATABASE_URL`
2. Vérifiez que `DJANGO_DEBUG=False` (en production, utilise PostgreSQL)
3. Utilisez `railway run` pour exécuter les commandes avec les variables Railway

### Problème : "Connection refused"

**Solution :**
1. Vérifiez que le service PostgreSQL est démarré (pas en pause)
2. Vérifiez que `DATABASE_URL` est correct
3. Vérifiez les logs Railway pour plus de détails

## ✅ Vérification finale

Après avoir appliqué les corrections :

```bash
# 1. Vérifier la configuration
railway run python scripts/check_railway_db.py

# 2. Tester la connexion
railway run python manage.py dbshell

# 3. Appliquer les migrations
railway run python manage.py migrate

# 4. Vérifier que tout fonctionne
railway run python manage.py check --deploy
```

## 📚 Ressources

- [Documentation Railway - Databases](https://docs.railway.app/databases/postgresql)
- [Documentation Railway - Variables](https://docs.railway.app/develop/variables)
- [Guide Configuration Base de Données Railway](./CONFIGURATION_DATABASE_RAILWAY.md)

---

**Besoin d'aide ?** Exécutez `railway run python scripts/check_railway_db.py` pour un diagnostic complet.

