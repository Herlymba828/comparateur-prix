# Guide de Déploiement Rapide - cPanel/WHM

## 🚀 Déploiement en 10 étapes

### Étape 1 : Préparer les fichiers localement

1. **Générer une clé secrète** :
   ```bash
   python scripts/generate_secret_key.py
   ```
   Copiez la clé générée.

2. **Vérifier que ces fichiers existent** :
   - ✅ `.htaccess` (créé)
   - ✅ `passenger_wsgi.py` (créé)
   - ✅ `index.py` (créé)
   - ✅ `requirements.txt`
   - ✅ `runtime.txt`
   - ✅ `.env.example`

### Étape 2 : Uploader les fichiers

**Via FTP/SFTP** :
- Connectez-vous à votre serveur
- Naviguez vers `/home/rs2694021ez6eg8n/public_html/comparer`
- Uploadez tous les fichiers (sauf `venv/`, `__pycache__/`, `.git/`)

**Via Git** (recommandé) :
```bash
cd /home/rs2694021ez6eg8n/public_html/comparer
git clone https://votre-repo.git .
```

### Étape 3 : Se connecter en SSH

```bash
ssh votre-utilisateur@ftp.navixtechnology.com
```

### Étape 4 : Activer l'environnement virtuel

```bash
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate
cd /home/rs2694021ez6eg8n/public_html/comparer
```

### Étape 5 : Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Étape 6 : Créer le fichier .env

```bash
cp .env.example .env
nano .env
```

**Remplissez avec vos vraies valeurs** :
- `DJANGO_SECRET_KEY` : La clé générée à l'étape 1
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` : Vos identifiants de base de données
- `DJANGO_ALLOWED_HOSTS` : `ftp.navixtechnology.com,www.ftp.navixtechnology.com`

Sauvegardez : `Ctrl+O`, puis `Ctrl+X`

### Étape 7 : Configurer la base de données

Dans cPanel :
1. Allez dans **"PostgreSQL Databases"** (ou **"MySQL Databases"**)
2. Créez une base de données
3. Créez un utilisateur avec tous les privilèges
4. Notez les identifiants et mettez-les dans `.env`

### Étape 8 : Appliquer les migrations

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### Étape 9 : Configurer Passenger dans cPanel

1. Allez dans **"Setup Python App"** ou **"Passenger"**
2. Configurez :
   - **App Root**: `/home/rs2694021ez6eg8n/public_html/comparer`
   - **App URL**: `/`
   - **Python Version**: 3.11
   - **Application File**: `passenger_wsgi.py`

3. Cliquez sur **"Restart"**

### Étape 10 : Tester

Visitez dans votre navigateur :
- `https://ftp.navixtechnology.com/api/docs/` (Swagger)
- `https://ftp.navixtechnology.com/admin/` (Admin Django)

---

## 🔧 Script de déploiement automatique

Pour automatiser les étapes 4-8, utilisez :

```bash
bash scripts/deploy_cpanel.sh
```

---

## ⚠️ Problèmes courants

### Erreur 500
- Vérifiez les logs : `tail -f error_log`
- Vérifiez que `.env` existe et est correct
- Vérifiez les permissions : `chmod 755 manage.py`

### Module not found
- Réinstallez : `pip install -r requirements.txt`
- Vérifiez que l'environnement virtuel est activé

### Erreur de base de données
- Vérifiez les identifiants dans `.env`
- Testez la connexion : `python manage.py dbshell`

---

## 📚 Documentation complète

Pour plus de détails, consultez : `docs/DEPLOIEMENT_CPANEL.md`

---

## ✅ Checklist finale

- [ ] Fichiers uploadés
- [ ] Environnement virtuel activé
- [ ] Dépendances installées
- [ ] Fichier `.env` configuré
- [ ] Base de données créée
- [ ] Migrations appliquées
- [ ] Superutilisateur créé
- [ ] Fichiers statiques collectés
- [ ] Passenger configuré
- [ ] SSL/HTTPS activé
- [ ] Application accessible

