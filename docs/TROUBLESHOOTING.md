# 🔧 Guide de Dépannage

Ce guide regroupe toutes les solutions aux erreurs courantes rencontrées dans le projet.

## 📋 Table des matières

- [Erreurs de Base de Données](#erreurs-de-base-de-données)
- [Erreurs d'Environnement](#erreurs-denvironnement)
- [Erreurs API](#erreurs-api)
- [Erreurs Railway](#erreurs-railway)
- [Erreurs de Build/Dépendances](#erreurs-de-builddépendances)

---

## 🗄️ Erreurs de Base de Données

### PostgreSQL : Version incompatible

**Erreur :**
```
django.db.utils.NotSupportedError: PostgreSQL 13 or later is required (found 9.622).
```

**Solution :** Utiliser MySQL/MariaDB (voir section [Migration vers MySQL](#migration-vers-mysql))

---

### MySQL : Erreur mysqlclient

**Erreur :**
```
error: Can not find valid pkg-config name.
Exception: Can not find valid pkg-config name.
Specify MYSQLCLIENT_CFLAGS and MYSQLCLIENT_LDFLAGS env vars manually
```

**Cause :** `mysqlclient==2.2.0` nécessite des bibliothèques système MySQL (`libmysqlclient-dev`) qui ne sont pas disponibles dans l'environnement Railway.

**Solution :** Sur Railway, vous utilisez PostgreSQL via `DATABASE_URL`, donc `mysqlclient` n'est pas nécessaire. Dans `requirements.txt`, `mysqlclient` est maintenant commenté. Utilisez `PyMySQL` si vous avez besoin de MySQL.

**Configuration :**
```txt
# mysqlclient nécessite des bibliothèques système MySQL (non disponible sur Railway)
# Utilisez PyMySQL à la place si vous avez besoin de MySQL
# mysqlclient==2.2.0  # Décommentez seulement si vous avez les dépendances système
PyMySQL==1.1.0
```

---

### Erreur : POSTGRES_PASSWORD must be set in production

**Erreur :**
```
django.core.exceptions.ImproperlyConfigured: POSTGRES_PASSWORD must be set in production
```

**Solutions :**

1. **Vérifier le format du fichier .env**
   - Pas d'espaces autour du `=`
   - Pas de guillemets sauf si nécessaire
   - Format correct : `DB_PASSWORD=BlackEurtz8282@`

2. **Vérifier l'emplacement du fichier .env**
   - Doit être à la racine du projet Django
   - Vérifier : `ls -la .env`

3. **Vérifier les permissions**
   ```bash
   chmod 600 .env
   ```

4. **Tester la lecture du fichier**
   ```bash
   python -c "from dotenv import load_dotenv; import os; from pathlib import Path; load_dotenv(Path('.env')); print('DB_PASSWORD:', os.getenv('DB_PASSWORD'))"
   ```

5. **Utiliser une variable alternative**
   - Si `DB_PASSWORD` ne fonctionne pas, essayez `MYSQL_PASSWORD` dans `.env`

---

### Migration vers MySQL

Si votre serveur utilise PostgreSQL 9.622 (trop ancien), migrez vers MySQL :

**Étapes :**

1. **Créer la base de données MySQL**
   - Créer une nouvelle base de données MySQL dans cPanel
   - Créer un utilisateur avec tous les privilèges

2. **Installer les dépendances**
   ```bash
   pip install mysqlclient
   # Ou si mysqlclient échoue :
   pip install PyMySQL
   ```

3. **Mettre à jour .env**
   ```bash
   DB_ENGINE=mysql
   DB_NAME=rs2694021ez6eg8n_comparer
   DB_USER=rs2694021ez6eg8n_dbuser
   DB_PASSWORD=votre_mot_de_passe_mysql
   DB_HOST=localhost
   DB_PORT=3306
   ```

4. **Appliquer les migrations**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

5. **Tester la connexion**
   ```bash
   python manage.py dbshell
   ```

---

## 🐍 Erreurs d'Environnement

### Erreur d'environnement virtuel

**Erreur :**
```
Fatal error in launcher: Unable to create process using '"C:\Users\herly\Downloads\soutenance2.0\venv\Scripts\python.exe"'
```

**Cause :** L'environnement virtuel pointe vers un ancien chemin Python qui n'existe plus.

**Solutions :**

1. **Utiliser python -m pip (Rapide)**
   ```powershell
   python -m pip install -r requirements-dev.txt
   ```

2. **Réinstaller pip dans l'environnement virtuel**
   ```powershell
   .\venv\Scripts\Activate.ps1
   python -m ensurepip --upgrade
   python -m pip install -r requirements-dev.txt
   ```

3. **Recréer l'environnement virtuel (Recommandé)**
   ```powershell
   deactivate
   Remove-Item -Recurse -Force venv
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   python -m pip install -r requirements-dev.txt
   ```

**Vérification :**
```powershell
pip --version
where python  # Doit pointer vers venv\Scripts\python.exe
```

---

## 🔌 Erreurs API

### Erreurs Serveur (HTTP 500)

**Causes possibles :**
1. Base de données vide ou mal configurée
2. Annotations de prix manquantes dans les requêtes
3. Relations ForeignKey non résolues
4. Erreurs dans les serializers

**Solutions :**

1. **Remplir la base de données**
   ```bash
   # Seed avec données de test
   railway run python manage.py seed_data --produits 100 --magasins 5
   
   # Ou scraper des données réelles
   railway run python manage.py scrape_dgccrf --limit 100
   ```

2. **Vérifier les données**
   ```bash
   railway run python manage.py shell -c "
   from apps.produits.models import Produit, Prix, Categorie
   print(f'Produits: {Produit.objects.count()}')
   print(f'Prix: {Prix.objects.count()}')
   print(f'Catégories: {Categorie.objects.count()}')
   print(f'Produits sans catégorie: {Produit.objects.filter(categorie__isnull=True).count()}')
   "
   ```

3. **Vérifier les migrations**
   ```bash
   railway run python manage.py showmigrations
   railway run python manage.py migrate
   ```

4. **Initialiser les catégories**
   ```bash
   railway run python manage.py init_categories
   ```

### Erreur 500 sur POST /api/utilisateurs/

**Symptôme :** Le client reçoit du HTML au lieu de JSON

**Solutions :**

1. **Récupérer les logs Railway**
   ```powershell
   railway logs --tail 200 | Select-String -Pattern "utilisateurs|ERROR|Exception|Traceback|500"
   ```

2. **Activer temporairement DEBUG (pour déboguer uniquement)**
   - Dans Railway → Variables : `DJANGO_DEBUG=True`
   - Redéployer
   - Tester
   - **IMPORTANT :** Remettre `DJANGO_DEBUG=False` après !

3. **Vérifier les erreurs communes :**
   - "UNIQUE constraint failed: utilisateurs.email" → Email déjà existant
   - "RelatedObjectDoesNotExist: Utilisateur has no profil" → Signal non déclenché
   - "IntegrityError: NOT NULL constraint failed" → Champ requis manquant

### Erreurs HTML au lieu de JSON

**Cause :** Gestion d'erreurs retournant du HTML au lieu de JSON

**Solution :** Le middleware `JSONExceptionMiddleware` intercepte toutes les exceptions pour les requêtes API (`/api/*`), garantissant que toutes les erreurs retournent du JSON.

---

## 🚂 Erreurs Railway

### railway run se connecte à la base locale

**Erreur :**
```
psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 5432 failed
```

**Causes possibles :**
1. Railway CLI n'est pas correctement lié au projet
2. Les variables d'environnement Railway ne sont pas chargées
3. Le fichier `.railway` n'existe pas ou est incorrect

**Solutions :**

1. **Vérifier et lier le projet Railway**
   ```bash
   railway status
   railway login
   railway link
   ```

2. **Utiliser Railway Dashboard (Recommandé)**
   - Allez sur https://railway.app
   - Ouvrez votre projet
   - Utilisez le terminal intégré dans l'onglet "Deployments" → "Terminal"

3. **Vérifier les variables d'environnement**
   ```bash
   railway variables
   railway variables | grep DATABASE_URL
   ```

4. **Exécuter via le service Railway**
   ```bash
   railway service
   railway run --service <service-name> python manage.py migrate
   ```

**Note :** Les commandes `railway run` depuis votre machine locale nécessitent que Railway CLI soit correctement configuré. Utilisez plutôt le **Railway Dashboard Terminal** qui garantit l'accès à toutes les variables d'environnement.

---

## 📦 Erreurs de Build/Dépendances

### Erreur mysqlclient sur Railway

**Solution :** `mysqlclient` est maintenant commenté dans `requirements.txt`. Railway utilise PostgreSQL via `DATABASE_URL`, donc `mysqlclient` n'est pas nécessaire.

**Configuration actuelle :**
- Railway : Utilise PostgreSQL via DATABASE_URL (pas besoin de mysqlclient)
- MySQL : Utilise PyMySQL (pas besoin de mysqlclient)
- Pas d'erreur de build sur Railway

---

## 🔍 Diagnostic des Erreurs 500

### Diagnostic Rapide sur Railway

1. **Tester les endpoints directement**
   ```bash
   railway run python manage.py shell -c "
   from django.test import Client
   client = Client()
   response = client.get('/api/produits/produits/')
   print(f'Status: {response.status_code}')
   "
   ```

2. **Vérifier les données de la base**
   ```bash
   railway run python manage.py shell -c "
   from apps.produits.models import Produit, Prix, Categorie
   print(f'Produits: {Produit.objects.count()}')
   print(f'Prix: {Prix.objects.count()}')
   print(f'Catégories: {Categorie.objects.count()}')
   "
   ```

3. **Vérifier les problèmes de relations**
   ```bash
   railway run python manage.py shell -c "
   from apps.produits.models import Produit, Prix
   print(f'Produits sans catégorie: {Produit.objects.filter(categorie__isnull=True).count()}')
   print(f'Prix sans produit: {Prix.objects.filter(produit__isnull=True).count()}')
   "
   ```

### Causes Communes des Erreurs 500

1. **Base de Données Vide**
   - Solution : `railway run python manage.py seed_data --produits 100 --magasins 5`

2. **Annotations Retournant None**
   - Solution : Les annotations ont été corrigées pour gérer les valeurs None

3. **Relations ForeignKey NULL**
   - Solution : Vérifier et corriger les données manquantes

4. **Problèmes de Serializer**
   - Solution : Les serializers ont été améliorés pour gérer les valeurs None

### Voir les Erreurs dans les Logs

**PowerShell :**
```powershell
# Filtrer les erreurs produits
railway logs --tail 500 | Select-String -Pattern "\[PRODUITS\].*ERROR" -CaseSensitive:$false

# Filtrer toutes les erreurs
railway logs --tail 500 | Select-String -Pattern "ERROR|Exception|Traceback" -CaseSensitive:$false
```

---

## 📋 Checklist de Diagnostic Général

### Étape 1 : Vérifier les Données
```bash
railway run python manage.py shell -c "
from apps.produits.models import Produit, Prix, Categorie
print('=== Statistiques ===')
print(f'Produits: {Produit.objects.count()}')
print(f'Prix: {Prix.objects.count()}')
print(f'Catégories: {Categorie.objects.count()}')
"
```

### Étape 2 : Tester un Endpoint Simple
```bash
curl https://comparo.up.railway.app/api/produits/categories/
```

### Étape 3 : Vérifier les Migrations
```bash
railway run python manage.py showmigrations
railway run python manage.py migrate
```

### Étape 4 : Vérifier les Logs
```powershell
railway logs --tail 200 | Select-String -Pattern "ERROR|Exception|500" -CaseSensitive:$false
```

---

## 🎯 Solutions Rapides

### Si la Base est Vide
```bash
# Option 1: Seed avec données de test
railway run python manage.py seed_data --produits 50 --magasins 3

# Option 2: Scraper des données réelles
railway run python manage.py scrape_dgccrf --limit 50
```

### Si les Catégories Manquent
```bash
railway run python manage.py init_categories
```

### Si les Relations sont Cassées
```bash
railway run python manage.py shell
# Corriger manuellement via le shell
```

---

## 🔒 Erreurs SSL

### ERR_CERT_COMMON_NAME_INVALID

**Erreur** :
```
Votre connexion n'est pas privée
ERR_CERT_COMMON_NAME_INVALID
```

**Cause** : Le certificat SSL installé ne correspond pas au domaine utilisé.

#### Solutions

**Solution 1 : Installer un certificat SSL pour le domaine (Recommandé)**

1. Accéder à cPanel → **"SSL/TLS"** ou **"Let's Encrypt SSL"**
2. Sélectionner le domaine
3. Cliquer sur **"Issue"** ou **"Install"**
4. Attendre 2-5 minutes que le certificat soit généré
5. Activer HTTPS dans **"Force HTTPS Redirect"**
6. Redémarrer l'application

**Solution 2 : Utiliser un domaine avec certificat valide**

Si vous avez un autre domaine avec certificat SSL valide (ex: `comparateurdeprix.com`), utilisez-le à la place.

**Solution 3 : Vérifier le certificat actuel**

Via navigateur :
1. Ouvrir `https://votre-domaine.com`
2. Cliquer sur l'icône de cadenas
3. Vérifier le **"Subject"** ou **"Common Name"** du certificat

Via ligne de commande :
```bash
openssl s_client -connect votre-domaine.com:443 -servername votre-domaine.com
```

### Erreur SSL avec Railway

**Erreur** :
```
psycopg.OperationalError: connection failed: connection to server at "127.0.0.1", port 5432 failed: server does not support SSL, but SSL was required
```

**Cause** : L'application essaie de se connecter à localhost au lieu de la base de données Railway, et SSL est forcé.

**Solutions** :

1. **Vérifier que DATABASE_URL est défini** :
   ```bash
   railway run python scripts/check_railway_db.py
   ```

2. **Vérifier que PostgreSQL est créé** :
   - Allez sur Railway
   - Vérifiez que vous avez un service **PostgreSQL**
   - Si ce n'est pas le cas, créez-le : **"+ New"** → **"Database"** → **"Add PostgreSQL"**

3. **Vérifier DATABASE_URL** :
   ```bash
   railway variables | grep DATABASE_URL
   ```

4. **Désactiver SSL pour localhost (si test local)** :
   ```bash
   POSTGRES_SSL_REQUIRE=False
   ```

**Note** : Cette solution est seulement pour le développement local, pas pour Railway.

---

## 📚 Ressources

- [Documentation API](./ENDPOINTS_API.md)
- [Configuration Railway](./CONFIGURATION_RAILWAY.md)
- [Authentification](./AUTHENTIFICATION.md)

---

*Dernière mise à jour : 2025-01-17*

