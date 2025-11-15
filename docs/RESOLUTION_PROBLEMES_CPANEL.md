# 🔧 Résolution des problèmes cPanel

## ❌ Problème actuel : Erreur de connexion PostgreSQL

```
psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", 
port 5432 failed: fe_sendauth: no password supplied
```

## ✅ Solution rapide (5 minutes)

### Étape 1 : Créer le fichier `.env`

Sur votre serveur cPanel, exécutez :

```bash
cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix
nano .env
```

### Étape 2 : Ajouter ce contenu dans `.env`

Remplacez les valeurs entre `<>` par vos vraies informations :

```bash
# Mode Debug (False en production)
DJANGO_DEBUG=False

# Clé secrète Django (générez-en une nouvelle)
DJANGO_SECRET_KEY=<générez-une-cle-aleatoire>

# Configuration PostgreSQL
DB_ENGINE=postgresql
DB_NAME=<nom_de_votre_base>
DB_USER=<utilisateur_postgresql>
DB_PASSWORD=<mot_de_passe_postgresql>
DB_HOST=localhost
DB_PORT=5432

# SSL PostgreSQL (False sur cPanel généralement)
POSTGRES_SSL_REQUIRE=False
```

### Étape 3 : Générer une clé secrète

```bash
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copiez la clé générée et remplacez `<générez-une-cle-aleatoire>` dans `.env`.

### Étape 4 : Obtenir les identifiants PostgreSQL

**Via cPanel :**
1. Connectez-vous à cPanel
2. Allez dans **"PostgreSQL Databases"** ou **"MySQL Databases"**
3. Si vous n'avez pas de base, créez-en une
4. Notez le nom de la base, l'utilisateur et le mot de passe

**Exemple de noms sur cPanel :**
- Base de données : `rs2694021ez6eg8n_comparer`
- Utilisateur : `rs2694021ez6eg8n_dbuser`
- Mot de passe : (celui que vous avez défini)

### Étape 5 : Protéger le fichier `.env`

```bash
chmod 600 .env
```

### Étape 6 : Tester la connexion

```bash
python manage.py dbshell
```

Si ça fonctionne, vous verrez le prompt PostgreSQL. Tapez `\q` pour quitter.

### Étape 7 : Appliquer les migrations

```bash
python manage.py migrate
```

### Étape 8 : Vérifier la configuration

```bash
python manage.py check --deploy
```

Les avertissements de sécurité devraient disparaître une fois `DJANGO_DEBUG=False` configuré.

## 📋 Exemple de fichier `.env` complet

```bash
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=django-insecure-abc123xyz789-remplacez-par-une-vraie-cle
DB_ENGINE=postgresql
DB_NAME=rs2694021ez6eg8n_comparer
DB_USER=rs2694021ez6eg8n_dbuser
DB_PASSWORD=votre_mot_de_passe_ici
DB_HOST=localhost
DB_PORT=5432
POSTGRES_SSL_REQUIRE=False
RECO_INIT_MODELS_ON_STARTUP=False
```

## 🚨 Avertissements de sécurité

Les avertissements que vous voyez (`W018`, `W004`, etc.) disparaîtront automatiquement une fois que :
- ✅ `DJANGO_DEBUG=False` est défini dans `.env`
- ✅ L'application est redémarrée

Les paramètres de sécurité sont déjà configurés dans `config/settings.py` et s'activeront automatiquement quand `DEBUG=False`.

## 🔍 Vérification rapide

Pour vérifier que tout est bien configuré :

```bash
# 1. Vérifier que .env existe
ls -la .env

# 2. Vérifier que les variables sont chargées
python manage.py shell -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DEBUG:', os.getenv('DJANGO_DEBUG')); print('DB_NAME:', os.getenv('DB_NAME'))"

# 3. Tester la connexion DB
python manage.py dbshell

# 4. Vérifier la configuration
python manage.py check --deploy
```

## 📚 Documentation complète

Pour plus de détails, consultez :
- `docs/CONFIGURATION_CPANEL.md` - Guide complet de configuration
- `docs/DEPLOIEMENT_CPANEL.md` - Guide de déploiement

## ⚡ Script automatique (optionnel)

Si vous préférez utiliser un script interactif :

```bash
chmod +x scripts/setup_env_cpanel.sh
./scripts/setup_env_cpanel.sh
```

Ce script vous guidera étape par étape pour créer le fichier `.env`.

