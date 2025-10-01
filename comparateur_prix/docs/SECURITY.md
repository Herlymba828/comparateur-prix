# Sécurité

## Secrets
- Ne pas commiter `.env` (voir `.gitignore`).
- Regénérer/rotater immédiatement toute clé exposée (ex: clés Google Maps, mots de passe DB).

## Django
- `DJANGO_DEBUG=False` en production.
- `DJANGO_ALLOWED_HOSTS` explicites.

## CORS/CSRF
- En dev: `CORS_ALLOW_ALL_ORIGINS` peut être `True`.
- En prod: par défaut désactivé (valeur forcée dans `settings.py`), définir `CORS_ALLOWED_ORIGINS`.
- Définir `CSRF_TRUSTED_ORIGINS` derrière un reverse proxy.

## HTTPS
- Cookies sécurisés + HSTS activés automatiquement quand `DEBUG=False`.
- Terminer TLS au niveau du reverse proxy ou de la plateforme (ex: Nginx).

## Permissions API
- DRF par défaut: `AllowAny`. Restreindre selon besoin.
- JWT disponible (SimpleJWT) si `USE_JWT_AUTH=True`.

## Base de données
- Utiliser un utilisateur DB dédié avec droits minimaux.
- Sauvegardes régulières et chiffrement au repos si possible.
