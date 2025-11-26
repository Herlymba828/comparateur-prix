# 🔧 Guide de Configuration : Redis et Base de Données

Ce guide vous explique comment configurer Redis et la base de données pour votre application Django Comparateur de Prix.

---

## 📋 Table des matières

1. [Configuration de la Base de Données](#configuration-de-la-base-de-données)
   - [PostgreSQL (Recommandé)](#postgresql-recommandé)
   - [MySQL/MariaDB](#mysqlmariadb)
   - [SQLite (Développement uniquement)](#sqlite-développement-uniquement)
2. [Configuration de Redis](#configuration-de-redis)
   - [Installation locale](#installation-locale)
   - [Configuration pour Railway](#configuration-pour-railway)
   - [Configuration pour cPanel](#configuration-pour-cpanel)
3. [Configuration des Variables d'Environnement](#configuration-des-variables-denvironnement)
4. [Vérification de la Configuration](#vérification-de-la-configuration)
5. [Dépannage](#dépannage)

---

## 🗄️ Configuration de la Base de Données

### PostgreSQL (Recommandé)

PostgreSQL est la base de données recommandée pour la production.

#### Option 1 : Utilisation de DATABASE_URL (Railway, Heroku, etc.)

Si vous utilisez Railway, Heroku ou un service similaire, `DATABASE_URL` est automatiquement fourni.

**Aucune configuration supplémentaire nécessaire !** L'application détecte automatiquement `DATABASE_URL`.

#### Option 2 : Configuration manuelle avec variables individuelles

Ajoutez ces variables dans votre fichier `.env` :

```bash
# Type de base de données
DB_ENGINE=postgresql

# Informations de connexion PostgreSQL
DB_NAME=comparateur_prix
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# Ou utilisez les variables PostgreSQL standard
POSTGRES_DB=comparateur_prix
POSTGRES_USER=postgres
POSTGRES_PASSWORD=votre_mot_de_passe
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# SSL (recommandé en production)
POSTGRES_SSL_REQUIRE=True
```

#### Installation PostgreSQL locale

**Sur Windows :**
1. Téléchargez PostgreSQL depuis [postgresql.org](https://www.postgresql.org/download/windows/)
2. Installez PostgreSQL avec l'installateur
3. Notez le mot de passe du superutilisateur `postgres`
4. Créez une base de données :
   ```sql
   CREATE DATABASE comparateur_prix;
   CREATE USER votre_utilisateur WITH PASSWORD 'votre_mot_de_passe';
   GRANT ALL PRIVILEGES ON DATABASE comparateur_prix TO votre_utilisateur;
   ```

**Sur Linux (Ubuntu/Debian) :**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib

# Démarrer PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Créer une base de données
sudo -u postgres psql
CREATE DATABASE comparateur_prix;
CREATE USER votre_utilisateur WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE comparateur_prix TO votre_utilisateur;
\q
```

**Sur macOS :**
```bash
brew install postgresql
brew services start postgresql

# Créer une base de données
createdb comparateur_prix
```

---

### MySQL/MariaDB

Si vous préférez utiliser MySQL/MariaDB :

```bash
# Type de base de données
DB_ENGINE=mysql

# Informations de connexion MySQL
DB_NAME=comparateur_prix
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=3306

# Ou utilisez les variables MySQL standard
MYSQL_DB=comparateur_prix
MYSQL_USER=root
MYSQL_PASSWORD=votre_mot_de_passe
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

#### Installation MySQL/MariaDB locale

**Sur Windows :**
1. Téléchargez MySQL depuis [mysql.com](https://dev.mysql.com/downloads/installer/)
2. Ou installez XAMPP qui inclut MySQL

**Sur Linux :**
```bash
# MySQL
sudo apt install mysql-server
sudo mysql_secure_installation

# MariaDB
sudo apt install mariadb-server
sudo mysql_secure_installation

# Créer une base de données
sudo mysql -u root -p
CREATE DATABASE comparateur_prix;
CREATE USER 'votre_utilisateur'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON comparateur_prix.* TO 'votre_utilisateur'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

**Sur macOS :**
```bash
brew install mysql
brew services start mysql

# Créer une base de données
mysql -u root -p
CREATE DATABASE comparateur_prix;
CREATE USER 'votre_utilisateur'@'localhost' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON comparateur_prix.* TO 'votre_utilisateur'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

---

### SQLite (Développement uniquement)

SQLite est utilisé automatiquement en mode développement (`DEBUG=True`). Aucune configuration nécessaire !

**Note :** SQLite n'est pas recommandé pour la production.

---

## 🔴 Configuration de Redis

Redis est utilisé pour :
- Le cache Django
- Les sessions
- Celery (tâches asynchrones)

### Installation locale

#### Windows

**Option 1 : WSL2 (Recommandé)**
```bash
# Dans WSL2
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Option 2 : Memurai (Alternative Windows native)**
1. Téléchargez depuis [memurai.com](https://www.memurai.com/)
2. Installez et démarrez le service

**Option 3 : Docker**
```bash
docker run -d -p 6379:6379 redis:latest
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install redis-server

# Démarrer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérifier que Redis fonctionne
redis-cli ping
# Devrait répondre: PONG
```

#### macOS

```bash
brew install redis
brew services start redis

# Vérifier que Redis fonctionne
redis-cli ping
# Devrait répondre: PONG
```

### Configuration pour Railway

1. **Ajoutez un service Redis dans Railway :**
   - Allez dans votre projet Railway
   - Cliquez sur **"+ New"** → **"Database"** → **"Add Redis"**
   - Railway configure automatiquement `REDIS_URL`

2. **Vérifiez les variables d'environnement :**
   - Railway fournit automatiquement `REDIS_URL`
   - Aucune configuration supplémentaire nécessaire !

### Configuration pour développement local

Si Redis est installé localement :

```bash
# Dans votre fichier .env
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_URL=redis://127.0.0.1:6379/1
REDIS_PASSWORD=  # Laissez vide si pas de mot de passe
```

**Note :** Assurez-vous que Redis est démarré localement.

### Configuration avec mot de passe

Si votre Redis nécessite un mot de passe :

```bash
# Format de l'URL Redis avec mot de passe
REDIS_URL=redis://:votre_mot_de_passe@localhost:6379/0

# Ou utilisez REDIS_PASSWORD séparément
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=votre_mot_de_passe
```

---

## ⚙️ Configuration des Variables d'Environnement

Créez ou modifiez votre fichier `.env` à la racine du projet :

### Configuration complète pour développement local

```bash
# ============================================
# BASE DE DONNÉES
# ============================================
# Option 1 : PostgreSQL (recommandé)
DB_ENGINE=postgresql
DB_NAME=comparateur_prix
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# Option 2 : MySQL/MariaDB
# DB_ENGINE=mysql
# DB_NAME=comparateur_prix
# DB_USER=root
# DB_PASSWORD=votre_mot_de_passe
# DB_HOST=localhost
# DB_PORT=3306

# ============================================
# REDIS
# ============================================
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_URL=redis://127.0.0.1:6379/1
REDIS_PASSWORD=

# ============================================
# CELERY (utilise Redis)
# ============================================
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
```

### Configuration pour Railway (Production)

Railway configure automatiquement `DATABASE_URL` et `REDIS_URL`. Vous pouvez ajouter :

```bash
# Railway fournit automatiquement :
# - DATABASE_URL
# - REDIS_URL (si vous avez ajouté un service Redis)

# Vous pouvez surcharger avec :
REDIS_CACHE_URL=${REDIS_URL}  # Utiliser la même instance Redis
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}
```

### Configuration pour développement local (Production-like)

```bash
# ============================================
# BASE DE DONNÉES
# ============================================
DB_ENGINE=postgresql
DB_NAME=comparateur_prix
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432

# ============================================
# REDIS
# ============================================
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_URL=redis://127.0.0.1:6379/1
```

---

## ✅ Vérification de la Configuration

### 1. Vérifier la connexion à la base de données

```bash
# Tester la connexion PostgreSQL
python manage.py dbshell

# Ou avec psql directement
psql -U votre_utilisateur -d comparateur_prix -h localhost
```

### 2. Vérifier Redis

```bash
# Tester Redis
redis-cli ping
# Devrait répondre: PONG

# Ou depuis Python
python manage.py shell
>>> import redis
>>> r = redis.from_url('redis://localhost:6379/0')
>>> r.ping()
True
```

### 3. Vérifier la configuration Django

```bash
# Vérifier les paramètres de production
python manage.py check --deploy

# Tester la connexion depuis Django
python manage.py shell
>>> from django.db import connection
>>> connection.ensure_connection()
>>> print("✅ Connexion à la base de données réussie!")
```

### 4. Appliquer les migrations

```bash
# Créer les tables dans la base de données
python manage.py migrate

# Si c'est une nouvelle installation, créez un superutilisateur
python manage.py createsuperuser
```

### 5. Tester Celery (si configuré)

```bash
# Démarrer Celery worker
celery -A config worker -l info

# Dans un autre terminal, tester une tâche
python manage.py shell
>>> from apps.produits.tasks import test_task  # Exemple
>>> test_task.delay()
```

---

## 🔍 Dépannage

### Problème : "fe_sendauth: no password supplied"

**Solution :** Vérifiez que `DB_PASSWORD` ou `POSTGRES_PASSWORD` est défini dans votre `.env`.

```bash
# Vérifier les variables d'environnement
python manage.py shell -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DB_PASSWORD:', 'défini' if os.getenv('DB_PASSWORD') else 'non défini')"
```

### Problème : "Connection refused" pour Redis

**Solutions :**
1. Vérifiez que Redis est démarré :
   ```bash
   # Linux
   sudo systemctl status redis-server
   
   # macOS
   brew services list | grep redis
   ```

2. Vérifiez le port :
   ```bash
   redis-cli -p 6379 ping
   ```

3. Vérifiez les permissions de connexion dans `redis.conf`

### Problème : "NameError: name 'DB_NAME' is not defined"

**Solution :** Assurez-vous que toutes les variables de base de données sont définies dans votre `.env`, ou utilisez `DATABASE_URL`.

### Problème : Base de données n'existe pas

**Solution :** Créez la base de données :

```sql
-- PostgreSQL
CREATE DATABASE comparateur_prix;

-- MySQL
CREATE DATABASE comparateur_prix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### Problème : Erreur de connexion en production (Railway)

**Solutions :**
1. Vérifiez que `DATABASE_URL` est bien défini dans Railway
2. Vérifiez que le service de base de données est démarré
3. Vérifiez les variables d'environnement dans Railway → Variables

### Problème : Redis ne fonctionne pas en production

**Solutions :**
1. Vérifiez que le service Redis est ajouté dans Railway
2. Vérifiez que `REDIS_URL` est défini
3. En cas d'erreur, l'application utilisera le cache local en développement

---

## 📝 Checklist de Configuration

### Base de Données
- [ ] Base de données créée (PostgreSQL/MySQL)
- [ ] Utilisateur créé avec les permissions appropriées
- [ ] Variables d'environnement définies dans `.env`
- [ ] Connexion testée avec `python manage.py dbshell`
- [ ] Migrations appliquées avec `python manage.py migrate`

### Redis
- [ ] Redis installé et démarré
- [ ] `REDIS_URL` défini dans `.env`
- [ ] Connexion testée avec `redis-cli ping`
- [ ] Celery configuré (si utilisé)

### Production (Railway)
- [ ] `DATABASE_URL` configuré (Railway) ou variables individuelles (cPanel)
- [ ] `REDIS_URL` configuré
- [ ] `DJANGO_DEBUG=False`
- [ ] `DJANGO_SECRET_KEY` défini
- [ ] Variables d'environnement vérifiées dans le panneau de contrôle

---

## 📚 Ressources supplémentaires

- [Documentation PostgreSQL](https://www.postgresql.org/docs/)
- [Documentation Redis](https://redis.io/documentation)
- [Documentation Celery](https://docs.celeryproject.org/)
- [Documentation Railway](https://docs.railway.app/)

---

## 💡 Conseils

1. **Sécurité :** Ne commitez jamais votre fichier `.env` dans Git
2. **Backup :** Faites des sauvegardes régulières de votre base de données
3. **Performance :** Utilisez Redis pour le cache en production
4. **Monitoring :** Surveillez l'utilisation de Redis et de la base de données

---

**Besoin d'aide ?** Consultez les autres documents dans le dossier `docs/` ou ouvrez une issue sur le dépôt.

