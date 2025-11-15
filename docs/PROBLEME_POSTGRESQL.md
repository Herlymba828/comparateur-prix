# 🔴 Problème : Version PostgreSQL incompatible

## Erreur rencontrée

```
django.db.utils.NotSupportedError: PostgreSQL 13 or later is required (found 9.622).
```

## Explication

Votre serveur utilise **PostgreSQL 9.622**, mais **Django 5.1.2** nécessite **PostgreSQL 13 ou supérieur**.

## Solutions possibles

### ✅ Solution 1 : Utiliser MySQL/MariaDB (RECOMMANDÉ)

MySQL/MariaDB est généralement plus facile à configurer sur cPanel et est largement supporté par Django.

#### Étape 1 : Créer la base de données MySQL dans cPanel

1. Allez dans cPanel → **"MySQL Databases"**
2. Créez une nouvelle base de données (ex: `rs2694021ez6eg8n_comparer`)
3. Créez un utilisateur avec un mot de passe fort
4. Donnez tous les privilèges à l'utilisateur sur la base

#### Étape 2 : Modifier la configuration Django

Modifiez votre fichier `.env` :

```bash
# Remplacer la configuration PostgreSQL par MySQL
# POSTGRES_DB=...
# POSTGRES_USER=...
# POSTGRES_PASSWORD=...
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432

# Utiliser MySQL à la place
DB_ENGINE=mysql
DB_NAME=rs2694021ez6eg8n_comparer
DB_USER=rs2694021ez6eg8n_dbuser
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=3306
```

#### Étape 3 : Installer le driver MySQL

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Installer mysqlclient
pip install mysqlclient

# Si mysqlclient échoue, utilisez PyMySQL
pip install PyMySQL
```

#### Étape 4 : Modifier settings.py pour supporter MySQL

Ajoutez ceci au début de `config/settings.py` (après les imports) :

```python
# Support MySQL avec PyMySQL (si mysqlclient ne fonctionne pas)
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass
```

#### Étape 5 : Modifier la configuration de la base de données

Dans `config/settings.py`, modifiez la section DATABASES :

```python
# Database
DB_ENGINE = os.getenv('DB_ENGINE', 'postgresql')
DB_NAME = os.getenv('DB_NAME', os.getenv('POSTGRES_DB', 'soutenance2'))
DB_USER = os.getenv('DB_USER', os.getenv('POSTGRES_USER', 'postgres'))
DB_PASSWORD = os.getenv('DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))
DB_HOST = os.getenv('DB_HOST', os.getenv('POSTGRES_HOST', 'localhost'))
DB_PORT = os.getenv('DB_PORT', os.getenv('POSTGRES_PORT', '5432'))

if DB_ENGINE == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    # Configuration PostgreSQL (par défaut)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'OPTIONS': {
                'options': '-c client_encoding=UTF8',
            },
        }
    }
```

---

### ⚠️ Solution 2 : Demander la mise à jour de PostgreSQL

Contactez votre hébergeur pour demander une mise à jour vers PostgreSQL 13 ou supérieur.

**Note** : Cela peut ne pas être possible sur un hébergement mutualisé.

---

### ⚠️ Solution 3 : Downgrader Django (NON RECOMMANDÉ)

Vous pourriez downgrader Django à la version 3.2 (dernière version supportant PostgreSQL 9.6), mais vous perdrez les fonctionnalités récentes.

**Ne faites cela que si les autres solutions ne fonctionnent pas.**

---

## 🚀 Solution rapide : Utiliser MySQL

La solution la plus rapide est d'utiliser MySQL/MariaDB. Suivez les étapes ci-dessus.

---

## 📝 Checklist après migration vers MySQL

- [ ] Base de données MySQL créée dans cPanel
- [ ] Utilisateur créé avec tous les privilèges
- [ ] Fichier `.env` mis à jour avec les identifiants MySQL
- [ ] `mysqlclient` ou `PyMySQL` installé
- [ ] `config/settings.py` modifié pour supporter MySQL
- [ ] Migrations appliquées : `python manage.py migrate`
- [ ] Superutilisateur créé : `python manage.py createsuperuser`

---

## 🔍 Vérification

Après la migration, testez la connexion :

```bash
python manage.py dbshell
```

Si vous voyez le prompt MySQL, c'est que tout fonctionne !

