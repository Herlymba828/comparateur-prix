# Configuration Celery sur Railway

## Problème identifié

Le Celery Worker crashait silencieusement en production Railway car :

1. **`--detach` crée des processus orphelins** que Railway ne peut pas monitorer
2. **Pas de logs visibles** quand le processus crash
3. **Impossible de redémarrer automatiquement** en cas d'erreur

## Solution actuelle

**Celery est désactivé dans le service Django principal** pour éviter les crashes silencieux.

## Configuration recommandée (Option A - Recommandée)

Créer des services Celery séparés dans Railway :

### 1. Service Celery Worker

```bash
# Dans Railway Dashboard:
# - Créer un nouveau service "celery-worker"
# - Commande: celery -A config worker -l info
# - Variables: Même DATABASE_URL, CELERY_BROKER_URL, etc.
```

### 2. Service Celery Beat

```bash
# Dans Railway Dashboard:
# - Créer un nouveau service "celery-beat"
# - Commande: celery -A config beat -l info
# - Variables: Même DATABASE_URL, CELERY_BROKER_URL, etc.
```

**Avantages :**
- ✅ Railway peut monitorer chaque service
- ✅ Redémarrage automatique en cas de crash
- ✅ Logs visibles et traçables
- ✅ Scalabilité indépendante

## Configuration alternative (Option B - Simple)

Si vous n'avez pas besoin de tâches asynchrones :

1. Garder Celery désactivé (configuration actuelle)
2. Les tâches longues peuvent être exécutées en synchrone
3. Ajouter Celery plus tard si nécessaire

## Variables d'environnement requises

Pour que Celery fonctionne, assurez-vous que ces variables sont définies :

```
CELERY_BROKER_URL=redis://default:PASSWORD@redis.railway.internal:6379
CELERY_RESULT_BACKEND=redis://default:PASSWORD@redis.railway.internal:6379
DATABASE_URL=postgresql://...
```

## Vérification

Pour vérifier que Celery est bien configuré :

```bash
# Localement
celery -A config inspect active

# Sur Railway (via SSH ou logs)
celery -A config inspect active_queues
```

## Tâches Celery disponibles

Les tâches suivantes sont définies dans `config/celery.py` :

- `entrainer-modeles-hebdomadaire` - Entraînement des modèles ML
- `generer-recommandations-quotidiennes` - Génération des recommandations
- `verifier-alertes-*` - Vérification des alertes prix
- `comparer-prix-homologues-quotidien` - Comparaison des prix
- `import-dgccrf-quotidien` - Import des données DGCCRF
- `backup-database-*` - Backup de la base de données

## Troubleshooting

### Celery Worker ne démarre pas

1. Vérifier que Redis est accessible
2. Vérifier les logs : `railway logs`
3. Vérifier `CELERY_BROKER_URL` est défini correctement

### Tâches ne s'exécutent pas

1. Vérifier que Celery Beat est en cours d'exécution
2. Vérifier que Celery Worker est en cours d'exécution
3. Vérifier les logs Celery pour les erreurs

### Erreur "Connection refused"

1. Vérifier que Redis est accessible depuis Railway
2. Vérifier que `CELERY_BROKER_URL` pointe vers le bon Redis
3. Vérifier les pare-feu/règles de sécurité

## Prochaines étapes

1. Créer les services Celery séparés dans Railway (Option A)
2. Ou confirmer que Celery n'est pas nécessaire (Option B)
3. Tester les tâches Celery en production
