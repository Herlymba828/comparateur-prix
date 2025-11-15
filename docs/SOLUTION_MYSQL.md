# ✅ Solution : Migration vers MySQL/MariaDB

## Problème résolu

Votre serveur utilise PostgreSQL 9.622, qui est trop ancien pour Django 5.1.2. La solution est d'utiliser **MySQL/MariaDB** qui est généralement mieux supporté sur cPanel.

## ✅ Modifications apportées

1. ✅ Support MySQL ajouté dans `config/settings.py`
2. ✅ `mysqlclient` et `PyMySQL` ajoutés à `requirements.txt`
3. ✅ Configuration flexible : supporte PostgreSQL ET MySQL

## 🚀 Étapes à suivre

### Étape 1 : Créer la base de données MySQL dans cPanel

1. Connectez-vous à **cPanel**
2. Allez dans **"MySQL Databases"**
3. Créez une nouvelle base de données :
   - Nom : `comparer` (ou autre)
   - Notez le nom complet : `rs2694021ez6eg8n_comparer`
4. Créez un utilisateur :
   - Nom d'utilisateur : (choisissez un nom)
   - Mot de passe : (choisissez un mot de passe fort)
   - Notez le nom complet : `rs2694021ez6eg8n_dbuser`
5. Ajoutez l'utilisateur à la base de données avec **tous les privilèges**

### Étape 2 : Installer les dépendances MySQL

Sur le serveur (via SSH) :

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate
cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix

# Installer mysqlclient (essayez d'abord celui-ci)
pip install mysqlclient

# Si mysqlclient échoue (erreurs de compilation), utilisez PyMySQL
pip install PyMySQL
```

**Note** : Si `mysqlclient` échoue, utilisez `PyMySQL` qui est plus facile à installer.

### Étape 3 : Mettre à jour le fichier .env

Éditez votre fichier `.env` :

```bash
nano .env
```

**Remplacez** la configuration PostgreSQL par MySQL :

```bash
# Configuration MySQL (remplacez les valeurs PostgreSQL)
DB_ENGINE=mysql
DB_NAME=rs2694021ez6eg8n_comparer
DB_USER=rs2694021ez6eg8n_dbuser
DB_PASSWORD=votre_mot_de_passe_mysql
DB_HOST=localhost
DB_PORT=3306

# Vous pouvez supprimer ou commenter les lignes PostgreSQL :
# POSTGRES_DB=...
# POSTGRES_USER=...
# POSTGRES_PASSWORD=...
```

Sauvegardez : `Ctrl+O`, puis `Enter`, puis `Ctrl+X`

### Étape 4 : Appliquer les migrations

```bash
# Vérifier la configuration
python manage.py check

# Appliquer les migrations
python manage.py migrate

# Si tout fonctionne, créer un superutilisateur
python manage.py createsuperuser
```

### Étape 5 : Tester la connexion

```bash
python manage.py dbshell
```

Si vous voyez le prompt MySQL (`mysql>`), c'est que tout fonctionne ! Tapez `exit` pour quitter.

---

## 🔍 Vérification

### Tester que MySQL fonctionne

```bash
# Dans le shell Django
python manage.py shell
```

Puis dans le shell Python :

```python
from django.db import connection
print(connection.vendor)  # Doit afficher "mysql"
print(connection.get_server_version())  # Affiche la version MySQL
exit()
```

---

## ⚠️ Si vous avez des erreurs

### Erreur : "No module named 'MySQLdb'"

**Solution** : Utilisez PyMySQL au lieu de mysqlclient :

```bash
pip install PyMySQL
```

Le code dans `settings.py` configure automatiquement PyMySQL.

### Erreur : "Access denied for user"

**Solution** : Vérifiez :
1. Les identifiants dans `.env` sont corrects
2. L'utilisateur a bien tous les privilèges sur la base
3. Le nom de la base et de l'utilisateur incluent le préfixe `rs2694021ez6eg8n_`

### Erreur : "Unknown database"

**Solution** : Vérifiez que la base de données existe dans cPanel et que le nom dans `.env` est correct (avec le préfixe).

---

## 📋 Checklist

- [ ] Base de données MySQL créée dans cPanel
- [ ] Utilisateur créé avec tous les privilèges
- [ ] `mysqlclient` ou `PyMySQL` installé
- [ ] Fichier `.env` mis à jour avec `DB_ENGINE=mysql`
- [ ] Migrations appliquées (`python manage.py migrate`)
- [ ] Superutilisateur créé (`python manage.py createsuperuser`)
- [ ] Connexion testée (`python manage.py dbshell`)

---

## 🎉 C'est fait !

Votre application Django utilise maintenant MySQL au lieu de PostgreSQL. Vous pouvez continuer le déploiement normalement.

---

## 💡 Note : Retour à PostgreSQL

Si vous voulez revenir à PostgreSQL plus tard (après mise à jour du serveur), il suffit de :

1. Mettre à jour `.env` :
   ```bash
   DB_ENGINE=postgresql
   DB_NAME=...
   # etc.
   ```

2. Réinstaller psycopg2 :
   ```bash
   pip install psycopg[binary]
   ```

Le code supporte automatiquement les deux bases de données !

