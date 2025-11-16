# 🔍 Guide de Vérification du Backend

Ce guide vous permet de vérifier que votre backend Django fonctionne correctement sur le serveur de production.

## 📋 Méthodes de Vérification

### Méthode 1 : Tests via Navigateur (Le plus simple)

Ouvrez votre navigateur et testez ces URLs :

#### ✅ 1. Test de santé (Health Check)
```
https://ftp.navixtechnology.com/api/health/
```
**Résultat attendu** : `{"status": "ok"}`

#### ✅ 2. Test de connexion
```
https://ftp.navixtechnology.com/api/test-connection/
```
**Résultat attendu** : JSON avec `status: "success"` et message de confirmation

#### ✅ 3. Documentation Swagger
```
https://ftp.navixtechnology.com/api/docs/
```
**Résultat attendu** : Interface Swagger avec tous les endpoints disponibles

#### ✅ 4. Admin Django
```
https://ftp.navixtechnology.com/admin/
```
**Résultat attendu** : Page de connexion de l'admin Django

#### ✅ 5. API Produits
```
https://ftp.navixtechnology.com/api/produits/produits/
```
**Résultat attendu** : Liste des produits (peut être vide si pas de données)

---

### Méthode 2 : Tests via cURL (Terminal/SSH)

#### Test 1 : Health Check
```bash
curl https://ftp.navixtechnology.com/api/health/
```
**Résultat attendu** : `{"status": "ok"}`

#### Test 2 : Test de connexion
```bash
curl https://ftp.navixtechnology.com/api/test-connection/
```
**Résultat attendu** : JSON avec statut de succès

#### Test 3 : Recherche de produits
```bash
curl "https://ftp.navixtechnology.com/api/search/produits/?q=eau"
```
**Résultat attendu** : Liste de produits correspondant à la recherche

#### Test 4 : Autocomplete
```bash
curl "https://ftp.navixtechnology.com/api/search/autocomplete/?q=eau"
```
**Résultat attendu** : Suggestions de produits

#### Test 5 : Authentification JWT
```bash
curl -X POST https://ftp.navixtechnology.com/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"votre_username","password":"votre_password"}'
```
**Résultat attendu** : Token JWT (access et refresh)

#### Test 6 : Endpoint avec authentification
```bash
# D'abord obtenir un token (voir test 5)
TOKEN="votre_token_ici"

curl -H "Authorization: Bearer $TOKEN" \
  https://ftp.navixtechnology.com/api/recommandations/pour_moi/
```
**Résultat attendu** : Recommandations pour l'utilisateur authentifié

---

### Méthode 3 : Tests via PowerShell (Windows)

#### Test 1 : Health Check
```powershell
Invoke-WebRequest -Uri "https://ftp.navixtechnology.com/api/health/" -Method GET
```

#### Test 2 : Test de connexion
```powershell
Invoke-WebRequest -Uri "https://ftp.navixtechnology.com/api/test-connection/" -Method GET
```

#### Test 3 : Authentification
```powershell
$body = @{
    username = "votre_username"
    password = "votre_password"
} | ConvertTo-Json

Invoke-WebRequest -Uri "https://ftp.navixtechnology.com/api/auth/token/" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

---

### Méthode 4 : Vérification via SSH (Sur le serveur)

Connectez-vous en SSH et testez :

#### 1. Vérifier que Django fonctionne
```bash
cd /home/rs2694021ez6eg8n/public_html/comparer
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Vérifier la configuration
python manage.py check --deploy

# Tester la connexion à la base de données
python manage.py dbshell
# Tapez \q pour quitter
```

#### 2. Tester l'application localement
```bash
# Tester avec curl depuis le serveur
curl http://localhost/api/health/
```

#### 3. Vérifier les logs
```bash
# Logs d'erreur Apache
tail -f /usr/local/apache/logs/error_log

# Ou dans cPanel : Errors
```

---

## ✅ Checklist de Vérification Complète

### Tests Basiques (Doivent tous passer)
- [ ] `/api/health/` retourne `{"status": "ok"}`
- [ ] `/api/test-connection/` retourne un statut de succès
- [ ] `/api/docs/` affiche la documentation Swagger
- [ ] `/admin/` affiche la page de connexion

### Tests API (Doivent fonctionner)
- [ ] `/api/search/produits/` retourne une liste (peut être vide)
- [ ] `/api/search/autocomplete/` retourne des suggestions
- [ ] `/api/produits/produits/` retourne la liste des produits
- [ ] `/api/magasins/magasins/` retourne la liste des magasins

### Tests Authentification
- [ ] `/api/auth/token/` permet d'obtenir un token JWT
- [ ] Les endpoints protégés retournent 401 sans token
- [ ] Les endpoints protégés retournent 200 avec un token valide

### Tests Base de Données
- [ ] Les migrations sont appliquées (`python manage.py migrate`)
- [ ] La connexion à la base fonctionne (`python manage.py dbshell`)
- [ ] Les données peuvent être lues (test avec `/api/produits/produits/`)

### Tests Performance
- [ ] Les réponses sont rapides (< 2 secondes)
- [ ] Pas d'erreurs 500 dans les logs
- [ ] Les fichiers statiques sont servis correctement

---

## 🚨 Dépannage des Problèmes Courants

### Erreur SSL : ERR_CERT_COMMON_NAME_INVALID

**Symptôme** : Le navigateur affiche "Votre connexion n'est pas privée" avec l'erreur `ERR_CERT_COMMON_NAME_INVALID`.

**Cause** : Le certificat SSL installé ne correspond pas au domaine `ftp.navixtechnology.com`.

**Solutions** :
1. **Installer un certificat SSL** pour `ftp.navixtechnology.com` dans cPanel (Let's Encrypt est gratuit)
2. **Vérifier le certificat** dans cPanel → SSL/TLS → Manage SSL Sites
3. **Utiliser un autre domaine** si le certificat est valide pour `comparateurdeprix.com`

> 📖 **Guide complet** : Consultez [`docs/RESOLUTION_ERREUR_SSL.md`](RESOLUTION_ERREUR_SSL.md) pour un guide détaillé.

**Solution rapide** :
- Dans cPanel → **SSL/TLS** → **Let's Encrypt SSL**
- Sélectionnez `ftp.navixtechnology.com`
- Cliquez sur **"Issue"** ou **"Install"**
- Attendez 2-5 minutes
- Redémarrez l'application dans **Setup Python App**

### Erreur 500 Internal Server Error

**Causes possibles** :
1. Fichier `.env` manquant ou incorrect
2. Base de données non accessible
3. Erreur dans le code Python
4. Permissions incorrectes

**Solutions** :
```bash
# Vérifier que .env existe
ls -la .env

# Vérifier les logs
tail -f error_log

# Vérifier la configuration
python manage.py check --deploy
```

### Erreur 404 Not Found

**Causes possibles** :
1. URL incorrecte
2. Configuration Passenger incorrecte
3. Fichier `passenger_wsgi.py` non trouvé

**Solutions** :
- Vérifier dans cPanel que `passenger_wsgi.py` est configuré comme "Application File"
- Vérifier que les URLs dans `config/urls.py` sont correctes

### Erreur "ALLOWED_HOSTS"

**Solution** :
Vérifier que dans `.env` :
```
DJANGO_ALLOWED_HOSTS=ftp.navixtechnology.com,www.ftp.navixtechnology.com,comparateurdeprix.com,www.comparateurdeprix.com
```

### Erreur de connexion à la base de données

**Solution** :
```bash
# Tester la connexion
python manage.py dbshell

# Vérifier les identifiants dans .env
cat .env | grep DB_
```

---

## 📊 Script de Test Automatique

Créez un fichier `test_backend.sh` sur le serveur :

```bash
#!/bin/bash

BASE_URL="https://ftp.navixtechnology.com"

echo "🔍 Test du backend..."
echo ""

# Test 1: Health Check
echo "1. Test Health Check..."
response=$(curl -s "$BASE_URL/api/health/")
if [[ $response == *"ok"* ]]; then
    echo "✅ Health Check: OK"
else
    echo "❌ Health Check: ÉCHEC"
fi

# Test 2: Test Connection
echo "2. Test Connection..."
response=$(curl -s "$BASE_URL/api/test-connection/")
if [[ $response == *"success"* ]]; then
    echo "✅ Test Connection: OK"
else
    echo "❌ Test Connection: ÉCHEC"
fi

# Test 3: Swagger
echo "3. Test Swagger..."
status=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/docs/")
if [ $status -eq 200 ]; then
    echo "✅ Swagger: OK"
else
    echo "❌ Swagger: ÉCHEC (Status: $status)"
fi

echo ""
echo "Tests terminés!"
```

Exécutez-le :
```bash
chmod +x test_backend.sh
./test_backend.sh
```

---

## 🎯 Résultat Attendu

Si tous les tests passent, votre backend est **fonctionnel** et prêt à être utilisé par votre frontend !

**Indicateurs de succès** :
- ✅ Tous les endpoints de base répondent
- ✅ L'authentification fonctionne
- ✅ La base de données est accessible
- ✅ Pas d'erreurs dans les logs
- ✅ Les réponses sont rapides

---

## 📞 Support

Si vous rencontrez des problèmes :
1. Vérifiez les logs : `tail -f error_log`
2. Testez en mode DEBUG temporairement (déconseillé en production)
3. Contactez le support de votre hébergeur si le problème persiste

