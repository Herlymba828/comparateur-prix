# Guide de Déploiement - cPanel/WHM

## Informations de votre environnement

- **Hébergeur**: WHM/cPanel
- **Domaine**: ftp.navixtechnology.com
- **Environnement virtuel**: `/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate`
- **Répertoire de travail**: `/home/rs2694021ez6eg8n/public_html/comparer`
- **Version Python**: 3.11

---

## ÉTAPE 1 : Préparation locale

### 1.1 Vérifier les fichiers à déployer

Assurez-vous d'avoir ces fichiers dans votre projet :
- `requirements.txt` (dépendances Python)
- `manage.py`
- `config/` (dossier de configuration Django)
- `apps/` (vos applications Django)
- `runtime.txt` (si vous utilisez Python 3.11)

### 1.2 Créer un fichier `.htaccess` pour cPanel

Créez un fichier `.htaccess` à la racine de votre projet :

```apache
# .htaccess pour cPanel avec Passenger
PassengerEnabled On
PassengerAppRoot /home/rs2694021ez6eg8n/public_html/comparer
PassengerBaseURI /
PassengerPython /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/python
PassengerAppType wsgi
PassengerStartupFile config/wsgi.py
```

### 1.3 Créer un fichier `passenger_wsgi.py` (alternative)

Si Passenger ne fonctionne pas avec `.htaccess`, créez `passenger_wsgi.py` à la racine :

```python
import sys
import os

# Ajouter le répertoire du projet au path
sys.path.insert(0, os.path.dirname(__file__))

# Activer l'environnement virtuel
activate_this = '/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate_this.py'
if os.path.exists(activate_this):
    exec(open(activate_this).read(), {'__file__': activate_this})

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Importer l'application WSGI
from config.wsgi import application

# Exposer l'application
application = application
```

### 1.4 Créer un fichier `.env.example`

Créez un fichier `.env.example` avec toutes les variables nécessaires (sans valeurs sensibles) :

```bash
# .env.example
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=votre-clé-secrète-ici
DJANGO_ALLOWED_HOSTS=ftp.navixtechnology.com,www.ftp.navixtechnology.com

# Base de données PostgreSQL
POSTGRES_DB=nom_de_votre_base
POSTGRES_USER=nom_utilisateur_db
POSTGRES_PASSWORD=mot_de_passe_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_SSL_REQUIRE=True

# JWT
USE_JWT_AUTH=True
JWT_ACCESS_MIN=60
JWT_REFRESH_DAYS=30

# CORS (optionnel)
CORS_ALLOWED_ORIGINS=https://votre-frontend.com
CSRF_TRUSTED_ORIGINS=https://votre-frontend.com

# Redis (optionnel)
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# Autres
SITE_URL=https://ftp.navixtechnology.com
```

---

## ÉTAPE 2 : Upload des fichiers

### 2.1 Via FTP/SFTP

1. Connectez-vous à votre serveur via FTP/SFTP avec FileZilla ou WinSCP
2. Naviguez vers `/home/rs2694021ez6eg8n/public_html/comparer`
3. Uploadez tous les fichiers de votre projet Django
4. **Important**: Ne pas uploader :
   - `venv/` (environnement virtuel local)
   - `__pycache__/`
   - `*.pyc`
   - `.git/`
   - `media/` (sera créé automatiquement)
   - `staticfiles/` (sera généré)

### 2.2 Via Git (recommandé)

Si vous avez un dépôt Git :

```bash
# Sur le serveur (via SSH)
cd /home/rs2694021ez6eg8n/public_html/comparer
git clone https://votre-repo.git .
# ou
git pull origin main
```

---

## ÉTAPE 3 : Configuration de l'environnement virtuel

### 3.1 Activer l'environnement virtuel

Connectez-vous en SSH à votre serveur :

```bash
ssh votre-utilisateur@ftp.navixtechnology.com
```

Puis :

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Vérifier la version de Python
python --version  # Doit afficher Python 3.11.x

# Aller dans le répertoire du projet
cd /home/rs2694021ez6eg8n/public_html/comparer
```

### 3.2 Installer les dépendances

```bash
# Mettre à jour pip
pip install --upgrade pip

# Installer les dépendances
pip install -r requirements.txt

# Si vous avez des problèmes de permissions, utilisez --user
# pip install --user -r requirements.txt
```

**Note**: Si certaines dépendances échouent, installez-les manuellement :
```bash
pip install django djangorestframework django-cors-headers psycopg2-binary
```

---

## ÉTAPE 4 : Configuration de la base de données

### 4.1 Créer la base de données dans cPanel

1. Connectez-vous à cPanel
2. Allez dans **"Bases de données MySQL"** ou **"PostgreSQL Databases"**
3. Créez une nouvelle base de données (ex: `rs2694021ez6eg8n_comparer`)
4. Créez un utilisateur et un mot de passe
5. Assurez-vous que l'utilisateur a tous les privilèges sur la base

### 4.2 Configurer les variables d'environnement

Dans cPanel, créez un fichier `.env` dans `/home/rs2694021ez6eg8n/public_html/comparer/` :

```bash
# Via SSH
cd /home/rs2694021ez6eg8n/public_html/comparer
nano .env
```

Collez votre configuration (remplacez les valeurs) :

```bash
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<générez-une-clé-secrète-longue>
DJANGO_ALLOWED_HOSTS=ftp.navixtechnology.com,www.ftp.navixtechnology.com

POSTGRES_DB=rs2694021ez6eg8n_comparer
POSTGRES_USER=rs2694021ez6eg8n_dbuser
POSTGRES_PASSWORD=votre_mot_de_passe
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_SSL_REQUIRE=True

USE_JWT_AUTH=True
SITE_URL=https://ftp.navixtechnology.com
```

**Générer une clé secrète** :
```bash
python -c "from secrets import token_urlsafe; print(token_urlsafe(50))"
```

Sauvegardez avec `Ctrl+O`, puis `Ctrl+X`.

### 4.3 Sécuriser le fichier .env

```bash
chmod 600 .env  # Seul le propriétaire peut lire/écrire
```

---

## ÉTAPE 5 : Migrations et configuration Django

### 5.1 Appliquer les migrations

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate
cd /home/rs2694021ez6eg8n/public_html/comparer

# Vérifier la configuration
python manage.py check --deploy

# Appliquer les migrations
python manage.py migrate

# Si vous avez des migrations spécifiques
python manage.py migrate produits
python manage.py migrate utilisateurs
python manage.py migrate recommandations
```

### 5.2 Créer un superutilisateur

```bash
python manage.py createsuperuser
```

Suivez les instructions pour créer un compte administrateur.

### 5.3 Collecter les fichiers statiques

```bash
# Créer le répertoire staticfiles si nécessaire
mkdir -p staticfiles

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

---

## ÉTAPE 6 : Configuration du serveur web (Passenger)

### 6.1 Vérifier la configuration Passenger

Dans cPanel :
1. Allez dans **"Setup Python App"** ou **"Passenger"**
2. Vérifiez que votre application est configurée :
   - **App Root**: `/home/rs2694021ez6eg8n/public_html/comparer`
   - **App URL**: `/` ou `/comparer`
   - **Python Version**: 3.11
   - **Application File**: `config/wsgi.py` ou `passenger_wsgi.py`

### 6.2 Configuration alternative avec .htaccess

Si Passenger n'est pas disponible, créez/modifiez `.htaccess` :

```apache
RewriteEngine On
RewriteBase /

# Rediriger vers HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Passer les requêtes à Django
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /index.py/$1 [L]
```

### 6.3 Créer un fichier `index.py` (si nécessaire)

Si votre hébergeur utilise un système différent, créez `index.py` :

```python
#!/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/python
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Rendez-le exécutable :
```bash
chmod +x index.py
```

---

## ÉTAPE 7 : Configuration SSL/HTTPS

### 7.1 Installer un certificat SSL

Dans cPanel :
1. Allez dans **"SSL/TLS"**
2. Installez un certificat SSL (Let's Encrypt est gratuit)
3. Activez **"Force HTTPS Redirect"**

### 7.2 Vérifier la configuration

Votre `.env` doit avoir :
```bash
DJANGO_DEBUG=False
```

Et dans `config/settings.py`, les paramètres de sécurité seront automatiquement activés.

---

## ÉTAPE 8 : Configuration des permissions

### 8.1 Définir les permissions correctes

```bash
cd /home/rs2694021ez6eg8n/public_html/comparer

# Fichiers Python
find . -type f -name "*.py" -exec chmod 644 {} \;

# Fichiers exécutables
chmod 755 manage.py
chmod 755 index.py  # si vous l'utilisez

# Répertoires
find . -type d -exec chmod 755 {} \;

# Fichiers sensibles
chmod 600 .env

# Répertoires d'écriture
chmod 775 media
chmod 775 staticfiles
chmod 775 logs  # si vous avez un dossier logs
```

### 8.2 Propriétaire des fichiers

Assurez-vous que vous êtes le propriétaire :
```bash
chown -R rs2694021ez6eg8n:rs2694021ez6eg8n /home/rs2694021ez6eg8n/public_html/comparer
```

---

## ÉTAPE 9 : Tests et vérifications

### 9.1 Tester la connexion à la base de données

```bash
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate
cd /home/rs2694021ez6eg8n/public_html/comparer

python manage.py dbshell
# Si cela fonctionne, tapez \q pour quitter
```

### 9.2 Tester l'application localement (via SSH)

```bash
python manage.py runserver 0.0.0.0:8000
# Testez avec: http://votre-ip:8000
```

### 9.3 Vérifier les logs

```bash
# Logs Apache (si disponibles)
tail -f /usr/local/apache/logs/error_log

# Logs de l'application Django
tail -f logs/*.log  # si vous avez configuré des logs
```

### 9.4 Tester l'API

Visitez dans votre navigateur :
- `https://ftp.navixtechnology.com/api/docs/` (Swagger UI)
- `https://ftp.navixtechnology.com/api/produits/produits/` (Liste des produits)
- `https://ftp.navixtechnology.com/admin/` (Interface d'administration)

---

## ÉTAPE 10 : Configuration avancée (optionnel)

### 10.1 Configuration Celery (si utilisé)

Si vous utilisez Celery pour les tâches asynchrones :

1. Créez un fichier `celeryd.conf` dans `/etc/supervisor/conf.d/` ou configurez-le via cPanel
2. Démarrez les workers Celery

### 10.2 Configuration Redis (si utilisé)

Si vous utilisez Redis pour le cache :
1. Installez Redis via cPanel ou demandez à votre hébergeur
2. Configurez `REDIS_URL` dans votre `.env`

### 10.3 Configuration des tâches cron

Dans cPanel, allez dans **"Cron Jobs"** et ajoutez :

```bash
# Tâches quotidiennes (exemple)
0 2 * * * source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate && cd /home/rs2694021ez6eg8n/public_html/comparer && python manage.py update_prices
```

---

## ÉTAPE 11 : Dépannage

### 11.1 Erreurs courantes

**Erreur 500 Internal Server Error**
- Vérifiez les logs : `tail -f error_log`
- Vérifiez que `.env` est correctement configuré
- Vérifiez les permissions des fichiers

**Erreur "Module not found"**
- Vérifiez que l'environnement virtuel est activé
- Réinstallez les dépendances : `pip install -r requirements.txt`

**Erreur de connexion à la base de données**
- Vérifiez les credentials dans `.env`
- Vérifiez que la base de données existe dans cPanel
- Vérifiez que l'utilisateur a les permissions

**Erreur "ALLOWED_HOSTS"**
- Vérifiez que `ftp.navixtechnology.com` est dans `DJANGO_ALLOWED_HOSTS`
- Vérifiez que `DJANGO_DEBUG=False` dans `.env`

### 11.2 Commandes utiles

```bash
# Vérifier la configuration Django
python manage.py check --deploy

# Voir les migrations en attente
python manage.py showmigrations

# Créer un superutilisateur
python manage.py createsuperuser

# Shell Django
python manage.py shell

# Nettoyer le cache
python manage.py clear_cache  # si configuré
```

---

## Checklist finale

Avant de considérer le déploiement terminé, vérifiez :

- [ ] Tous les fichiers sont uploadés
- [ ] L'environnement virtuel est activé et les dépendances installées
- [ ] Le fichier `.env` est configuré avec toutes les variables
- [ ] La base de données est créée et les migrations appliquées
- [ ] Un superutilisateur est créé
- [ ] Les fichiers statiques sont collectés
- [ ] Le certificat SSL est installé et HTTPS fonctionne
- [ ] L'application est accessible via `https://ftp.navixtechnology.com`
- [ ] L'API répond correctement
- [ ] L'interface d'administration est accessible
- [ ] Les logs ne montrent pas d'erreurs critiques

---

## Support

En cas de problème :
1. Vérifiez les logs d'erreur
2. Testez en mode DEBUG temporairement (déconseillé en production)
3. Contactez le support de votre hébergeur si nécessaire

---

## Notes importantes

- **Ne jamais** commiter le fichier `.env` dans Git
- **Toujours** utiliser `DJANGO_DEBUG=False` en production
- **Toujours** utiliser HTTPS en production
- **Sauvegardez** régulièrement votre base de données
- **Surveillez** les logs pour détecter les problèmes

