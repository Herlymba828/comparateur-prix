# Développement

## Environnement
- Copier `.env.example` en `.env` et renseigner les variables nécessaires.
- Créer un venv, installer `requirements.txt`.

## Lancement
```bash
python comparateur_prix/manage.py runserver
celery -A comparateur_prix.config worker -l info
celery -A comparateur_prix.config beat -l info
```

## Tests
```bash
python comparateur_prix/manage.py test
# Tests ciblés
python comparateur_prix/manage.py test apps.api
python comparateur_prix/manage.py test apps.prix
```

## Style/Qualité
- Respecter PEP8/Black (si configuré).
- Ajouter des tests unitaires pour chaque nouveau module/endpoint.

## Conventions
- Noms de routes API en kebab-case (ex: `comparaisons-prix`).
- Modules applicatifs sous `apps/`.

## Données de démo
- Utiliser la commande `import_dgccrf` avec `--dry-run` pour inspecter les données.
