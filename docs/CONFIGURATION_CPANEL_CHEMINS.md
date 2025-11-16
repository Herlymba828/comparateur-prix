# 🔧 Configuration cPanel avec les Chemins Réels

## 📍 Chemins identifiés

D'après vos informations :
- **Environnement virtuel** : `/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/`
- **Application Django dans cPanel** : `/home/rs2694021ez6eg8n/public_html/comparer`
- **Projet uploadé** : `/home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix`

---

## ✅ Solution : Configurer cPanel pour pointer vers le bon répertoire

### Option 1 : Modifier l'App Root dans cPanel (Recommandé)

#### Étape 1 : Modifier l'application dans cPanel

1. Dans cPanel, allez dans **"Setup Python App"**
2. Cliquez sur votre application existante
3. Modifiez le champ **App Root** :
   - **Ancien** : `/home/rs2694021ez6eg8n/public_html/comparer`
   - **Nouveau** : `/home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix`
4. Vérifiez que **Application File** est : `passenger_wsgi.py`
5. Cliquez sur **"Save"** ou **"Update"**
6. Cliquez sur **"Restart"**

#### Étape 2 : Vérifier que le fichier passenger_wsgi.py est au bon endroit

Le fichier `passenger_wsgi.py` doit être dans :
```
/home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix/passenger_wsgi.py
```

Vérifiez qu'il contient le bon chemin d'environnement virtuel (déjà corrigé dans le fichier).

---

### Option 2 : Déplacer le projet (Alternative)

Si vous préférez avoir le projet directement dans `/home/rs2694021ez6eg8n/public_html/comparer/` :

#### Étape 1 : Déplacer les fichiers

```bash
# Via SSH
cd /home/rs2694021ez6eg8n/public_html/comparer

# Déplacer le contenu de comparateur-prix vers comparer
mv comparateur-prix/* .
mv comparateur-prix/.* . 2>/dev/null  # Déplacer les fichiers cachés

# Supprimer le dossier vide
rmdir comparateur-prix
```

#### Étape 2 : Vérifier dans cPanel

1. Dans cPanel → **Setup Python App**
2. Vérifiez que **App Root** est : `/home/rs2694021ez6eg8n/public_html/comparer`
3. Vérifiez que **Application File** est : `passenger_wsgi.py`
4. Cliquez sur **"Restart"**

---

## 🔍 Vérification des chemins

### Vérifier que tout est au bon endroit

```bash
# Aller dans le répertoire du projet
cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix

# Vérifier que manage.py existe
ls -la manage.py

# Vérifier que passenger_wsgi.py existe
ls -la passenger_wsgi.py

# Vérifier que le fichier .env existe (si configuré)
ls -la .env
```

### Vérifier le chemin dans passenger_wsgi.py

Le fichier `passenger_wsgi.py` doit contenir :

```python
# Activer l'environnement virtuel
activate_this = '/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate_this.py'
```

---

## 📝 Configuration complète dans cPanel

### Dans Setup Python App

1. **App Root** : `/home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix`
2. **App URL** : `/` (ou `/comparateur-prix` si vous préférez)
3. **Python Version** : `3.11`
4. **Application File** : `passenger_wsgi.py`
5. **Virtual Environment** : `/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/`

---

## 🚀 Étapes suivantes

### 1. Installer les dépendances

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Aller dans le projet
cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configurer le fichier .env

```bash
cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix
nano .env
```

Utilisez le contenu de `docs/ENV_PRODUCTION_CORRIGE.md` pour configurer le fichier.

### 3. Appliquer les migrations

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Aller dans le projet
cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur
python manage.py createsuperuser

# Collecter les fichiers statiques
python manage.py collectstatic --noinput
```

### 4. Redémarrer l'application

Dans cPanel → **Setup Python App** → **Restart**

### 5. Tester

- `https://comparateurdeprix.com/api/health/`
- `https://comparateurdeprix.com/api/docs/`

---

## 🚨 Dépannage

### Erreur : "App Root not found"

**Cause** : Le chemin dans cPanel ne correspond pas au répertoire réel

**Solution** :
1. Vérifiez le chemin exact dans File Manager de cPanel
2. Mettez à jour **App Root** dans Setup Python App avec le chemin exact

### Erreur : "passenger_wsgi.py not found"

**Cause** : Le fichier n'est pas dans le répertoire App Root

**Solution** :
```bash
# Vérifier que le fichier existe
ls -la /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix/passenger_wsgi.py

# Si le fichier n'existe pas, créez-le ou copiez-le
```

### Erreur : "Module not found"

**Cause** : Les dépendances ne sont pas installées dans l'environnement virtuel

**Solution** :
```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Installer les dépendances
cd /home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix
pip install -r requirements.txt
```

---

## 📋 Checklist

- [ ] ✅ **App Root** dans cPanel pointe vers `/home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix`
- [ ] ✅ **Application File** est `passenger_wsgi.py`
- [ ] ✅ **Virtual Environment** est `/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/`
- [ ] ✅ Le fichier `passenger_wsgi.py` contient le bon chemin d'environnement virtuel
- [ ] ✅ Le fichier `passenger_wsgi.py` est dans le répertoire du projet
- [ ] ✅ Les dépendances sont installées dans l'environnement virtuel
- [ ] ✅ Le fichier `.env` est configuré
- [ ] ✅ Les migrations sont appliquées
- [ ] ✅ L'application est redémarrée dans cPanel
- [ ] ✅ Les tests passent : Health Check, Swagger, Admin

---

## 🎯 Résumé

**Configuration actuelle** :
- Environnement virtuel : `/home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/`
- Projet : `/home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix`

**Action principale** :
Modifiez **App Root** dans cPanel → Setup Python App pour pointer vers `/home/rs2694021ez6eg8n/public_html/comparer/comparateur-prix`

Le fichier `passenger_wsgi.py` a déjà été mis à jour avec le bon chemin d'environnement virtuel.

