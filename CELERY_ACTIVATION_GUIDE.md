# 🚀 Guide d'activation de Celery sur Railway

## ⚠️ IMPORTANT

Celery Worker et Beat doivent être créés comme **services séparés** dans Railway Dashboard.

## 📋 Étapes d'activation

### Étape 1 : Accéder à Railway Dashboard

1. Allez sur https://railway.app
2. Connectez-vous à votre compte
3. Sélectionnez votre projet `invigorating-upliftment`

### Étape 2 : Créer le service Celery Worker

1. Cliquez sur **"New Service"** (bouton + en haut à droite)
2. Sélectionnez **"GitHub Repo"**
3. Sélectionnez votre repository `comparateur-prix`
4. Configurez le service :
   - **Nom du service :** `celery-worker`
   - **Branche :** `main`
   - **Commande de démarrage :** 
     ```bash
     bash start_celery_worker.sh
     ```

5. Cliquez sur **"Create Service"**

### Étape 3 : Configurer les variables du Celery Worker

1. Allez dans le service `celery-worker`
2. Cliquez sur l'onglet **"Variables"**
3. Ajoutez les variables suivantes (copiez-les du service `web`) :
   - `DATABASE_URL`
   - `DATABASE_PUBLIC_URL`
   - `CELERY_BROKER_URL`
   - `CELERY_RESULT_BACKEND`
   - `DJANGO_SECRET_KEY`
   - `DJANGO_DEBUG=False`
   - `DJANGO_SETTINGS_MODULE=config.settings`

4. Cliquez sur **"Deploy"**

### Étape 4 : Créer le service Celery Beat

1. Cliquez sur **"New Service"** (bouton + en haut à droite)
2. Sélectionnez **"GitHub Repo"**
3. Sélectionnez votre repository `comparateur-prix`
4. Configurez le service :
   - **Nom du service :** `celery-beat`
   - **Branche :** `main`
   - **Commande de démarrage :**
     ```bash
     bash start_celery_beat.sh
     ```

5. Cliquez sur **"Create Service"**

### Étape 5 : Configurer les variables du Celery Beat

1. Allez dans le service `celery-beat`
2. Cliquez sur l'onglet **"Variables"**
3. Ajoutez les mêmes variables que le Celery Worker :
   - `DATABASE_URL`
   - `DATABASE_PUBLIC_URL`
   - `CELERY_BROKER_URL`
   - `CELERY_RESULT_BACKEND`
   - `DJANGO_SECRET_KEY`
   - `DJANGO_DEBUG=False`
   - `DJANGO_SETTINGS_MODULE=config.settings`

4. Cliquez sur **"Deploy"**

## ✅ Vérification

### Vérifier que les services démarrent

1. Allez dans le service `celery-worker`
2. Cliquez sur l'onglet **"Logs"**
3. Vous devriez voir :
   ```
   🚀 Démarrage de Celery Worker...
   ⏳ Démarrage du worker Celery...
   ```

4. Allez dans le service `celery-beat`
5. Cliquez sur l'onglet **"Logs"**
6. Vous devriez voir :
   ```
   🚀 Démarrage de Celery Beat (Scheduler)...
   ⏳ Démarrage du scheduler Celery Beat...
   ```

### Vérifier que les tâches s'exécutent

```bash
# Depuis votre machine locale
celery -A config inspect active

# Résultat attendu:
# {
#   'celery@celery-worker-1': {
#     'active': [...]
#   }
# }
```

## 📊 Services finaux

Après activation, vous devriez avoir 3 services :

| Service | Rôle | Commande |
|---------|------|----------|
| `web` | API Django | `bash start.sh` |
| `celery-worker` | Exécution des tâches | `bash start_celery_worker.sh` |
| `celery-beat` | Planification des tâches | `bash start_celery_beat.sh` |

## 🔧 Troubleshooting

### Celery Worker ne démarre pas

1. Vérifier les logs : Onglet "Logs" du service
2. Vérifier que `CELERY_BROKER_URL` est défini
3. Vérifier que Redis est accessible
4. Vérifier que `DATABASE_URL` est défini

### Tâches ne s'exécutent pas

1. Vérifier que Celery Beat est en cours d'exécution
2. Vérifier que Celery Worker est en cours d'exécution
3. Vérifier les logs pour les erreurs
4. Vérifier que les tâches sont bien définies dans `config/celery.py`

### Erreur "Connection refused"

1. Vérifier que Redis est accessible
2. Vérifier que PostgreSQL est accessible
3. Vérifier les pare-feu/règles de sécurité

## 📈 Monitoring

### Commandes utiles

```bash
# Voir les workers actifs
celery -A config inspect active

# Voir les tâches planifiées
celery -A config inspect scheduled

# Voir les statistiques
celery -A config inspect stats

# Voir les tâches en attente
celery -A config inspect reserved
```

## 🎯 Résumé

Après ces étapes, Celery sera **actif et obligatoire** avec :

- ✅ Service Celery Worker séparé
- ✅ Service Celery Beat séparé
- ✅ Tâches planifiées automatiques
- ✅ Tâches asynchrones à la demande
- ✅ Monitoring et logs visibles

**État :** 🟢 CELERY ACTIVE
