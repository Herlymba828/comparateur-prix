# ⚠️ CELERY EST OBLIGATOIRE - Configuration complète

## 🎯 Objectif

Configurer Celery Worker et Celery Beat comme **services séparés et obligatoires** sur Railway.

## 📋 Prérequis

- ✅ Redis configuré et accessible
- ✅ PostgreSQL configuré et accessible
- ✅ Variables d'environnement définies

## 🚀 Configuration sur Railway

### Étape 1 : Créer le service Celery Worker

1. **Dans Railway Dashboard :**
   - Allez à votre projet
   - Cliquez sur "New Service"
   - Sélectionnez "GitHub Repo"
   - Sélectionnez votre repository

2. **Configuration du service :**
   - **Nom :** `celery-worker`
   - **Commande de démarrage :** 
     ```bash
     bash start_celery_worker.sh
     ```

3. **Variables d'environnement :**
   - Copier les mêmes variables que le service Django :
     - `DATABASE_URL`
     - `DATABASE_PUBLIC_URL`
     - `CELERY_BROKER_URL`
     - `CELERY_RESULT_BACKEND`
     - `DJANGO_SECRET_KEY`
     - `DJANGO_DEBUG=False`

4. **Ressources :**
   - Memory: 512 MB (minimum)
   - CPU: Partagé

### Étape 2 : Créer le service Celery Beat

1. **Dans Railway Dashboard :**
   - Cliquez sur "New Service"
   - Sélectionnez "GitHub Repo"
   - Sélectionnez votre repository

2. **Configuration du service :**
   - **Nom :** `celery-beat`
   - **Commande de démarrage :**
     ```bash
     bash start_celery_beat.sh
     ```

3. **Variables d'environnement :**
   - Mêmes variables que Celery Worker

4. **Ressources :**
   - Memory: 256 MB (minimum)
   - CPU: Partagé

### Étape 3 : Vérifier la configuration

```bash
# Vérifier que les services démarrent
railway logs --service celery-worker
railway logs --service celery-beat

# Vérifier que les tâches s'exécutent
celery -A config inspect active
celery -A config inspect scheduled
```

## 📊 Tâches Celery qui s'exécuteront

### Tâches planifiées (Beat)

| Tâche | Fréquence | Description |
|-------|-----------|-------------|
| `entrainer-modeles-hebdomadaire` | Hebdomadaire | Entraînement des modèles ML |
| `generer-recommandations-quotidiennes` | Quotidienne | Génération des recommandations |
| `verifier-alertes-quotidienne` | Quotidienne | Vérification des alertes prix |
| `verifier-alertes-instantanee` | 15 minutes | Vérification instantanée des alertes |
| `comparer-prix-homologues-quotidien` | Quotidienne | Comparaison des prix homologués |
| `import-dgccrf-quotidien` | Quotidienne | Import des données DGCCRF |
| `backup-database-quotidien` | Quotidienne | Backup de la base de données |

### Tâches asynchrones (à la demande)

| Tâche | Déclencheur | Description |
|-------|------------|-------------|
| `send_activation_code_email` | Inscription | Envoi d'email d'activation |
| `send_reset_email` | Réinitialisation | Envoi d'email de réinitialisation |
| `send_login_otp_email` | Connexion OTP | Envoi du code OTP |
| `executer_analyse_prix` | Demande utilisateur | Exécution d'une analyse |
| `generer_rapport_analyse` | Demande utilisateur | Génération d'un rapport |
| `log_search_event_async` | Recherche | Logging asynchrone |

## ✅ Vérification

### Vérifier que Celery Worker fonctionne

```bash
# Depuis votre machine locale
celery -A config inspect active

# Résultat attendu:
# {
#   'celery@worker-1': {
#     'active': [...]
#   }
# }
```

### Vérifier que Celery Beat fonctionne

```bash
# Vérifier les tâches planifiées
celery -A config inspect scheduled

# Résultat attendu:
# {
#   'celery@beat-1': {
#     'scheduled': [...]
#   }
# }
```

### Vérifier les logs

```bash
# Logs du worker
railway logs --service celery-worker

# Logs du beat
railway logs --service celery-beat
```

## 🔧 Troubleshooting

### Celery Worker ne démarre pas

1. Vérifier les logs : `railway logs --service celery-worker`
2. Vérifier que Redis est accessible
3. Vérifier que `CELERY_BROKER_URL` est défini correctement
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

# Voir les tâches actives avec détails
celery -A config inspect active_queues
```

### Alertes à configurer

- ⚠️ Celery Worker crash
- ⚠️ Celery Beat crash
- ⚠️ Tâches en retard
- ⚠️ Erreurs de tâches

## 🎯 Résumé

Celery est maintenant **obligatoire et toujours actif** avec :

- ✅ Service Celery Worker séparé
- ✅ Service Celery Beat séparé
- ✅ Tâches planifiées automatiques
- ✅ Tâches asynchrones à la demande
- ✅ Monitoring et logs visibles

**État :** 🟢 CELERY MANDATORY
