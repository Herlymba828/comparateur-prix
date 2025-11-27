# Vérification du Port Gunicorn sur Railway

Ce guide explique comment vérifier que Gunicorn écoute sur le bon port sur Railway.

## 🔍 Problème Courant

**Erreur** : "Le serveur n'écoute pas sur le port attendu"

**Cause** : Railway définit automatiquement la variable `PORT`, mais elle peut être différente de 8080.

---

## ✅ Vérification Rapide

### 1. Vérifier les Logs Railway

Dans les logs Railway, vous devriez voir :

```
📡 Port détecté depuis Railway: <PORT>
✅ Démarrage du serveur Gunicorn...
   📍 Écoute sur: 0.0.0.0:<PORT>
```

Le `<PORT>` affiché est le port que Railway attend.

### 2. Vérifier la Configuration

**Fichier `start.sh`** :
```bash
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

✅ **Correct** : Utilise `$PORT` (variable Railway)

❌ **Incorrect** : `--bind 0.0.0.0:8080` (port fixe)

---

## 🔧 Diagnostic

### Méthode 1 : Via les Logs Railway

1. Allez dans Railway → Votre service Django
2. Cliquez sur **"View Logs"**
3. Cherchez la ligne : `📡 Port détecté depuis Railway:`
4. Notez le port affiché

### Méthode 2 : Via Railway CLI

```bash
# Voir les variables d'environnement
railway variables

# Cherchez la variable PORT
# Railway la définit automatiquement
```

### Méthode 3 : Via Script de Diagnostic

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

## 🚨 Problèmes Courants

### Problème 1 : PORT non défini

**Symptôme** : Logs affichent "PORT non défini, utilisation du port 8080 par défaut"

**Solution** :
- Railway devrait définir automatiquement `PORT`
- Vérifiez que vous êtes bien sur Railway (pas en local)
- Si le problème persiste, définissez manuellement `PORT=8080` dans Railway → Variables

### Problème 2 : Port différent de 8080

**Symptôme** : Railway utilise un port différent (ex: 3000, 5000, etc.)

**Solution** :
- ✅ **C'est normal !** Railway peut utiliser n'importe quel port
- Le script `start.sh` utilise automatiquement `$PORT`
- Gunicorn écoute sur `0.0.0.0:$PORT` (tous les ports sont acceptés)

### Problème 3 : Gunicorn n'écoute pas

**Symptôme** : Le port n'est pas en écoute

**Vérifications** :
1. Vérifiez les logs Railway pour voir si Gunicorn a démarré
2. Vérifiez que `start.sh` est exécuté correctement
3. Vérifiez que Gunicorn utilise bien `--bind 0.0.0.0:$PORT`

---

## 📋 Checklist

- [ ] Variable `PORT` définie par Railway (automatique)
- [ ] `start.sh` utilise `$PORT` et non un port fixe
- [ ] Gunicorn démarre avec `--bind 0.0.0.0:$PORT`
- [ ] Les logs affichent le port utilisé
- [ ] Le port est en écoute (vérifiable via `check_port.py`)

---

## 🔍 Commandes Utiles

### Voir les variables d'environnement

```bash
railway variables
```

### Voir les logs en temps réel

```bash
railway logs --follow
```

### Exécuter le diagnostic

```bash
railway run python scripts/check_port.py
```

### Vérifier manuellement le port

```bash
# Dans Railway shell
netstat -tuln | grep LISTEN
# ou
ss -tuln | grep LISTEN
```

---

## 💡 Notes Importantes

1. **Railway définit automatiquement PORT** : Vous n'avez pas besoin de le définir manuellement
2. **Le port peut varier** : Railway peut utiliser 3000, 5000, 8080, ou tout autre port
3. **Gunicorn doit écouter sur 0.0.0.0** : Pas sur 127.0.0.1 (localhost uniquement)
4. **Le port doit être dynamique** : Utilisez `$PORT` et non un port fixe

---

## ✅ Configuration Correcte

### start.sh (correct)

```bash
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### railway.json (correct)

```json
{
  "deploy": {
    "startCommand": "bash start.sh"
  }
}
```

---

## 🚀 Après Correction

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

