# Configuration pour l'application mobile

Ce document explique comment configurer le backend pour qu'il fonctionne avec l'application mobile.

## Prérequis

- Python 3.8+
- Django 4.2+
- djangorestframework-simplejwt
- django-cors-headers
- PostgreSQL

## Configuration du backend

### 1. Variables d'environnement

Créez un fichier `.env` à la racine du projet avec les variables suivantes :

```
# Configuration de la base de données
POSTGRES_DB=comparateur_prix
POSTGRES_USER=postgres
POSTGRES_PASSWORD=votre_mot_de_passe
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Clé secrète Django
DJANGO_SECRET_KEY=votre_clé_secrète_très_longue_et_sécurisée

# Configuration JWT
JWT_ALGORITHM=HS256
JWT_ACCESS_MIN=60
JWT_REFRESH_DAYS=30

# Configuration CORS (optionnel)
CORS_ALLOWED_ORIGINS=http://localhost:19000,http://localhost:19006,http://192.168.1.65:19000,http://192.168.1.65:19006
CSRF_TRUSTED_ORIGINS=http://localhost:19000,http://localhost:19006,http://192.168.1.65:19000,http://192.168.1.65:19006

# Configuration de débogage
DEBUG=True
```

### 2. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 3. Migrations de la base de données

```bash
python manage.py migrate
```

### 4. Création d'un superutilisateur (optionnel)

```bash
python manage.py createsuperuser
```

### 5. Démarrage du serveur de développement

```bash
python manage.py runserver 0.0.0.0:8000
```

## Configuration de l'application mobile

1. Assurez-vous que l'application mobile est configurée pour utiliser l'URL du backend dans le fichier `.env`
2. L'URL par défaut est `http://192.168.1.65:8000/api` (remplacez par l'IP de votre machine)

## Dépannage

### Problèmes de connexion

- Vérifiez que le serveur Django est en cours d'exécution
- Vérifiez que le port 8000 est accessible depuis votre appareil mobile/émulateur
- Vérifiez les journaux du serveur pour les erreurs

### Problèmes CORS

- Vérifiez que `CORS_ALLOWED_ORIGINS` contient l'URL de votre application mobile
- Vérifiez que `CSRF_TRUSTED_ORIGINS` contient également ces URL

### Problèmes d'authentification

- Vérifiez que les tokens JWT sont correctement générés
- Vérifiez que les en-têtes d'autorisation sont correctement envoyés

## Sécurité

En production :
- Ne jamais utiliser `DEBUG=True`
- Utilisez HTTPS
- Configurez correctement les en-têtes de sécurité
- Utilisez des clés secrètes fortes
- Limitez les origines CORS aux domaines autorisés
