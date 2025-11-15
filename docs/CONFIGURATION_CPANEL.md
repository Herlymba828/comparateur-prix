# Configuration cPanel - Résolution des problèmes

## Problème 1 : Erreur de connexion à la base de données

L'erreur `fe_sendauth: no password supplied` indique que les identifiants PostgreSQL ne sont pas configurés.

### Solution : Créer le fichier `.env`

1. **Connectez-vous à votre serveur cPanel via SSH** ou utilisez le **File Manager** de cPanel.

2. **Naviguez vers le répertoire de votre application** :
   ```bash
   cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix
   ```

3. **Créez un fichier `.env`** à la racine du projet (même niveau que `manage.py`) :
   ```bash
   touch .env
   ```

4. **Ajoutez les variables d'environnement suivantes** dans le fichier `.env` :

   ```bash
   # Mode Debug (IMPORTANT : False en production)
   DJANGO_DEBUG=False

   # Clé secrète Django (générez-en une nouvelle pour la production)
   DJANGO_SECRET_KEY=votre_cle_secrete_ici

   # Configuration PostgreSQL
   DB_ENGINE=postgresql
   DB_NAME=nom_de_votre_base_de_donnees
   DB_USER=nom_utilisateur_postgresql
   DB_PASSWORD=mot_de_passe_postgresql
   DB_HOST=localhost
   DB_PORT=5432

   # Hôtes autorisés (optionnel, sera ajouté automatiquement si DEBUG=False)
   # DJANGO_ALLOWED_HOSTS=ftp.navixtechnology.com,www.ftp.navixtechnology.com
   ```

### Comment obtenir les identifiants PostgreSQL sur cPanel

1. **Via cPanel** :
   - Allez dans **"PostgreSQL Databases"** ou **"MySQL Databases"** (selon votre hébergeur)
   - Créez une base de données si elle n'existe pas
   - Créez un utilisateur PostgreSQL si nécessaire
   - Notez le nom de la base, l'utilisateur et le mot de passe

2. **Via SSH** :
   ```bash
   # Vérifier les bases de données disponibles
   psql -U votre_utilisateur -l
   ```

### Générer une clé secrète Django

Sur le serveur, exécutez :
```bash
cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix
python manage.py shell -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Ou utilisez le script fourni :
```bash
python scripts/generate_secret_key.py
```

Copiez la clé générée dans votre fichier `.env` pour `DJANGO_SECRET_KEY`.

## Problème 2 : Avertissements de sécurité

Les avertissements de sécurité apparaissent parce que `DEBUG=True` en production. Une fois que vous avez configuré `DJANGO_DEBUG=False` dans le fichier `.env`, ces avertissements disparaîtront.

### Vérification après configuration

1. **Vérifiez que le fichier `.env` est bien créé** :
   ```bash
   ls -la .env
   ```

2. **Vérifiez que les variables sont bien chargées** :
   ```bash
   python manage.py shell -c "import os; from dotenv import load_dotenv; load_dotenv(); print('DEBUG:', os.getenv('DJANGO_DEBUG')); print('DB_NAME:', os.getenv('DB_NAME'))"
   ```

3. **Testez la connexion à la base de données** :
   ```bash
   python manage.py dbshell
   ```

4. **Appliquez les migrations** :
   ```bash
   python manage.py migrate
   ```

5. **Vérifiez la configuration de production** :
   ```bash
   python manage.py check --deploy
   ```

## Sécurité du fichier `.env`

⚠️ **IMPORTANT** : Le fichier `.env` contient des informations sensibles. Assurez-vous qu'il n'est pas accessible publiquement.

1. **Vérifiez que `.env` est dans `.gitignore`** (déjà fait normalement)

2. **Protégez le fichier via `.htaccess`** (si nécessaire) :
   ```apache
   <Files ".env">
       Order allow,deny
       Deny from all
   </Files>
   ```

3. **Définissez les permissions correctes** :
   ```bash
   chmod 600 .env
   ```

## Exemple de fichier `.env` complet

```bash
# ============================================
# Configuration Django - PRODUCTION
# ============================================

# Mode Debug (False en production)
DJANGO_DEBUG=False

# Clé secrète Django (générez-en une nouvelle)
DJANGO_SECRET_KEY=django-insecure-remplacez-par-une-vraie-cle-secrete-aleatoire

# Configuration PostgreSQL
DB_ENGINE=postgresql
DB_NAME=rs2694021ez6eg8n_comparer
DB_USER=rs2694021ez6eg8n_dbuser
DB_PASSWORD=votre_mot_de_passe_ici
DB_HOST=localhost
DB_PORT=5432

# SSL PostgreSQL (optionnel, True par défaut en production)
POSTGRES_SSL_REQUIRE=False

# Hôtes autorisés (optionnel)
DJANGO_ALLOWED_HOSTS=ftp.navixtechnology.com,www.ftp.navixtechnology.com

# Initialisation des modèles ML au démarrage (False pour économiser la mémoire)
RECO_INIT_MODELS_ON_STARTUP=False
```

## Étapes de déploiement complètes

1. ✅ Créer le fichier `.env` avec les bonnes variables
2. ✅ Vérifier les permissions du fichier `.env` (600)
3. ✅ Tester la connexion à la base de données
4. ✅ Appliquer les migrations : `python manage.py migrate`
5. ✅ Collecter les fichiers statiques : `python manage.py collectstatic --noinput`
6. ✅ Vérifier la configuration : `python manage.py check --deploy`
7. ✅ Redémarrer l'application (via cPanel ou Passenger)

## Dépannage

### Erreur : "connection failed: fe_sendauth: no password supplied"
- Vérifiez que `DB_PASSWORD` est défini dans `.env`
- Vérifiez que le fichier `.env` est au bon endroit (même répertoire que `manage.py`)
- Vérifiez les permissions du fichier `.env`

### Erreur : "database does not exist"
- Créez la base de données via cPanel ou PostgreSQL
- Vérifiez que `DB_NAME` dans `.env` correspond au nom réel de la base

### Erreur : "password authentication failed"
- Vérifiez que `DB_USER` et `DB_PASSWORD` sont corrects
- Réinitialisez le mot de passe de l'utilisateur PostgreSQL si nécessaire

### Les avertissements de sécurité persistent
- Vérifiez que `DJANGO_DEBUG=False` dans `.env`
- Redémarrez l'application après modification de `.env`
- Vérifiez que le fichier `.env` est bien lu : `python manage.py shell -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DJANGO_DEBUG'))"`

