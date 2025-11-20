# 🔍 Guide de Débogage - Erreur 500 sur POST /api/utilisateurs/

## 📋 Situation

- **Backend** : Déployé sur Railway (production)
- **Frontend** : React Native en local
- **Erreur** : 500 Internal Server Error lors de l'inscription
- **Symptôme** : Le client reçoit du HTML au lieu de JSON

---

## 🚀 Solutions pour Obtenir la Stacktrace

### Option 1 : Via Railway CLI (Recommandé)

#### 1. Installer Railway CLI (si pas déjà fait)

```powershell
# Via npm
npm install -g @railway/cli

# Ou télécharger depuis
# https://railway.app/cli
```

#### 2. Se connecter à Railway

```powershell
railway login
```

#### 3. Lier le projet (si pas déjà fait)

```powershell
cd C:\Users\herly\Videos\Projects\comparateur_prix
railway link
```

#### 4. Récupérer les logs

```powershell
# Voir les 200 dernières lignes
railway logs --tail 200

# Filtrer les erreurs liées à /api/utilisateurs/
railway logs --tail 200 | Select-String -Pattern "utilisateurs|ERROR|Exception|Traceback|500"

# Voir les logs en temps réel
railway logs --tail 0

# Sauvegarder les logs dans un fichier
railway logs --tail 500 > railway_logs.txt
```

#### 5. Utiliser le script PowerShell fourni

```powershell
.\get_railway_logs.ps1
```

---

### Option 2 : Via l'Interface Web Railway

1. Allez sur https://railway.app
2. Connectez-vous à votre compte
3. Sélectionnez votre projet
4. Cliquez sur votre service Django
5. Allez dans l'onglet **"Deployments"** ou **"Logs"**
6. Cherchez les erreurs récentes lors de l'inscription

---

### Option 3 : Activer Temporairement DEBUG sur Railway

⚠️ **ATTENTION** : Ne faites cela que temporairement pour déboguer !

1. Dans Railway → Variables d'environnement
2. Ajoutez ou modifiez :
   ```
   DJANGO_DEBUG=True
   ```
3. Redéployez l'application
4. Testez l'inscription
5. **IMPORTANT** : Remettez `DJANGO_DEBUG=False` après le débogage !

---

## 🔧 Améliorations Apportées

### 1. Gestion d'erreurs améliorée

La méthode `create` du `UtilisateurViewSet` a été améliorée pour :
- ✅ Toujours retourner du JSON (jamais de HTML)
- ✅ Logger l'erreur complète avec traceback
- ✅ Retourner des détails en mode DEBUG
- ✅ Retourner un message générique en production (sécurité)

### 2. Logging détaillé

Toutes les erreurs sont maintenant loggées avec :
- Le message d'erreur complet
- La stacktrace complète
- Les données reçues dans la requête

---

## 📊 Format de la Réponse d'Erreur

### En Production (DEBUG=False)

```json
{
  "detail": "Une erreur est survenue lors de la création du compte.",
  "error_type": "IntegrityError",
  "debug_info": "Consultez les logs du serveur pour plus de détails."
}
```

### En Développement (DEBUG=True)

```json
{
  "detail": "Une erreur est survenue lors de la création du compte.",
  "error_type": "IntegrityError",
  "error_message": "UNIQUE constraint failed: utilisateurs.email",
  "traceback": [
    "File \"/app/apps/utilisateurs/views.py\", line 111, in create",
    "  user = serializer.save()",
    "..."
  ]
}
```

---

## 🔍 Erreurs Communes et Solutions

### 1. "UNIQUE constraint failed: utilisateurs.email"

**Cause** : Email déjà existant dans la base de données

**Solution** : Vérifier la validation dans le serializer (déjà implémentée)

### 2. "RelatedObjectDoesNotExist: Utilisateur has no profil"

**Cause** : Le signal n'a pas créé le profil

**Solution** : Déjà géré dans le code - création manuelle si nécessaire

### 3. "IntegrityError: NOT NULL constraint failed"

**Cause** : Champ requis manquant

**Solution** : Vérifier que tous les champs requis sont envoyés

### 4. "OperationalError: database is locked"

**Cause** : Conflit de transaction

**Solution** : Vérifier les transactions dans le code (déjà géré avec `transaction.atomic()`)

---

## 📝 Checklist de Débogage

- [ ] Railway CLI installé et connecté
- [ ] Logs Railway récupérés
- [ ] Stacktrace complète identifiée
- [ ] Type d'erreur identifié
- [ ] Solution appliquée
- [ ] Test effectué
- [ ] DEBUG remis à False en production

---

## 🚨 Important

1. **Ne jamais laisser DEBUG=True en production** après le débogage
2. **Ne jamais exposer des informations sensibles** dans les réponses d'erreur
3. **Toujours logger les erreurs complètes** pour le débogage
4. **Toujours retourner du JSON** pour React Native

---

## 📞 Prochaines Étapes

1. Récupérer les logs Railway avec l'une des méthodes ci-dessus
2. Identifier le type d'erreur exact dans la stacktrace
3. Appliquer la correction appropriée
4. Tester à nouveau l'inscription
5. Remettre DEBUG=False en production

