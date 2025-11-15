# Optimisation des Modèles ML - Chargement depuis le disque

## Problème identifié

Les modèles ML étaient entraînés à chaque démarrage de Django, ce qui :
- Ralentissait considérablement le démarrage (plusieurs secondes)
- Consommait inutilement des ressources CPU
- N'était pas nécessaire si les données n'avaient pas changé

## Solution implémentée

### 1. Sauvegarde automatique des modèles

Les modèles entraînés sont maintenant sauvegardés dans :
```
ml_models/saved/
  ├── modele_contenu.joblib
  └── modele_prix.joblib
```

### 2. Chargement intelligent

Au démarrage, le système :
1. **Vérifie si les modèles existent** sur le disque
2. **Vérifie l'âge des modèles** (réentraînement si > 7 jours)
3. **Charge les modèles depuis le disque** si valides
4. **Réentraîne uniquement si nécessaire**

### 3. Réentraînement automatique

Les modèles sont réentraînés automatiquement si :
- Les fichiers n'existent pas
- Les modèles sont trop anciens (> 7 jours)
- Le chargement échoue
- `force_retrain=True` est passé

## Avantages

✅ **Démarrage plus rapide** : ~5 secondes → ~0.5 secondes  
✅ **Moins de charge CPU** : Pas d'entraînement inutile  
✅ **Modèles persistants** : Survivent aux redémarrages  
✅ **Réentraînement intelligent** : Seulement quand nécessaire  

## Configuration

### Désactiver l'initialisation au démarrage

Par défaut, l'initialisation est désactivée. Pour l'activer :

```bash
# Dans .env
RECO_INIT_MODELS_ON_STARTUP=True
```

### Forcer le réentraînement

```python
from apps.recommandations.modeles_ml import GestionnaireRecommandations

gestionnaire = GestionnaireRecommandations()
gestionnaire.initialiser_modeles(force_retrain=True)
```

## Installation optionnelle : XGBoost et LightGBM

Pour améliorer les performances de prédiction de prix, vous pouvez installer :

```bash
pip install xgboost==2.0.3 lightgbm==4.1.0
```

Ou décommentez dans `requirements.txt` :
```txt
xgboost==2.0.3
lightgbm==4.1.0
```

**Note** : Ces bibliothèques sont optionnelles. Le système fonctionne avec RandomForest par défaut.

## Vérification

### Vérifier que les modèles sont chargés

Regardez les logs au démarrage :
```
[INFO] Modèles chargés depuis le disque (pas de réentraînement)
```

### Vérifier les fichiers de modèles

```bash
ls -lh ml_models/saved/
```

### Forcer le réentraînement

Supprimez les fichiers pour forcer le réentraînement :
```bash
rm ml_models/saved/*.joblib
```

## Problèmes connus

### System check warnings

Si vous voyez des warnings au démarrage, vérifiez :
1. Les migrations sont à jour : `python manage.py migrate`
2. Les variables d'environnement sont correctes
3. Les dépendances sont installées

### Modèles corrompus

Si le chargement échoue, les modèles seront automatiquement réentraînés.

## Performance

| Scénario | Temps avant | Temps après |
|----------|-------------|-------------|
| Premier démarrage | ~5s | ~5s (entraînement) |
| Démarrages suivants | ~5s | ~0.5s (chargement) |
| Après 7 jours | ~5s | ~5s (réentraînement) |

## Maintenance

### Nettoyage des anciens modèles

Les modèles sont automatiquement réentraînés après 7 jours. Pour changer cette durée, modifiez `modele_age_max` dans `initialiser_modeles()`.

### Sauvegarde manuelle

Les modèles sont sauvegardés automatiquement après l'entraînement. Vous pouvez aussi les sauvegarder manuellement :

```python
gestionnaire.modele_contenu.sauvegarder('chemin/modele.joblib')
gestionnaire.modele_prix.sauvegarder('chemin/prix.joblib')
```

