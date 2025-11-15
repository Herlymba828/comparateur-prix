# 📋 Étapes de Déploiement - cPanel/WHM

## Vue d'ensemble

Ce guide vous accompagne étape par étape pour déployer votre backend Django sur votre hébergeur cPanel/WHM.

**Informations de votre environnement** :
- 📁 Répertoire : `/home/rs2694021ez6eg8n/public_html/comparer`
- 🐍 Python : 3.11
- 🌐 Domaine : `ftp.navixtechnology.com`
- 🔧 Environnement virtuel : `/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/`

---

## 📦 ÉTAPE 1 : Préparation locale

### 1.1 Générer une clé secrète

Sur votre machine locale :

```bash
python scripts/generate_secret_key.py
```

**Copiez la clé générée** - vous en aurez besoin à l'étape 6.

### 1.2 Vérifier les fichiers

Assurez-vous d'avoir ces fichiers dans votre projet :
- ✅ `.htaccess`
- ✅ `passenger_wsgi.py`
- ✅ `index.py`
- ✅ `requirements.txt`
- ✅ `runtime.txt`

---

## 📤 ÉTAPE 2 : Upload des fichiers

### Option A : Via FTP/SFTP (FileZilla, WinSCP)

1. Connectez-vous à votre serveur
2. Naviguez vers `/home/rs2694021ez6eg8n/public_html/comparer`
3. Uploadez **tous les fichiers** sauf :
   - ❌ `venv/` (environnement virtuel local)
   - ❌ `__pycache__/`
   - ❌ `*.pyc`
   - ❌ `.git/`
   - ❌ `media/` (sera créé automatiquement)
   - ❌ `staticfiles/` (sera généré)

### Option B : Via Git (recommandé)

Si vous avez un dépôt Git :

```bash
# Sur le serveur (via SSH)
cd /home/rs2694021ez6eg8n/public_html/comparer
git clone https://votre-repo.git .
# ou si le dossier existe déjà
git pull origin main
```

---

## 🔌 ÉTAPE 3 : Connexion SSH

Connectez-vous à votre serveur via SSH :

```bash
ssh votre-utilisateur@ftp.navixtechnology.com
```

Si vous ne connaissez pas vos identifiants SSH :
1. Allez dans cPanel
2. Cherchez **"Terminal"** ou **"SSH Access"**
3. Activez l'accès SSH si nécessaire

---

## 🐍 ÉTAPE 4 : Activation de l'environnement virtuel

Une fois connecté en SSH :

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Vérifier que Python 3.11 est actif
python --version
# Doit afficher : Python 3.11.x

# Aller dans le répertoire du projet
cd /home/rs2694021ez6eg8n/public_html/comparer

# Vérifier que vous êtes au bon endroit
ls -la
# Vous devriez voir manage.py, requirements.txt, etc.
```

**💡 Astuce** : Vous verrez `(3.11)` au début de votre ligne de commande quand l'environnement virtuel est activé.

---

## 📥 ÉTAPE 5 : Installation des dépendances

```bash
# Mettre à jour pip
pip install --upgrade pip

# Installer toutes les dépendances
pip install -r requirements.txt

# Si vous avez des erreurs de permissions, utilisez :
# pip install --user -r requirements.txt
```

**⏱️ Temps estimé** : 5-10 minutes selon la connexion.

**⚠️ Si certaines dépendances échouent** :
- `psycopg2-binary` : Installez-le séparément : `pip install psycopg2-binary`
- `Pillow` : Peut nécessiter des bibliothèques système (généralement déjà installées sur cPanel)

---

## ⚙️ ÉTAPE 6 : Configuration du fichier .env

### 6.1 Créer le fichier .env

```bash
# Créer le fichier .env à partir de l'exemple
cp .env.example .env

# Ou créer un nouveau fichier
nano .env
```

### 6.2 Remplir le fichier .env

Collez ce contenu et **remplacez les valeurs** :

```bash
# Configuration Django
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<COLLEZ_LA_CLÉ_GÉNÉRÉE_À_L_ÉTAPE_1>
DJANGO_ALLOWED_HOSTS=ftp.navixtechnology.com,www.ftp.navixtechnology.com

# Base de données PostgreSQL
POSTGRES_DB=rs2694021ez6eg8n_comparer
POSTGRES_USER=rs2694021ez6eg8n_dbuser
POSTGRES_PASSWORD=<VOTRE_MOT_DE_PASSE_DB>
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_SSL_REQUIRE=True

# JWT
USE_JWT_AUTH=True
SITE_URL=https://ftp.navixtechnology.com
```

**Sauvegarder** : `Ctrl+O` puis `Enter`, puis `Ctrl+X`

### 6.3 Sécuriser le fichier .env

```bash
chmod 600 .env
```

Cela empêche les autres utilisateurs de lire votre fichier de configuration.

---

## 🗄️ ÉTAPE 7 : Configuration de la base de données

### 7.1 Créer la base de données dans cPanel

1. Connectez-vous à **cPanel**
2. Allez dans **"PostgreSQL Databases"** (ou **"MySQL Databases"** si vous utilisez MySQL)
3. Dans **"Create New Database"** :
   - Nom : `comparer` (ou autre nom)
   - Cliquez sur **"Create Database"**
4. Dans **"Add New User"** :
   - Créez un utilisateur avec un mot de passe fort
   - Cliquez sur **"Create User"**
5. Dans **"Add User To Database"** :
   - Sélectionnez l'utilisateur et la base
   - Cochez **"ALL PRIVILEGES"**
   - Cliquez sur **"Make Changes"**

### 7.2 Noter les identifiants

Notez :
- **Nom de la base** : `rs2694021ez6eg8n_comparer` (format cPanel)
- **Utilisateur** : `rs2694021ez6eg8n_dbuser` (format cPanel)
- **Mot de passe** : (celui que vous avez créé)
- **Hôte** : `localhost` (généralement)

### 7.3 Mettre à jour le fichier .env

Éditez `.env` et remplacez les valeurs de la base de données :

```bash
nano .env
```

Mettez à jour :
- `POSTGRES_DB=rs2694021ez6eg8n_comparer`
- `POSTGRES_USER=rs2694021ez6eg8n_dbuser`
- `POSTGRES_PASSWORD=votre_mot_de_passe`

---

## 🔄 ÉTAPE 8 : Migrations et configuration Django

### 8.1 Vérifier la configuration

```bash
# Vérifier que tout est correct
python manage.py check --deploy
```

Vous verrez des avertissements `drf_spectacular` - c'est normal, ils ne sont pas critiques.

### 8.2 Appliquer les migrations

```bash
# Appliquer toutes les migrations
python manage.py migrate

# Si vous avez des migrations spécifiques
python manage.py migrate produits
python manage.py migrate utilisateurs
python manage.py migrate recommandations
python manage.py migrate analyses
python manage.py migrate magasins
```

### 8.3 Créer un superutilisateur

```bash
python manage.py createsuperuser
```

Suivez les instructions :
- Username : (choisissez un nom d'utilisateur)
- Email : (votre email)
- Password : (choisissez un mot de passe fort)

### 8.4 Collecter les fichiers statiques

```bash
# Créer le répertoire si nécessaire
mkdir -p staticfiles

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

---

## 🌐 ÉTAPE 9 : Configuration du serveur web (Passenger)

### 9.1 Dans cPanel

1. Allez dans **"Setup Python App"** ou **"Passenger"**
2. Si vous avez déjà une application, cliquez dessus
3. Sinon, créez une nouvelle application :
   - **App Root** : `/home/rs2694021ez6eg8n/public_html/comparer`
   - **App URL** : `/` (ou `/comparer` si vous préférez)
   - **Python Version** : `3.11`
   - **Application File** : `passenger_wsgi.py`
4. Cliquez sur **"Create"** ou **"Restart"**

### 9.2 Vérifier la configuration

Assurez-vous que :
- ✅ L'environnement virtuel est correctement détecté
- ✅ Le fichier `passenger_wsgi.py` est trouvé
- ✅ Python 3.11 est sélectionné

---

## 🔒 ÉTAPE 10 : Configuration SSL/HTTPS

### 10.1 Installer un certificat SSL

Dans cPanel :

1. Allez dans **"SSL/TLS"**
2. Dans **"Let's Encrypt"** (gratuit) :
   - Sélectionnez votre domaine : `ftp.navixtechnology.com`
   - Cliquez sur **"Run AutoSSL"** ou **"Install"**
3. Attendez quelques minutes que le certificat soit installé

### 10.2 Forcer HTTPS

1. Dans **"SSL/TLS"**, allez dans **"Force HTTPS Redirect"**
2. Activez la redirection pour `ftp.navixtechnology.com`
3. Cliquez sur **"Save"**

---

## ✅ ÉTAPE 11 : Tests et vérifications

### 11.1 Tester l'API

Ouvrez votre navigateur et visitez :

- **Swagger UI** : `https://ftp.navixtechnology.com/api/docs/`
- **API Produits** : `https://ftp.navixtechnology.com/api/produits/produits/`
- **Admin Django** : `https://ftp.navixtechnology.com/admin/`

### 11.2 Tester l'authentification

```bash
# Tester l'obtention d'un token JWT
curl -X POST https://ftp.navixtechnology.com/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"votre_username","password":"votre_password"}'
```

### 11.3 Vérifier les logs

Si quelque chose ne fonctionne pas :

```bash
# Logs Apache (si disponibles)
tail -f /usr/local/apache/logs/error_log

# Ou dans cPanel, allez dans "Errors" pour voir les erreurs récentes
```

---

## 🚀 Script de déploiement automatique

Pour automatiser les étapes 4-8, utilisez le script fourni :

```bash
# Rendre le script exécutable
chmod +x scripts/deploy_cpanel.sh

# Exécuter le script
bash scripts/deploy_cpanel.sh
```

Ce script :
- ✅ Active l'environnement virtuel
- ✅ Met à jour pip
- ✅ Installe les dépendances
- ✅ Vérifie la configuration
- ✅ Applique les migrations
- ✅ Collecte les fichiers statiques
- ✅ Configure les permissions

---

## 🔧 Dépannage

### Erreur 500 Internal Server Error

**Causes possibles** :
1. Fichier `.env` manquant ou incorrect
2. Permissions incorrectes
3. Erreur dans le code Python

**Solutions** :
```bash
# Vérifier que .env existe
ls -la .env

# Vérifier les permissions
chmod 755 manage.py
chmod 755 passenger_wsgi.py

# Vérifier les logs
tail -f error_log
```

### Erreur "Module not found"

**Solution** :
```bash
# Réinstaller les dépendances
pip install -r requirements.txt

# Vérifier que l'environnement virtuel est activé
which python
# Doit afficher : /home/rs2694021ez6eg8n/virtualenv/...
```

### Erreur de connexion à la base de données

**Solutions** :
1. Vérifiez les identifiants dans `.env`
2. Testez la connexion :
   ```bash
   python manage.py dbshell
   ```
3. Vérifiez que la base de données existe dans cPanel

### Erreur "ALLOWED_HOSTS"

**Solution** :
Vérifiez que dans `.env` :
```bash
DJANGO_ALLOWED_HOSTS=ftp.navixtechnology.com,www.ftp.navixtechnology.com
```

---

## 📋 Checklist finale

Avant de considérer le déploiement terminé :

- [ ] ✅ Tous les fichiers sont uploadés
- [ ] ✅ Environnement virtuel activé
- [ ] ✅ Dépendances installées (`pip install -r requirements.txt`)
- [ ] ✅ Fichier `.env` créé et configuré
- [ ] ✅ Base de données créée dans cPanel
- [ ] ✅ Migrations appliquées (`python manage.py migrate`)
- [ ] ✅ Superutilisateur créé (`python manage.py createsuperuser`)
- [ ] ✅ Fichiers statiques collectés (`python manage.py collectstatic`)
- [ ] ✅ Passenger configuré dans cPanel
- [ ] ✅ Certificat SSL installé
- [ ] ✅ HTTPS fonctionne
- [ ] ✅ API accessible (`https://ftp.navixtechnology.com/api/docs/`)
- [ ] ✅ Admin accessible (`https://ftp.navixtechnology.com/admin/`)

---

## 📞 Support

Si vous rencontrez des problèmes :

1. **Vérifiez les logs** : `tail -f error_log`
2. **Testez en mode DEBUG temporairement** (déconseillé en production) :
   ```bash
   # Dans .env, changez temporairement
   DJANGO_DEBUG=True
   ```
3. **Contactez le support de votre hébergeur** si le problème persiste

---

## 🎉 Félicitations !

Votre backend Django est maintenant déployé sur `https://ftp.navixtechnology.com` !

**Prochaines étapes** :
- Configurez votre frontend pour utiliser cette API
- Configurez les tâches cron si nécessaire
- Surveillez les logs régulièrement
- Faites des sauvegardes régulières de la base de données

