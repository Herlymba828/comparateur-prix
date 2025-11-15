# Guide de Déploiement - ftp.navixtechnology.com

## Configuration du domaine

Le backend Django est configuré pour être hébergé sur **ftp.navixtechnology.com**.

### Modifications apportées

1. **ALLOWED_HOSTS** : Le domaine `ftp.navixtechnology.com` a été ajouté à la liste des hôtes autorisés
2. **CORS_ALLOWED_ORIGINS** : Les origines HTTP et HTTPS ont été ajoutées pour permettre les requêtes cross-origin
3. **CSRF_TRUSTED_ORIGINS** : Les origines ont été ajoutées pour la protection CSRF

## Variables d'environnement requises en production

Assurez-vous de définir les variables d'environnement suivantes sur votre serveur :

### Sécurité
```bash
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<votre-clé-secrète-générée>
```

### Base de données
```bash
POSTGRES_DB=<nom-de-la-base>
POSTGRES_USER=<utilisateur-postgres>
POSTGRES_PASSWORD=<mot-de-passe-postgres>
POSTGRES_HOST=<hôte-postgres>
POSTGRES_PORT=5432
POSTGRES_SSL_REQUIRE=True  # Recommandé en production
```

### JWT (si utilisé)
```bash
USE_JWT_AUTH=True
JWT_ACCESS_MIN=60
JWT_REFRESH_DAYS=30
```

### CORS (optionnel - pour ajouter d'autres origines)
```bash
CORS_ALLOWED_ORIGINS=https://votre-frontend.com,https://www.votre-frontend.com
CSRF_TRUSTED_ORIGINS=https://votre-frontend.com,https://www.votre-frontend.com
```

### Redis (optionnel - pour le cache et Celery)
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
```

## Configuration du serveur web

### Nginx (exemple)

```nginx
server {
    listen 80;
    server_name ftp.navixtechnology.com;
    
    # Redirection HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ftp.navixtechnology.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # Configuration SSL recommandée
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Headers de sécurité
    add_header X-Forwarded-Proto $scheme;
    
    # Fichiers statiques
    location /static/ {
        alias /path/to/your/project/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # Fichiers médias
    location /media/ {
        alias /path/to/your/project/media/;
        expires 7d;
    }
    
    # Proxy vers Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### Gunicorn (exemple)

```bash
gunicorn config.wsgi:application \
    --bind 127.0.0.1:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile /var/log/gunicorn/access.log \
    --error-logfile /var/log/gunicorn/error.log \
    --log-level info
```

## Commandes de déploiement

### 1. Collecter les fichiers statiques
```bash
python manage.py collectstatic --noinput
```

### 2. Appliquer les migrations
```bash
python manage.py migrate
```

### 3. Créer un superutilisateur (si nécessaire)
```bash
python manage.py createsuperuser
```

### 4. Vérifier la configuration
```bash
python manage.py check --deploy
```

## Sécurité en production

Les paramètres de sécurité suivants sont automatiquement activés lorsque `DEBUG=False` :

- ✅ `SESSION_COOKIE_SECURE = True`
- ✅ `CSRF_COOKIE_SECURE = True`
- ✅ `SECURE_SSL_REDIRECT = True`
- ✅ `SECURE_HSTS_SECONDS = 31536000`
- ✅ `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- ✅ `SECURE_HSTS_PRELOAD = True`
- ✅ `X_FRAME_OPTIONS = 'DENY'`
- ✅ `SECURE_CONTENT_TYPE_NOSNIFF = True`
- ✅ `SECURE_BROWSER_XSS_FILTER = True`

## Monitoring et logs

Les logs sont configurés dans `config/optimizations/logging.py`. En production, vérifiez :

- Les logs d'erreur Django
- Les logs du serveur web (Nginx/Apache)
- Les logs de Gunicorn
- Les logs de Celery (si utilisé)

## Checklist de déploiement

- [ ] Variables d'environnement configurées
- [ ] `DJANGO_DEBUG=False` défini
- [ ] `DJANGO_SECRET_KEY` défini et sécurisé
- [ ] Base de données PostgreSQL configurée et accessible
- [ ] Migrations appliquées
- [ ] Fichiers statiques collectés
- [ ] Certificat SSL configuré
- [ ] Serveur web (Nginx/Apache) configuré
- [ ] Gunicorn/Uvicorn configuré et démarré
- [ ] Celery workers démarrés (si utilisé)
- [ ] Tests de connectivité effectués
- [ ] Monitoring configuré

## Support

En cas de problème, vérifiez :
1. Les logs du serveur
2. La configuration des variables d'environnement
3. La connectivité à la base de données
4. Les permissions des fichiers et répertoires

