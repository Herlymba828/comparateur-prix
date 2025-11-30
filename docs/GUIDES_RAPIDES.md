# ⚡ Guides Rapides

Guide rapide pour les tâches courantes : Redis, Railway, JWT et suppression de commits Git.

## 📋 Table des matières

- [Guide Rapide Redis](#guide-rapide-redis)
- [Guide Rapide Railway](#guide-rapide-railway)
- [Guide Authentification JWT](#guide-authentification-jwt)
- [Guide Suppression Commits Git](#guide-suppression-commits-git)

---

## 🔴 Guide Rapide Redis

### Installation

#### Windows

**Option 1 : WSL2 (Recommandé)**
```bash
# Dans WSL2
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Option 2 : Memurai (Alternative Windows native)**
1. Téléchargez depuis [memurai.com](https://www.memurai.com/)
2. Installez et démarrez le service

**Option 3 : Docker**
```bash
docker run -d -p 6379:6379 redis:latest
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install redis-server

# Démarrer Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Vérifier que Redis fonctionne
redis-cli ping
# Devrait répondre: PONG
```

#### macOS

```bash
brew install redis
brew services start redis

# Vérifier que Redis fonctionne
redis-cli ping
# Devrait répondre: PONG
```

### Configuration

#### Variables d'environnement

```bash
# Dans votre fichier .env
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_CACHE_URL=redis://127.0.0.1:6379/1
REDIS_PASSWORD=  # Laissez vide si pas de mot de passe
```

#### Configuration avec mot de passe

```bash
# Format de l'URL Redis avec mot de passe
REDIS_URL=redis://:votre_mot_de_passe@localhost:6379/0

# Ou utilisez REDIS_PASSWORD séparément
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=votre_mot_de_passe
```

### Vérification

```bash
# Tester Redis
redis-cli ping
# Devrait répondre: PONG

# Ou depuis Python
python manage.py shell
>>> import redis
>>> r = redis.from_url('redis://localhost:6379/0')
>>> r.ping()
True
```

### Configuration pour Railway

1. **Ajoutez un service Redis dans Railway** :
   - Allez dans votre projet Railway
   - Cliquez sur **"+ New"** → **"Database"** → **"Add Redis"**
   - Railway configure automatiquement `REDIS_URL`

2. **Vérifiez les variables d'environnement** :
   - Railway fournit automatiquement `REDIS_URL`
   - Aucune configuration supplémentaire nécessaire !

### Dépannage

#### Erreur : "Connection refused" pour Redis

**Solutions** :
1. Vérifiez que Redis est démarré :
   ```bash
   # Linux
   sudo systemctl status redis-server
   
   # macOS
   brew services list | grep redis
   ```

2. Vérifiez le port :
   ```bash
   redis-cli -p 6379 ping
   ```

3. Vérifiez les permissions de connexion dans `redis.conf`

---

## 🚂 Guide Rapide Railway

### Démarrage Rapide

#### 1️⃣ Créer le service PostgreSQL (2 minutes)

1. Allez sur https://railway.app
2. Ouvrez votre projet
3. Cliquez sur **"+ New"** → **"Database"** → **"Add PostgreSQL"**
4. Attendez 1-2 minutes que Railway crée la base de données

✅ **C'est tout !** Railway configure automatiquement `DATABASE_URL`.

#### 2️⃣ Configurer les variables d'environnement (3 minutes)

Dans Railway → Votre service Django → **Variables**, ajoutez :

```bash
# OBLIGATOIRE
DJANGO_SECRET_KEY=votre_clé_secrète_générée
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=comparo.up.railway.app,*.railway.app

# URLs
SITE_URL=https://comparo.up.railway.app
BACKEND_URL=https://comparo.up.railway.app
```

**Générer une clé secrète :**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

#### 3️⃣ Appliquer les migrations (1 minute)

**Option A : Via Railway CLI (Recommandé)**
```bash
npm i -g @railway/cli
railway login
railway link
railway run python manage.py migrate
```

**Option B : Via l'interface Railway**
- Allez dans votre service Django
- Cliquez sur **"Deployments"** → **"View Logs"**
- Ou utilisez le shell Railway

#### 4️⃣ Vérifier que tout fonctionne

1. Allez sur `https://comparo.up.railway.app/api/health/`
2. Vous devriez voir : `{"status": "ok"}`

✅ **Terminé !** Votre application est configurée.

### Commandes Utiles

#### Voir les variables d'environnement

```bash
railway variables
```

#### Ajouter une variable

```bash
railway variables set DJANGO_SECRET_KEY=votre_clé
```

#### Voir les logs en temps réel

```bash
railway logs --follow
```

#### Exécuter une commande

```bash
railway run python manage.py migrate
railway run python manage.py createsuperuser
railway run python manage.py shell
```

#### Vérifier le statut

```bash
railway status
```

#### Lier un projet

```bash
railway link
```

### Configuration Domaine

#### Utiliser le domaine principal

1. **Configurer le domaine sur Railway**
   - Dans Railway, allez dans votre projet
   - Ajoutez un domaine personnalisé : `comparateurdeprix.com`
   - Railway configure automatiquement le certificat SSL via Let's Encrypt

2. **Mettre à jour les variables d'environnement**
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

3. **Tester**
   - `https://comparateurdeprix.com/api/health/`
   - `https://comparateurdeprix.com/api/docs/`
   - `https://www.comparateurdeprix.com/api/health/`

#### Créer un sous-domaine API (Recommandé)

Créez un sous-domaine dédié pour l'API : `api.comparateurdeprix.com`

1. **Créer le sous-domaine sur Railway**
   - Dans Railway, allez dans votre projet
   - Ajoutez un domaine personnalisé : `api.comparateurdeprix.com`
   - Railway configure automatiquement le certificat SSL via Let's Encrypt

2. **Mettre à jour les variables d'environnement**
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

3. **Tester**
   - `https://api.comparateurdeprix.com/api/health/`
   - `https://api.comparateurdeprix.com/api/docs/`

### Dépannage

#### Problème : "DATABASE_URL not found"

**Solution** :
1. Vérifiez que le service PostgreSQL est bien créé
2. Vérifiez que les services sont dans le même projet Railway
3. Railway devrait automatiquement partager `DATABASE_URL`
4. Si nécessaire, copiez manuellement `DATABASE_URL` depuis le service PostgreSQL vers le service Django

#### Problème : "Connection refused" ou "Connection timeout"

**Solutions** :
1. Vérifiez que le service PostgreSQL est démarré (pas en pause)
2. Vérifiez que `DATABASE_URL` est correct
3. Vérifiez que `DJANGO_DEBUG=False` (en production)
4. Vérifiez les logs Railway pour plus de détails

#### Problème : "relation does not exist" ou "table does not exist"

**Solution** :
```bash
# Appliquer les migrations
railway run python manage.py migrate
```

---

## 🔐 Guide Authentification JWT

### Configuration JWT

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),  # 1 heure
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),   # 30 jours
    'ROTATE_REFRESH_TOKENS': True,                  # Rotation activée
    'BLACKLIST_AFTER_ROTATION': True,               # Blacklist activée
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### ⚠️ Important : Rotation des Tokens

Avec `ROTATE_REFRESH_TOKENS=True` et `BLACKLIST_AFTER_ROTATION=True` :
- Chaque refresh génère un **nouveau refresh token**
- L'ancien refresh token est **blacklisté** (ne peut plus être utilisé)
- Le frontend **DOIT** sauvegarder le nouveau refresh token

### Endpoints d'Authentification

#### Obtenir un token

```
POST /api/auth/token/
Body: {"username": "...", "password": "..."}
Response: {"access": "...", "refresh": "..."}
```

#### Rafraîchir un token

```
POST /api/auth/token/refresh/
Body: {"refresh": "..."}
Response: {"access": "...", "refresh": "..."}  // Nouveau refresh si rotation activée
```

#### Vérifier un token

```
GET /api/auth/verify-token/
Headers: Authorization: Bearer <token>
Response: {"valid": true, "user_id": 1, "username": "..."}
```

### Format de la Requête de Refresh

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "votre_refresh_token_ici"
}
```

### Réponse du Refresh

```json
{
  "access": "nouveau_access_token_ici",
  "refresh": "nouveau_refresh_token_ici"  // Si ROTATE_REFRESH_TOKENS=True
}
```

### ⚠️ IMPORTANT : Utiliser le Nouveau Token

**Le frontend DOIT utiliser le nouveau `access` token** retourné dans la réponse :

```javascript
// ❌ MAUVAIS - Utiliser l'ancien token
const response = await fetch('/api/auth/token/refresh/', {
  method: 'POST',
  body: JSON.stringify({ refresh: refreshToken })
});
const data = await response.json();
// Ne pas utiliser le nouveau token !
fetch('/api/produits/produits/5/like/', {
  headers: {
    'Authorization': `Bearer ${oldAccessToken}` // ❌ ERREUR
  }
});

// ✅ CORRECT - Utiliser le nouveau token
const response = await fetch('/api/auth/token/refresh/', {
  method: 'POST',
  body: JSON.stringify({ refresh: refreshToken })
});
const data = await response.json();
// Utiliser le nouveau token immédiatement
fetch('/api/produits/produits/5/like/', {
  headers: {
    'Authorization': `Bearer ${data.access}` // ✅ CORRECT
  }
});
```

### Format du Header Authorization

Le header **DOIT** être exactement dans ce format :

```
Authorization: Bearer <token>
```

**Points importants** :
- Le mot "Bearer" (avec majuscule B)
- Un espace après "Bearer"
- Pas de guillemets autour du token
- Pas d'espaces supplémentaires

### Exemple Complet (JavaScript/React)

```javascript
// Fonction pour rafraîchir le token
async function refreshToken(refreshToken) {
  const response = await fetch('/api/auth/token/refresh/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh: refreshToken })
  });
  
  if (response.ok) {
    const data = await response.json();
    // ⚠️ IMPORTANT : Sauvegarder le nouveau token
    localStorage.setItem('access_token', data.access);
    if (data.refresh) {
      localStorage.setItem('refresh_token', data.refresh);
    }
    return data.access;
  } else {
    throw new Error('Token refresh failed');
  }
}

// Fonction pour faire une requête authentifiée
async function authenticatedFetch(url, options = {}) {
  let accessToken = localStorage.getItem('access_token');
  
  // Ajouter le token au header
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
    ...options.headers
  };
  
  let response = await fetch(url, { ...options, headers });
  
  // Si 401, essayer de rafraîchir le token
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      try {
        // Rafraîchir le token
        accessToken = await refreshToken(refreshToken);
        // Réessayer la requête avec le nouveau token
        headers['Authorization'] = `Bearer ${accessToken}`;
        response = await fetch(url, { ...options, headers });
      } catch (error) {
        // Rediriger vers la page de connexion
        window.location.href = '/login';
        throw error;
      }
    }
  }
  
  return response;
}

// Utilisation
async function likeProduct(productId) {
  const response = await authenticatedFetch(
    `/api/produits/produits/${productId}/like/`,
    { method: 'POST' }
  );
  return response.json();
}
```

### Tester avec curl

```bash
# 1. Obtenir un token
curl -X POST http://localhost:8001/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "votre_username", "password": "votre_password"}'

# Réponse :
# {"access": "eyJ0eXAiOiJKV1QiLCJhbGc...", "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."}

# 2. Utiliser le token pour liker un produit
curl -X POST http://localhost:8001/api/produits/produits/5/like/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..." \
  -H "Content-Type: application/json"

# 3. Si 401, rafraîchir le token
curl -X POST http://localhost:8001/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "votre_refresh_token"}'

# Réponse :
# {"access": "nouveau_token_ici", "refresh": "nouveau_refresh_token_ici"}

# 4. Utiliser le NOUVEAU token
curl -X POST http://localhost:8001/api/produits/produits/5/like/ \
  -H "Authorization: Bearer nouveau_token_ici" \
  -H "Content-Type: application/json"
```

### Checklist Frontend

- [ ] Le token refresh retourne bien un nouveau `access` token
- [ ] Le nouveau token est sauvegardé immédiatement après le refresh
- [ ] Le nouveau token est utilisé dans toutes les requêtes suivantes
- [ ] Le format du header est exactement : `Authorization: Bearer <token>`
- [ ] Pas d'espaces supplémentaires ou de guillemets
- [ ] Si `ROTATE_REFRESH_TOKENS=True`, le nouveau `refresh` token est aussi sauvegardé
- [ ] L'ancien refresh token n'est plus utilisé après rotation

### Endpoints protégés (nécessitent le token)

- `POST /api/produits/produits/{id}/like/`
- `DELETE /api/produits/produits/{id}/like/`
- `GET /api/produits/produits/mes_likes/`
- `GET /api/recommandations/pour_moi/`

---

## 🗑️ Guide Suppression Commits Git

### ⚠️ AVERTISSEMENT IMPORTANT

**Si les commits sont déjà sur GitHub et partagés avec d'autres développeurs :**
- ⛔ **NE PAS** utiliser `git push --force` sans coordination
- Cela peut causer des problèmes pour les autres développeurs
- Préférez créer de nouveaux commits pour corriger

### Option 1 : Rebase Interactif (Pour supprimer/combiner des commits)

#### Étape 1 : Lancer le rebase interactif

```bash
# Réviser les 10 derniers commits
git rebase -i HEAD~10

# Ou réviser depuis un commit spécifique
git rebase -i <commit-hash>
```

#### Étape 2 : Dans l'éditeur qui s'ouvre

- Remplacez `pick` par `drop` pour **supprimer** un commit
- Remplacez `pick` par `squash` ou `fixup` pour **combiner** avec le commit précédent
- Sauvegardez et fermez l'éditeur

#### Étape 3 : Force push (⚠️ DANGEREUX)

```bash
git push --force origin main
# OU (plus sûr, évite d'écraser les commits des autres)
git push --force-with-lease origin main
```

### Option 2 : Reset (Pour revenir à un commit antérieur)

#### Soft Reset (garde les modifications)

```bash
# Revenir au commit 155d59d5 (garde les modifications en staging)
git reset --soft 155d59d5

# Puis créer un nouveau commit
git commit -m "Nouveau message"
```

#### Hard Reset (⚠️ SUPPRIME les modifications)

```bash
# Revenir au commit 155d59d5 (SUPPRIME toutes les modifications)
git reset --hard 155d59d5

# Force push
git push --force origin main
```

### Option 3 : Créer un nouveau commit de correction (RECOMMANDÉ)

**Au lieu de supprimer les commits, créez un nouveau commit qui corrige :**

```bash
# Faire vos modifications
git add .
git commit -m "fix: Correction des erreurs d'inscription"
git push origin main
```

**Avantages** :
- ✅ Pas de risque pour les autres développeurs
- ✅ Historique complet conservé
- ✅ Plus sûr en production

### Option 4 : Supprimer seulement les commits locaux (pas encore poussés)

Si vous avez des commits locaux non poussés :

```bash
# Voir les commits locaux non poussés
git log origin/main..HEAD

# Supprimer les N derniers commits (garde les modifications)
git reset --soft HEAD~N

# OU supprimer complètement (⚠️ supprime les modifications)
git reset --hard HEAD~N
```

### Exemples pratiques

#### Exemple 1 : Supprimer les 2 derniers commits

```bash
git rebase -i HEAD~2
# Dans l'éditeur : changer 'pick' en 'drop' pour les commits à supprimer
git push --force-with-lease origin main
```

#### Exemple 2 : Combiner les 3 derniers commits en un seul

```bash
git rebase -i HEAD~3
# Dans l'éditeur : 
# - Laisser 'pick' pour le premier commit
# - Changer 'pick' en 'squash' pour les 2 autres
git push --force-with-lease origin main
```

#### Exemple 3 : Revenir à un commit spécifique

```bash
# Revenir au commit "Mise à jour des endpoints de l'API"
git reset --soft 155d59d5
git commit -m "Nouveau commit combiné"
git push --force-with-lease origin main
```

### ⚠️ Commandes DANGEREUSES

Ces commandes peuvent **détruire votre travail** :

```bash
# ⛔ SUPPRIME TOUT (modifications + commits)
git reset --hard <commit>

# ⛔ ÉCRASE l'historique sur GitHub
git push --force origin main

# ⛔ SUPPRIME les commits non poussés
git reset --hard origin/main
```

**Toujours utiliser `--force-with-lease` au lieu de `--force` :**
```bash
# ✅ Plus sûr : échoue si quelqu'un d'autre a poussé entre-temps
git push --force-with-lease origin main
```

### Récupérer après une erreur

Si vous avez supprimé des commits par erreur :

```bash
# Voir l'historique complet (y compris les commits supprimés)
git reflog

# Revenir à un commit spécifique
git reset --hard <commit-hash-from-reflog>
```

### Recommandation pour votre projet

**Vu que vous travaillez seul sur ce projet :**

1. **Pour nettoyer l'historique** : Utilisez `git rebase -i` pour combiner les commits de correction
2. **Pour supprimer des commits** : Utilisez `git reset --soft` puis créez un nouveau commit
3. **Toujours utiliser** : `git push --force-with-lease` au lieu de `--force`

**Exemple de nettoyage :**
```bash
# Combiner les commits de correction en un seul
git rebase -i HEAD~5
# Dans l'éditeur, garder le premier et mettre 'squash' pour les autres
git push --force-with-lease origin main
```

---

## 📚 Ressources

- [Documentation Redis](https://redis.io/documentation)
- [Documentation Railway](https://docs.railway.app/)
- [Documentation Django REST Framework JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Documentation Git](https://git-scm.com/doc)

---

*Dernière mise à jour : 2025-01-17*

