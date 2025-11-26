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

#### Étape 1 : Configurer le domaine sur Railway

1. Dans Railway, allez dans votre projet
2. Ajoutez un domaine personnalisé : `comparateurdeprix.com`
3. Railway configure automatiquement le certificat SSL via Let's Encrypt

#### Étape 3 : Configurer le domaine sur Railway

1. Dans Railway, allez dans votre projet
2. Ajoutez un domaine personnalisé : `comparateurdeprix.com`
3. Railway configure automatiquement le certificat SSL

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

Railway redémarre automatiquement après chaque déploiement.

#### Étape 6 : Tester

Testez ces URLs :
- `https://comparateurdeprix.com/api/health/`
- `https://comparateurdeprix.com/api/docs/`
- `https://www.comparateurdeprix.com/api/health/`

---

### Option 2 : Créer un sous-domaine API (Recommandé pour séparation)

Créez un sous-domaine dédié pour l'API : `api.comparateurdeprix.com`

#### Étape 1 : Créer le sous-domaine sur Railway

1. Dans Railway, allez dans votre projet
2. Ajoutez un domaine personnalisé : `api.comparateurdeprix.com`
3. Railway configure automatiquement le certificat SSL via Let's Encrypt

#### Étape 2 : Mettre à jour le fichier .env

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

Railway redémarre automatiquement après chaque déploiement.

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
- [ ] Domaine configuré sur Railway pour `comparateurdeprix.com`
- [ ] Fichier `.env` mis à jour avec les nouveaux domaines
- [ ] Application redémarrée
- [ ] Test réussi : `https://comparateurdeprix.com/api/health/`

### Pour Option 2 (Sous-domaine API)
- [ ] Sous-domaine `api.comparateurdeprix.com` créé
- [ ] Certificat SSL installé pour `api.comparateurdeprix.com`
- [ ] Domaine configuré sur Railway pour `api.comparateurdeprix.com`
- [ ] Fichier `.env` mis à jour avec le sous-domaine
- [ ] Application redémarrée
- [ ] Test réussi : `https://api.comparateurdeprix.com/api/health/`

---

## 🚨 Dépannage

### Le certificat SSL n'est pas valide

**Solution** :
1. Dans Railway, vérifiez la configuration du domaine
2. Railway gère automatiquement les certificats SSL via Let's Encrypt
3. Si nécessaire, supprimez et réajoutez le domaine

### Erreur 404 sur les nouvelles URLs

**Solution** :
1. Vérifiez que le domaine est bien configuré dans Railway
2. Vérifiez que le service est déployé et actif
3. Attendez quelques minutes pour la propagation DNS

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
1. Vérifiez les logs dans Railway : `railway logs`
2. Vérifiez la configuration du domaine dans Railway
3. Consultez la documentation Railway si nécessaire

