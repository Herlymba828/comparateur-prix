# 🌐 Configuration du Backend avec comparateurdeprix.com

## 📋 Domaines disponibles

D'après votre configuration, vous avez ces domaines :
- `comparateurdeprix.com` ✅ (probablement avec certificat SSL)
- `www.comparateurdeprix.com` ✅ (probablement avec certificat SSL)
- `ftp.navixtechnology.com` ❌ (pas de certificat SSL valide)

---

## ✅ Solution Recommandée : Utiliser comparateurdeprix.com

### Option 1 : Utiliser le domaine principal (Simple)

Utilisez `comparateurdeprix.com` ou `www.comparateurdeprix.com` directement pour votre backend.

#### Étape 1 : Configurer le domaine dans cPanel

1. Dans cPanel, allez dans **"Subdomains"** ou **"Addon Domains"**
2. Vérifiez que `comparateurdeprix.com` pointe vers :
   - `/home/rs2694021ez6eg8n/public_html/comparer`
   - OU `/home/rs2694021ez6eg8n/public_html/` (selon votre configuration)

#### Étape 2 : Vérifier le certificat SSL

1. Dans cPanel → **SSL/TLS** → **Manage SSL Sites**
2. Vérifiez que `comparateurdeprix.com` et `www.comparateurdeprix.com` ont des certificats SSL valides
3. Si pas de certificat, installez-en un via **Let's Encrypt SSL**

#### Étape 3 : Configurer Passenger pour comparateurdeprix.com

1. Dans cPanel → **Setup Python App** ou **Passenger**
2. Créez/modifiez l'application :
   - **App Root** : `/home/rs2694021ez6eg8n/public_html/comparer`
   - **App URL** : `/` (ou `/api` si vous préférez)
   - **Python Version** : `3.11`
   - **Application File** : `passenger_wsgi.py`
   - **Domain** : `comparateurdeprix.com` (si l'option est disponible)

#### Étape 4 : Mettre à jour le fichier .env

Sur le serveur, modifiez le fichier `.env` :

```bash
# Django
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,comparateurdeprix.com,www.comparateurdeprix.com

# CSRF
CSRF_TRUSTED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:8000,http://127.0.0.1:8000

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000

# Frontend/Backend
FRONTEND_URL=https://comparateurdeprix.com
BACKEND_URL=https://comparateurdeprix.com
PUBLIC_BASE_URL=https://comparateurdeprix.com
SITE_URL=https://comparateurdeprix.com
```

#### Étape 5 : Redémarrer l'application

1. Dans cPanel → **Setup Python App**
2. Cliquez sur votre application
3. Cliquez sur **"Restart"**

#### Étape 6 : Tester

Testez ces URLs :
- `https://comparateurdeprix.com/api/health/`
- `https://comparateurdeprix.com/api/docs/`
- `https://www.comparateurdeprix.com/api/health/`

---

### Option 2 : Créer un sous-domaine API (Recommandé pour séparation)

Créez un sous-domaine dédié pour l'API : `api.comparateurdeprix.com`

#### Étape 1 : Créer le sous-domaine dans cPanel

1. Dans cPanel → **Subdomains**
2. Créez un nouveau sous-domaine :
   - **Subdomain** : `api`
   - **Domain** : `comparateurdeprix.com`
   - **Document Root** : `/home/rs2694021ez6eg8n/public_html/comparer`
   - Cliquez sur **"Create"**

#### Étape 2 : Installer un certificat SSL pour le sous-domaine

1. Dans cPanel → **SSL/TLS** → **Let's Encrypt SSL**
2. Sélectionnez `api.comparateurdeprix.com`
3. Cliquez sur **"Issue"** ou **"Install"**
4. Attendez 2-5 minutes

#### Étape 3 : Configurer Passenger pour le sous-domaine

1. Dans cPanel → **Setup Python App** ou **Passenger**
2. Créez une nouvelle application :
   - **App Root** : `/home/rs2694021ez6eg8n/public_html/comparer`
   - **App URL** : `/` (ou laissez vide)
   - **Python Version** : `3.11`
   - **Application File** : `passenger_wsgi.py`
   - **Domain** : `api.comparateurdeprix.com` (si disponible)

#### Étape 4 : Mettre à jour le fichier .env

```bash
# Django
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,api.comparateurdeprix.com,comparateurdeprix.com,www.comparateurdeprix.com

# CSRF
CSRF_TRUSTED_ORIGINS=https://api.comparateurdeprix.com,https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:8000,http://127.0.0.1:8000

# CORS
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://comparateurdeprix.com,https://www.comparateurdeprix.com,http://localhost:3000,http://127.0.0.1:3000

# Frontend/Backend
FRONTEND_URL=https://comparateurdeprix.com
BACKEND_URL=https://api.comparateurdeprix.com
PUBLIC_BASE_URL=https://comparateurdeprix.com
SITE_URL=https://comparateurdeprix.com
```

#### Étape 5 : Redémarrer l'application

1. Dans cPanel → **Setup Python App**
2. Cliquez sur votre application
3. Cliquez sur **"Restart"**

#### Étape 6 : Tester

Testez ces URLs :
- `https://api.comparateurdeprix.com/api/health/`
- `https://api.comparateurdeprix.com/api/docs/`

---

## 🔄 Migration depuis ftp.navixtechnology.com

Si vous migrez depuis `ftp.navixtechnology.com` :

### Étape 1 : Sauvegarder la configuration actuelle

```bash
# Sur le serveur, sauvegardez le .env actuel
cp .env .env.backup
```

### Étape 2 : Mettre à jour le fichier .env

Modifiez le fichier `.env` avec les nouvelles valeurs (voir Option 1 ou 2 ci-dessus).

### Étape 3 : Vérifier la configuration Django

```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Vérifier la configuration
cd /home/rs2694021ez6eg8n/public_html/comparer
python manage.py check --deploy
```

### Étape 4 : Redémarrer l'application

Dans cPanel → **Setup Python App** → **Restart**

### Étape 5 : Tester

Testez les nouvelles URLs pour vérifier que tout fonctionne.

---

## 📋 Checklist de Configuration

### Pour Option 1 (Domaine principal)
- [ ] `comparateurdeprix.com` pointe vers le bon répertoire
- [ ] Certificat SSL installé pour `comparateurdeprix.com`
- [ ] Certificat SSL installé pour `www.comparateurdeprix.com`
- [ ] Passenger configuré pour `comparateurdeprix.com`
- [ ] Fichier `.env` mis à jour avec les nouveaux domaines
- [ ] Application redémarrée
- [ ] Test réussi : `https://comparateurdeprix.com/api/health/`

### Pour Option 2 (Sous-domaine API)
- [ ] Sous-domaine `api.comparateurdeprix.com` créé
- [ ] Certificat SSL installé pour `api.comparateurdeprix.com`
- [ ] Passenger configuré pour `api.comparateurdeprix.com`
- [ ] Fichier `.env` mis à jour avec le sous-domaine
- [ ] Application redémarrée
- [ ] Test réussi : `https://api.comparateurdeprix.com/api/health/`

---

## 🚨 Dépannage

### Le certificat SSL n'est pas valide

**Solution** :
1. Dans cPanel → **SSL/TLS** → **Let's Encrypt SSL**
2. Supprimez l'ancien certificat
3. Réinstallez un nouveau certificat

### Le domaine ne pointe pas vers le bon répertoire

**Solution** :
1. Dans cPanel → **Subdomains** ou **Addon Domains**
2. Modifiez le **Document Root** pour pointer vers `/home/rs2694021ez6eg8n/public_html/comparer`

### Erreur 404 sur les nouvelles URLs

**Solution** :
1. Vérifiez que Passenger est configuré pour le bon domaine
2. Vérifiez que `passenger_wsgi.py` est dans le bon répertoire
3. Redémarrez l'application dans cPanel

### Erreur ALLOWED_HOSTS

**Solution** :
Vérifiez que le nouveau domaine est dans `DJANGO_ALLOWED_HOSTS` dans le fichier `.env`

---

## 🎯 Recommandation

**Je recommande l'Option 2 (Sous-domaine API)** car :
- ✅ Séparation claire entre frontend et backend
- ✅ Meilleure organisation
- ✅ Plus facile à maintenir
- ✅ Permet d'avoir le frontend sur `comparateurdeprix.com` et l'API sur `api.comparateurdeprix.com`

Mais si vous préférez la simplicité, l'Option 1 fonctionne aussi très bien !

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs : `tail -f error_log`
2. Vérifiez la configuration dans cPanel
3. Contactez le support de votre hébergeur si nécessaire

