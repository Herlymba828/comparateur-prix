# 🔗 Guide : Connecter votre projet uploadé à l'application Django dans cPanel

Ce guide vous explique comment faire fonctionner votre projet Django uploadé sur le serveur avec l'application Python que vous avez créée dans cPanel.

---

## 📋 Prérequis

- ✅ Votre projet est uploadé sur le serveur
- ✅ Vous avez créé une application Python dans cPanel (Setup Python App)
- ✅ Vous avez accès SSH ou au terminal de cPanel

---

## 🔍 ÉTAPE 1 : Vérifier l'emplacement de votre projet

### 1.1 Trouver où sont vos fichiers

Connectez-vous en SSH ou utilisez le Terminal de cPanel :

```bash
# Chercher votre projet
find /home/rs2694021ez6eg8n -name "manage.py" -type f 2>/dev/null
```

**Emplacements possibles** :
- `/home/rs2694021ez6eg8n/public_html/comparer/`
- `/home/rs2694021ez6eg8n/public_html/`
- `/home/rs2694021ez6eg8n/comparer/`
- Autre emplacement selon votre upload

### 1.2 Vérifier la structure

Une fois que vous avez trouvé le répertoire, vérifiez qu'il contient :
```bash
cd /chemin/vers/votre/projet
ls -la
```

Vous devriez voir :
- ✅ `manage.py`
- ✅ `passenger_wsgi.py`
- ✅ `requirements.txt`
- ✅ `config/` (dossier)
- ✅ `apps/` (dossier)

---

## 🐍 ÉTAPE 2 : Vérifier et corriger l'environnement virtuel

### 2.1 Trouver le chemin de l'environnement virtuel

Dans cPanel → **Setup Python App**, regardez votre application :
- Notez le chemin de l'**environnement virtuel** (Virtual Environment)
- Il ressemble à : `/home/rs2694021ez6eg8n/virtualenv/nom_app/3.11/`

### 2.2 Vérifier le fichier passenger_wsgi.py

Ouvrez le fichier `passenger_wsgi.py` dans votre projet :

```bash
cd /chemin/vers/votre/projet
nano passenger_wsgi.py
```

**Vérifiez la ligne 13** - elle doit correspondre au chemin de votre environnement virtuel :

```python
# Exemple si votre env virtuel est : /home/rs2694021ez6eg8n/virtualenv/compare2/3.11/
activate_this = '/home/rs2694021ez6eg8n/virtualenv/compare2/3.11/bin/activate_this.py'
```

**Si le chemin est incorrect**, corrigez-le :

```python
# Pour cPanel, utilisez généralement :
activate_this = '/home/rs2694021ez6eg8n/virtualenv/nom_de_votre_app/3.11/bin/activate_this.py'
```

**Note** : Remplacez `nom_de_votre_app` par le nom réel de votre application Python dans cPanel.

---

## ⚙️ ÉTAPE 3 : Configurer l'application dans cPanel

### 3.1 Accéder à Setup Python App

1. Dans cPanel, allez dans **"Setup Python App"** ou **"Passenger"**
2. Cliquez sur votre application existante (ou créez-en une nouvelle)

### 3.2 Configurer les paramètres

Assurez-vous que ces paramètres sont corrects :

- **App Root** : `/chemin/vers/votre/projet`
  - Exemple : `/home/rs2694021ez6eg8n/public_html/comparer`
  
- **App URL** : `/` (ou `/comparer` selon votre configuration)

- **Python Version** : `3.11`

- **Application File** : `passenger_wsgi.py`
  - ⚠️ **IMPORTANT** : Le fichier doit être à la racine de votre projet

- **Virtual Environment** : Vérifiez qu'il pointe vers le bon environnement

### 3.3 Sauvegarder et redémarrer

1. Cliquez sur **"Save"** ou **"Update"**
2. Cliquez sur **"Restart"** pour redémarrer l'application

---

## 📦 ÉTAPE 4 : Installer les dépendances

### 4.1 Activer l'environnement virtuel

```bash
# Trouvez le chemin de votre environnement virtuel dans cPanel
# Exemple :
source /home/rs2694021ez6eg8n/virtualenv/nom_app/3.11/bin/activate

# Vérifier que Python 3.11 est actif
python --version
# Doit afficher : Python 3.11.x
```

### 4.2 Aller dans le répertoire du projet

```bash
cd /chemin/vers/votre/projet
```

### 4.3 Installer les dépendances

```bash
# Mettre à jour pip
pip install --upgrade pip

# Installer toutes les dépendances
pip install -r requirements.txt
```

**⏱️ Temps estimé** : 5-10 minutes

**⚠️ Si erreur de permissions** :
```bash
pip install --user -r requirements.txt
```

---

## 🔐 ÉTAPE 5 : Configurer le fichier .env

### 5.1 Créer ou modifier le fichier .env

```bash
cd /chemin/vers/votre/projet
nano .env
```

### 5.2 Ajouter la configuration minimale

```bash
# Django
DJANGO_SECRET_KEY=votre_clé_secrète_ici
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=comparateurdeprix.com,www.comparateurdeprix.com

# Base de données
DB_ENGINE=mysql
DB_NAME=rs2694021ez6eg8n_soutenance2.0
DB_USER=rs2694021ez6eg8n_db_user
DB_PASSWORD=BlackEurtz8282@
DB_HOST=localhost
DB_PORT=3306

# URLs
BACKEND_URL=https://comparateurdeprix.com
FRONTEND_URL=https://comparateurdeprix.com
SITE_URL=https://comparateurdeprix.com
```

**💡 Astuce** : Consultez `docs/ENV_PRODUCTION_CORRIGE.md` pour le fichier `.env` complet.

### 5.3 Sécuriser le fichier .env

```bash
chmod 600 .env
```

---

## 🗄️ ÉTAPE 6 : Configurer la base de données

### 6.1 Vérifier la connexion

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/nom_app/3.11/bin/activate

# Aller dans le projet
cd /chemin/vers/votre/projet

# Tester la connexion
python manage.py dbshell
# Si ça fonctionne, tapez \q pour quitter
```

### 6.2 Appliquer les migrations

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

### 6.3 Créer un superutilisateur

```bash
python manage.py createsuperuser
```

Suivez les instructions pour créer un compte admin.

---

## 📁 ÉTAPE 7 : Collecter les fichiers statiques

```bash
# Créer le répertoire si nécessaire
mkdir -p staticfiles

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

---

## 🔧 ÉTAPE 8 : Vérifier la configuration

### 8.1 Vérifier avec Django

```bash
python manage.py check --deploy
```

Vous verrez des avertissements `drf_spectacular` - c'est normal, ils ne sont pas critiques.

### 8.2 Vérifier les permissions

```bash
# Fichiers Python
find . -type f -name "*.py" -exec chmod 644 {} \;

# Fichiers exécutables
chmod 755 manage.py
chmod 755 passenger_wsgi.py

# Répertoires
find . -type d -exec chmod 755 {} \;

# Fichier .env
chmod 600 .env
```

---

## 🔄 ÉTAPE 9 : Redémarrer l'application

### 9.1 Dans cPanel

1. Allez dans **Setup Python App**
2. Cliquez sur votre application
3. Cliquez sur **"Restart"**

### 9.2 Vérifier les logs

Si l'application ne démarre pas, vérifiez les logs :

```bash
# Logs d'erreur
tail -f error_log

# Ou dans cPanel → Errors
```

---

## ✅ ÉTAPE 10 : Tester l'application

### 10.1 Tests via navigateur

Ouvrez votre navigateur et testez :

- **Health Check** : `https://comparateurdeprix.com/api/health/`
  - Doit retourner : `{"status": "ok"}`

- **Swagger** : `https://comparateurdeprix.com/api/docs/`
  - Doit afficher la documentation API

- **Admin** : `https://comparateurdeprix.com/admin/`
  - Doit afficher la page de connexion

### 10.2 Tests via SSH

```bash
# Test Health Check
curl https://comparateurdeprix.com/api/health/

# Test Connection
curl https://comparateurdeprix.com/api/test-connection/
```

---

## 🚨 Dépannage

### Erreur 500 Internal Server Error

**Causes possibles** :
1. Fichier `.env` manquant ou incorrect
2. Chemin de l'environnement virtuel incorrect dans `passenger_wsgi.py`
3. Dépendances non installées
4. Permissions incorrectes

**Solutions** :
```bash
# 1. Vérifier que .env existe
ls -la .env

# 2. Vérifier le chemin dans passenger_wsgi.py
cat passenger_wsgi.py | grep activate_this

# 3. Réinstaller les dépendances
pip install -r requirements.txt

# 4. Vérifier les permissions
chmod 755 manage.py passenger_wsgi.py
```

### Erreur "Module not found"

**Solution** :
```bash
# Vérifier que l'environnement virtuel est activé
which python
# Doit afficher : /home/rs2694021ez6eg8n/virtualenv/...

# Réinstaller les dépendances
pip install -r requirements.txt
```

### Erreur "ALLOWED_HOSTS"

**Solution** :
Vérifiez que votre domaine est dans `DJANGO_ALLOWED_HOSTS` dans le fichier `.env` :
```bash
DJANGO_ALLOWED_HOSTS=comparateurdeprix.com,www.comparateurdeprix.com
```

### L'application ne démarre pas

**Vérifications** :
1. Le chemin dans `passenger_wsgi.py` correspond-il à votre environnement virtuel ?
2. Le fichier `passenger_wsgi.py` est-il à la racine du projet ?
3. L'**App Root** dans cPanel correspond-il au répertoire de votre projet ?
4. L'**Application File** dans cPanel est-il bien `passenger_wsgi.py` ?

---

## 📋 Checklist finale

Avant de considérer que tout fonctionne :

- [ ] ✅ Projet uploadé et trouvé sur le serveur
- [ ] ✅ Chemin de l'environnement virtuel correct dans `passenger_wsgi.py`
- [ ] ✅ Application Python configurée dans cPanel avec les bons paramètres
- [ ] ✅ Environnement virtuel activé
- [ ] ✅ Dépendances installées (`pip install -r requirements.txt`)
- [ ] ✅ Fichier `.env` créé et configuré
- [ ] ✅ Base de données accessible
- [ ] ✅ Migrations appliquées (`python manage.py migrate`)
- [ ] ✅ Superutilisateur créé (`python manage.py createsuperuser`)
- [ ] ✅ Fichiers statiques collectés (`python manage.py collectstatic`)
- [ ] ✅ Application redémarrée dans cPanel
- [ ] ✅ Tests réussis : Health Check, Swagger, Admin

---

## 🎯 Points importants à retenir

1. **Le chemin de l'environnement virtuel** dans `passenger_wsgi.py` doit correspondre exactement à celui créé par cPanel
2. **L'App Root** dans cPanel doit pointer vers le répertoire contenant `manage.py` et `passenger_wsgi.py`
3. **L'Application File** doit être `passenger_wsgi.py` (à la racine du projet)
4. **Le fichier `.env`** doit être présent et correctement configuré
5. **Toutes les dépendances** doivent être installées dans l'environnement virtuel

---

## 📞 Support

Si vous rencontrez toujours des problèmes :

1. **Vérifiez les logs** : `tail -f error_log`
2. **Vérifiez la configuration** dans cPanel → Setup Python App
3. **Testez en mode DEBUG temporairement** (déconseillé en production) :
   ```bash
   # Dans .env
   DJANGO_DEBUG=True
   ```
4. **Contactez le support de votre hébergeur** si le problème persiste

---

## 🎉 Félicitations !

Si tous les tests passent, votre application Django est maintenant fonctionnelle sur le serveur !

**Prochaines étapes** :
- Configurez votre frontend pour utiliser l'API
- Configurez les tâches cron si nécessaire
- Surveillez les logs régulièrement
- Faites des sauvegardes régulières

