# 🔒 Résolution de l'erreur SSL : ERR_CERT_COMMON_NAME_INVALID

## 🚨 Problème

Vous rencontrez l'erreur :
```
Votre connexion n'est pas privée
ERR_CERT_COMMON_NAME_INVALID
```

Cette erreur signifie que le **certificat SSL installé ne correspond pas au domaine** `ftp.navixtechnology.com`.

---

## ✅ Solutions

### Solution 1 : Installer un certificat SSL pour `ftp.navixtechnology.com` (Recommandé)

#### Étape 1 : Accéder à cPanel
1. Connectez-vous à votre cPanel
2. Allez dans **"SSL/TLS"** ou **"Let's Encrypt SSL"**

#### Étape 2 : Installer un certificat Let's Encrypt (Gratuit)
1. Dans la section **"Let's Encrypt SSL"** :
   - Sélectionnez le domaine : `ftp.navixtechnology.com`
   - Cliquez sur **"Issue"** ou **"Install"**
2. Attendez 2-5 minutes que le certificat soit généré et installé

#### Étape 3 : Vérifier l'installation
1. Retournez dans **"SSL/TLS"**
2. Allez dans **"Manage SSL Sites"**
3. Vérifiez que `ftp.navixtechnology.com` apparaît avec un certificat valide

#### Étape 4 : Activer HTTPS
1. Dans **"SSL/TLS"**, allez dans **"Force HTTPS Redirect"**
2. Sélectionnez `ftp.navixtechnology.com`
3. Activez la redirection HTTPS
4. Cliquez sur **"Save"**

#### Étape 5 : Redémarrer l'application
1. Allez dans **"Setup Python App"** ou **"Passenger"**
2. Cliquez sur votre application
3. Cliquez sur **"Restart"**

---

### Solution 2 : Utiliser comparateurdeprix.com (RECOMMANDÉ)

Vous avez `comparateurdeprix.com` et `www.comparateurdeprix.com` qui ont probablement déjà des certificats SSL valides. C'est la **solution la plus simple** !

> 📖 **Guide complet** : Consultez [`docs/CONFIGURATION_DOMAINE_COMPARATEURDEPRIX.md`](CONFIGURATION_DOMAINE_COMPARATEURDEPRIX.md) pour un guide détaillé.

#### Option A : Utiliser le domaine principal directement

1. **Configurer Passenger** pour utiliser `comparateurdeprix.com`
2. **Mettre à jour le fichier `.env`** :
```bash
DJANGO_ALLOWED_HOSTS=comparateurdeprix.com,www.comparateurdeprix.com
BACKEND_URL=https://comparateurdeprix.com
```
3. **Tester** : `https://comparateurdeprix.com/api/health/`

#### Option B : Créer un sous-domaine API (Recommandé)

1. **Créer le sous-domaine** `api.comparateurdeprix.com` dans cPanel
2. **Installer un certificat SSL** pour ce sous-domaine
3. **Configurer Passenger** pour ce sous-domaine
4. **Mettre à jour le fichier `.env`** :
```bash
DJANGO_ALLOWED_HOSTS=api.comparateurdeprix.com,comparateurdeprix.com,www.comparateurdeprix.com
BACKEND_URL=https://api.comparateurdeprix.com
```
5. **Tester** : `https://api.comparateurdeprix.com/api/health/`

---

### Solution 3 : Vérifier et corriger le certificat existant

#### Étape 1 : Vérifier le certificat actuel

Dans cPanel :
1. Allez dans **"SSL/TLS"** → **"Manage SSL Sites"**
2. Vérifiez quel domaine est associé au certificat
3. Notez les domaines listés dans le certificat

#### Étape 2 : Ajouter `ftp.navixtechnology.com` au certificat

Si vous avez un certificat multi-domaine :
1. Dans **"Manage SSL Sites"**, cliquez sur **"Edit"**
2. Ajoutez `ftp.navixtechnology.com` aux domaines autorisés
3. Sauvegardez

#### Étape 3 : Réinstaller le certificat

Si le certificat ne peut pas être modifié :
1. Supprimez l'ancien certificat pour `ftp.navixtechnology.com`
2. Réinstallez un nouveau certificat Let's Encrypt (voir Solution 1)

---

### Solution 4 : Solution temporaire (DÉCONSEILLÉ en production)

⚠️ **ATTENTION** : Cette solution désactive HTTPS temporairement. À utiliser uniquement pour tester.

#### Étape 1 : Désactiver HTTPS dans Django

Dans votre fichier `.env` sur le serveur :
```bash
# Temporairement, désactiver le redirect HTTPS
# (Modifiez config/settings.py si nécessaire)
```

#### Étape 2 : Utiliser HTTP temporairement

Accédez à votre API via HTTP :
```
http://ftp.navixtechnology.com/api/health/
```

⚠️ **Important** : Réactivez HTTPS dès que possible pour la sécurité !

---

## 🔍 Diagnostic

### Vérifier le certificat SSL actuel

#### Via navigateur
1. Ouvrez `https://ftp.navixtechnology.com`
2. Cliquez sur l'icône de cadenas dans la barre d'adresse
3. Cliquez sur **"Certificat"** ou **"Certificate"**
4. Vérifiez le **"Subject"** ou **"Common Name"** du certificat

#### Via ligne de commande (SSH)
```bash
# Vérifier le certificat
openssl s_client -connect ftp.navixtechnology.com:443 -servername ftp.navixtechnology.com

# Vérifier les domaines autorisés (SAN)
echo | openssl s_client -connect ftp.navixtechnology.com:443 2>/dev/null | openssl x509 -noout -text | grep -A 1 "Subject Alternative Name"
```

### Vérifier la configuration DNS

Assurez-vous que `ftp.navixtechnology.com` pointe vers votre serveur :
```bash
# Vérifier le DNS
nslookup ftp.navixtechnology.com
# ou
dig ftp.navixtechnology.com
```

---

## 📋 Checklist de résolution

- [ ] Certificat SSL installé pour `ftp.navixtechnology.com` dans cPanel
- [ ] Certificat Let's Encrypt valide et non expiré
- [ ] HTTPS activé dans cPanel (Force HTTPS Redirect)
- [ ] Application redémarrée après installation du certificat
- [ ] DNS configuré correctement pour `ftp.navixtechnology.com`
- [ ] Test de connexion HTTPS réussi : `https://ftp.navixtechnology.com/api/health/`
- [ ] Pas d'erreur de certificat dans le navigateur

---

## 🚀 Après résolution

Une fois le certificat SSL installé et configuré :

### 1. Tester la connexion HTTPS
```bash
# Via curl
curl https://ftp.navixtechnology.com/api/health/

# Via navigateur
https://ftp.navixtechnology.com/api/health/
```

### 2. Vérifier que tout fonctionne
- ✅ Health Check : `https://ftp.navixtechnology.com/api/health/`
- ✅ Swagger : `https://ftp.navixtechnology.com/api/docs/`
- ✅ Admin : `https://ftp.navixtechnology.com/admin/`

### 3. Mettre à jour votre frontend
Assurez-vous que votre frontend utilise `https://ftp.navixtechnology.com` pour les appels API.

---

## 🆘 Si le problème persiste

### Contactez votre hébergeur

Si vous ne pouvez pas installer de certificat SSL :
1. Contactez le support de votre hébergeur cPanel
2. Demandez l'installation d'un certificat SSL pour `ftp.navixtechnology.com`
3. Vérifiez si AutoSSL est activé sur votre compte

### Vérifier les logs

```bash
# Logs d'erreur Apache
tail -f /usr/local/apache/logs/error_log

# Logs SSL
tail -f /usr/local/apache/logs/ssl_error_log
```

### Alternatives

Si l'installation d'un certificat SSL n'est pas possible :
1. Utilisez un autre domaine avec certificat valide
2. Configurez un sous-domaine (ex: `api.comparateurdeprix.com`)
3. Utilisez un service de proxy SSL (Cloudflare, etc.)

---

## 📞 Support

Si vous avez besoin d'aide supplémentaire :
1. Vérifiez les logs d'erreur
2. Contactez le support de votre hébergeur
3. Consultez la documentation cPanel sur SSL/TLS

