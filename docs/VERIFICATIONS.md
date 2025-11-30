# ✅ Guide Complet : Vérifications

Guide complet pour toutes les vérifications : conformité de l'API d'inscription et port Gunicorn sur Railway.

## 📋 Table des matières

- [Vérification de Conformité : API d'Inscription](#vérification-de-conformité-api-dinscription)
- [Vérification du Port Gunicorn sur Railway](#vérification-du-port-gunicorn-sur-railway)

---

## 📝 Vérification de Conformité : API d'Inscription

Ce document vérifie que l'implémentation correspond à la documentation dans `ENDPOINTS_API.md`.

### ✅ Conformité Générale : **CONFORME**

---

### 1. Endpoints

#### Documentation
- `POST /api/utilisateurs/` - Via ViewSet
- `POST /api/auth/register/` - Via RegisterView

#### Implémentation
- ✅ `POST /api/utilisateurs/` - `UtilisateurViewSet.create()` (ligne 108)
- ✅ `POST /api/auth/register/` - `RegisterView.post()` (ligne 662)
- ✅ Les deux utilisent `InscriptionSerializer`

**Statut : CONFORME**

---

### 2. Champs Requis

#### Documentation
| Champ | Validation |
|-------|------------|
| `username` | Requis, unique |
| `email` | Requis, unique, format email valide |
| `password` | Requis, minimum 8 caractères |
| `password_confirmation` | Requis, doit correspondre à `password` |

#### Implémentation
- ✅ `username` : `required=True` dans `extra_kwargs` (ligne 21)
- ✅ `email` : `required=True` dans `extra_kwargs` (ligne 20)
- ✅ `password` : `min_length=8` (ligne 9)
- ✅ `password_confirmation` : présent dans `fields` (ligne 15)

**Statut : CONFORME**

---

### 3. Champs Optionnels

#### Documentation
- `first_name`, `last_name`, `type_utilisateur`, `telephone`, `code_postal`, `ville`, `date_naissance`

#### Implémentation
- ✅ Tous présents dans `fields` (lignes 16-17)

**Statut : CONFORME**

---

### 4. Validations

#### 4.1 Username Unique

**Documentation :**
- Message : "Un utilisateur avec ce nom d'utilisateur existe déjà."

**Implémentation :**
- ✅ `validate_username()` (ligne 24-28)
- ✅ Message : `_('Un utilisateur avec ce nom d'utilisateur existe déjà.')`

**Statut : CONFORME**

---

#### 4.2 Email Unique

**Documentation :**
- Message : "Un utilisateur avec cet email existe déjà."

**Implémentation :**
- ✅ `validate_email()` (ligne 30-34)
- ✅ Message : `_('Un utilisateur avec cet email existe déjà.')`
- ✅ Normalisation : `value.lower().strip()`

**Statut : CONFORME**

---

#### 4.3 Password Minimum Length

**Documentation :**
- Message : "Assurez-vous que ce champ comporte au moins 8 caractères."

**Implémentation :**
- ✅ `password = serializers.CharField(min_length=8)` (ligne 9)
- ✅ Message généré automatiquement par DRF

**Note :** Le message exact peut varier selon la langue, mais la validation est correcte.

**Statut : CONFORME**

---

#### 4.4 Password Confirmation

**Documentation :**
- Message si manquant : "Ce champ est obligatoire."
- Message si différent : "Les mots de passe ne correspondent pas."

**Implémentation :**
- ✅ `validate()` vérifie la présence (ligne 76-79)
- ✅ `validate()` vérifie la correspondance (ligne 81-84)
- ✅ Message : `_('La confirmation du mot de passe est requise.')`
- ✅ Message : `_('Les mots de passe ne correspondent pas.')`

**Note :** Le message pour "champ obligatoire" est généré automatiquement par DRF.

**Statut : CONFORME**

---

#### 4.5 Champs Requis Manquants

**Documentation :**
- Message : "Ce champ est obligatoire."

**Implémentation :**
- ✅ `validate()` vérifie `username` (ligne 95-98)
- ✅ `validate()` vérifie `email` (ligne 90-93)
- ✅ Messages générés automatiquement par DRF pour les champs `required=True`

**Statut : CONFORME**

---

### 5. Réponse de Succès

#### Documentation
```json
{
  "user": { ... },
  "refresh": "...",
  "access": "...",
  "activation_pending": true
}
```

#### Implémentation

**UtilisateurViewSet.create() (ligne 197-233)**
- ✅ Retourne `UtilisateurSerializer(user).data` dans `response_data`
- ✅ Ajoute `refresh` et `access` si JWT activé (ligne 203-211)
- ✅ Ajoute `activation_pending` si `est_verifie=False` (ligne 214-215)
- ✅ Status : `HTTP_201_CREATED` (ligne 233)

**RegisterView.post() (ligne 674-689)**
- ✅ Retourne `UtilisateurSerializer(user).data` dans `user_payload`
- ✅ Ajoute `refresh` et `access` si JWT activé (ligne 676-681)
- ✅ Ajoute `activation_pending` si `est_verifie=False` (ligne 687-688)
- ✅ Status : `HTTP_201_CREATED` (ligne 689)

**Statut : CONFORME**

---

### 6. Structure de la Réponse User

#### Documentation
Les champs documentés incluent :
- `id`, `uuid`, `username`, `email`, `first_name`, `last_name`, `type_utilisateur`, `telephone`, `date_naissance`, `code_postal`, `ville`, `date_creation`, `derniere_connexion`, `est_verifie`, `points_fidelite`, `niveau_fidelite`, `total_achats`, `nombre_commandes`

#### Implémentation
`UtilisateurSerializer` (ligne 318-326) inclut :
- ✅ Tous les champs documentés
- ✅ Champs supplémentaires : `preferences`, `nom_entreprise`, `siret`, `profil`, `statistiques_fidelite`, `age`, `est_nouveau`, `est_client_fidele`

**Note :** La réponse inclut plus de champs que documentés, ce qui est acceptable (rétrocompatibilité).

**Statut : CONFORME** (avec champs supplémentaires)

---

### 7. Gestion des Erreurs

#### Documentation
- Erreurs de validation retournent `400 Bad Request`
- Messages d'erreur clairs pour chaque cas

#### Implémentation
- ✅ `serializer.is_valid(raise_exception=True)` retourne `400` pour les erreurs de validation
- ✅ Messages d'erreur personnalisés dans `validate()` et `validate_*()`
- ✅ Gestion des erreurs DB avec `503 Service Unavailable` (ligne 128-135, 177-184)

**Statut : CONFORME**

---

### 8. Email d'Activation

#### Documentation
- Mentionne que l'email d'activation est envoyé après l'inscription

#### Implémentation
- ✅ `UtilisateurViewSet.create()` : Envoie l'email via Celery (ligne 217-231)
- ✅ `RegisterView.post()` : Envoie l'email via Celery (ligne 667-673)
- ✅ Gestion gracieuse si Celery/Redis indisponible (ne fait pas échouer l'inscription)

**Statut : CONFORME**

---

### 9. Points d'Attention

#### 9.1 Messages d'Erreur Traduits

Les messages d'erreur utilisent `_()` pour la traduction Django. Les messages exacts peuvent varier selon la langue configurée, mais les validations sont correctes.

**Recommandation :** La documentation devrait mentionner que les messages peuvent varier selon la langue.

#### 9.2 Champs Supplémentaires dans la Réponse

La réponse inclut plus de champs que documentés (ex: `profil`, `statistiques_fidelite`). C'est acceptable pour la rétrocompatibilité, mais pourrait être documenté.

**Recommandation :** Ajouter une section "Champs supplémentaires" dans la documentation.

#### 9.3 Validation du Téléphone

Le serializer normalise automatiquement le téléphone (ajoute `+33` si nécessaire). Ce comportement n'est pas documenté.

**Recommandation :** Documenter la normalisation automatique du téléphone.

---

### 10. Résumé

| Aspect | Statut | Notes |
|--------|--------|-------|
| Endpoints | ✅ CONFORME | Les deux endpoints fonctionnent |
| Champs requis | ✅ CONFORME | Tous présents et validés |
| Champs optionnels | ✅ CONFORME | Tous présents |
| Validations | ✅ CONFORME | Toutes implémentées |
| Messages d'erreur | ✅ CONFORME | Messages corrects (peuvent varier selon langue) |
| Réponse de succès | ✅ CONFORME | Structure correcte |
| Gestion d'erreurs | ✅ CONFORME | Gestion robuste |
| Email d'activation | ✅ CONFORME | Envoi automatique |

---

### Conclusion

**L'implémentation est CONFORME à la documentation.**

Quelques améliorations mineures pourraient être apportées à la documentation :
1. Mentionner que les messages d'erreur peuvent varier selon la langue
2. Documenter les champs supplémentaires dans la réponse
3. Documenter la normalisation automatique du téléphone

Mais globalement, l'implémentation correspond fidèlement à ce qui est documenté.

---

## 🔍 Vérification du Port Gunicorn sur Railway

Ce guide explique comment vérifier que Gunicorn écoute sur le bon port sur Railway.

### 🔍 Problème Courant

**Erreur** : "Le serveur n'écoute pas sur le port attendu"

**Cause** : Railway définit automatiquement la variable `PORT`, mais elle peut être différente de 8080.

---

### ✅ Vérification Rapide

#### 1. Vérifier les Logs Railway

Dans les logs Railway, vous devriez voir :

```
📡 Port détecté depuis Railway: <PORT>
✅ Démarrage du serveur Gunicorn...
   📍 Écoute sur: 0.0.0.0:<PORT>
```

Le `<PORT>` affiché est le port que Railway attend.

#### 2. Vérifier la Configuration

**Fichier `start.sh`** :
```bash
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

✅ **Correct** : Utilise `$PORT` (variable Railway)

❌ **Incorrect** : `--bind 0.0.0.0:8080` (port fixe)

---

### 🔧 Diagnostic

#### Méthode 1 : Via les Logs Railway

1. Allez dans Railway → Votre service Django
2. Cliquez sur **"View Logs"**
3. Cherchez la ligne : `📡 Port détecté depuis Railway:`
4. Notez le port affiché

#### Méthode 2 : Via Railway CLI

```bash
# Voir les variables d'environnement
railway variables

# Cherchez la variable PORT
# Railway la définit automatiquement
```

#### Méthode 3 : Via Script de Diagnostic

```bash
# Exécuter le script de diagnostic
railway run python scripts/check_port.py
```

Le script affichera :
- Le port détecté
- Si le port est en écoute
- Les processus Gunicorn
- Les variables Railway

---

### 🚨 Problèmes Courants

#### Problème 1 : PORT non défini

**Symptôme** : Logs affichent "PORT non défini, utilisation du port 8080 par défaut"

**Solution** :
- Railway devrait définir automatiquement `PORT`
- Vérifiez que vous êtes bien sur Railway (pas en local)
- Si le problème persiste, définissez manuellement `PORT=8080` dans Railway → Variables

#### Problème 2 : Port différent de 8080

**Symptôme** : Railway utilise un port différent (ex: 3000, 5000, etc.)

**Solution** :
- ✅ **C'est normal !** Railway peut utiliser n'importe quel port
- Le script `start.sh` utilise automatiquement `$PORT`
- Gunicorn écoute sur `0.0.0.0:$PORT` (tous les ports sont acceptés)

#### Problème 3 : Gunicorn n'écoute pas

**Symptôme** : Le port n'est pas en écoute

**Vérifications** :
1. Vérifiez les logs Railway pour voir si Gunicorn a démarré
2. Vérifiez que `start.sh` est exécuté correctement
3. Vérifiez que Gunicorn utilise bien `--bind 0.0.0.0:$PORT`

---

### 📋 Checklist

- [ ] Variable `PORT` définie par Railway (automatique)
- [ ] `start.sh` utilise `$PORT` et non un port fixe
- [ ] Gunicorn démarre avec `--bind 0.0.0.0:$PORT`
- [ ] Les logs affichent le port utilisé
- [ ] Le port est en écoute (vérifiable via `check_port.py`)

---

### 🔍 Commandes Utiles

#### Voir les variables d'environnement

```bash
railway variables
```

#### Voir les logs en temps réel

```bash
railway logs --follow
```

#### Exécuter le diagnostic

```bash
railway run python scripts/check_port.py
```

#### Vérifier manuellement le port

```bash
# Dans Railway shell
netstat -tuln | grep LISTEN
# ou
ss -tuln | grep LISTEN
```

---

### 💡 Notes Importantes

1. **Railway définit automatiquement PORT** : Vous n'avez pas besoin de le définir manuellement
2. **Le port peut varier** : Railway peut utiliser 3000, 5000, 8080, ou tout autre port
3. **Gunicorn doit écouter sur 0.0.0.0** : Pas sur 127.0.0.1 (localhost uniquement)
4. **Le port doit être dynamique** : Utilisez `$PORT` et non un port fixe

---

### ✅ Configuration Correcte

#### start.sh (correct)

```bash
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

#### railway.json (correct)

```json
{
  "deploy": {
    "startCommand": "bash start.sh"
  }
}
```

---

### 🚀 Après Correction

Une fois corrigé, vous devriez voir dans les logs :

```
📡 Port détecté depuis Railway: 8080
✅ Démarrage du serveur Gunicorn...
   📍 Écoute sur: 0.0.0.0:8080
   🔗 Health check: http://0.0.0.0:8080/api/health/
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:8080
```

Et Railway devrait pouvoir se connecter à votre application.

---

## 📚 Ressources

- [Documentation Railway](https://docs.railway.app/)
- [Documentation Gunicorn](https://gunicorn.org/)
- [Documentation Django REST Framework](https://www.django-rest-framework.org/)

---

*Dernière mise à jour : 2025-01-17*

