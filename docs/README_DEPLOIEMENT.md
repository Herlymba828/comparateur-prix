# Guide de Déploiement Rapide - Railway

## 🚀 Déploiement sur Railway

### Étape 1 : Préparer les fichiers localement

1. **Générer une clé secrète** :
   ```bash
   python scripts/generate_secret_key.py
   ```
   Copiez la clé générée.

2. **Vérifier que ces fichiers existent** :
   - ✅ `.htaccess` (créé)
   - ✅ `passenger_wsgi.py` (créé)
   - ✅ `index.py` (créé)
   - ✅ `requirements.txt`
   - ✅ `runtime.txt`
   - ✅ `.env.example`

Consultez la documentation complète de déploiement Railway : `docs/DEPLOIEMENT_RAILWAY.md`

Railway configure automatiquement :
- ✅ Base de données PostgreSQL via `DATABASE_URL`
- ✅ Redis via `REDIS_URL`
- ✅ Variables d'environnement
- ✅ SSL/HTTPS
- ✅ Déploiement continu via Git

