# 🔧 Résolution de l'erreur "POSTGRES_PASSWORD must be set in production"

## ❌ Problème

Lors de l'exécution de `python manage.py dbshell`, vous obtenez l'erreur :
```
django.core.exceptions.ImproperlyConfigured: POSTGRES_PASSWORD must be set in production
```

Même si votre fichier `.env` contient `DB_PASSWORD=BlackEurtz8282@`.

## 🔍 Diagnostic

### Étape 1 : Exécuter le script de diagnostic

Sur le serveur, exécutez :

```bash
cd /home/rs2694021ez6eg8n/comparer1/comparateur-prix
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate
python scripts/diagnostic_env.py
```

Ce script va :
- Vérifier si le fichier `.env` est trouvé
- Afficher toutes les variables d'environnement liées à la base de données
- Indiquer quelles variables sont présentes/absentes
- Vérifier la configuration finale

### Étape 2 : Vérifier manuellement le fichier .env

```bash
cd /home/rs2694021ez6eg8n/comparer1/comparateur-prix
cat .env | grep -i password
```

Vous devriez voir :
```
DB_PASSWORD=BlackEurtz8282@
```

### Étape 3 : Vérifier le format du fichier .env

Le fichier `.env` doit respecter ces règles :
- **Pas d'espaces** autour du signe `=`
- **Pas de guillemets** sauf si nécessaire (pour les valeurs avec espaces)
- **Pas de caractères spéciaux** non échappés (le `@` devrait être OK)

**Format correct :**
```bash
DB_PASSWORD=BlackEurtz8282@
```

**Formats incorrects :**
```bash
DB_PASSWORD = BlackEurtz8282@    # Espaces autour du =
DB_PASSWORD="BlackEurtz8282@"    # Guillemets inutiles (peut causer des problèmes)
DB_PASSWORD='BlackEurtz8282@'    # Guillemets simples (peut causer des problèmes)
```

## ✅ Solutions

### Solution 1 : Vérifier que le fichier .env est au bon endroit

Le fichier `.env` doit être à la racine du projet Django, c'est-à-dire :
```
/home/rs2694021ez6eg8n/comparer1/comparateur-prix/.env
```

Vérifiez :
```bash
ls -la /home/rs2694021ez6eg8n/comparer1/comparateur-prix/.env
```

### Solution 2 : Vérifier le format de la ligne DB_PASSWORD

Assurez-vous que la ligne est exactement :
```bash
DB_PASSWORD=BlackEurtz8282@
```

Sans espaces, sans guillemets.

### Solution 3 : Vérifier que le fichier .env est bien lu

Testez avec Python directement :

```bash
cd /home/rs2694021ez6eg8n/comparer1/comparateur-prix
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate
python -c "from dotenv import load_dotenv; import os; from pathlib import Path; load_dotenv(Path('.env')); print('DB_PASSWORD:', os.getenv('DB_PASSWORD'))"
```

Si cela affiche `None` ou une chaîne vide, le fichier `.env` n'est pas lu correctement.

### Solution 4 : Vérifier les permissions du fichier .env

```bash
ls -la .env
```

Les permissions doivent être `600` (lecture/écriture pour le propriétaire uniquement) :
```bash
chmod 600 .env
```

### Solution 5 : Vérifier qu'il n'y a pas de caractères invisibles

Parfois, des caractères invisibles (retours à la ligne Windows, BOM, etc.) peuvent causer des problèmes.

Pour nettoyer le fichier :
```bash
# Créer une sauvegarde
cp .env .env.backup

# Nettoyer les retours à la ligne Windows
sed -i 's/\r$//' .env

# Vérifier qu'il n'y a pas de caractères bizarres
cat -A .env | grep DB_PASSWORD
```

### Solution 6 : Utiliser une variable alternative

Si `DB_PASSWORD` ne fonctionne pas, essayez `MYSQL_PASSWORD` (puisque vous utilisez MySQL) :

Dans votre `.env`, ajoutez ou remplacez :
```bash
MYSQL_PASSWORD=BlackEurtz8282@
```

### Solution 7 : Vérifier que DEBUG est bien False

Si `DJANGO_DEBUG=True`, la vérification du mot de passe ne se fait pas. Mais en production, vous devez avoir `DJANGO_DEBUG=False`.

Vérifiez :
```bash
grep DJANGO_DEBUG .env
```

## 🧪 Test après correction

Après avoir appliqué une solution, testez :

```bash
cd /home/rs2694021ez6eg8n/comparer1/comparateur-prix
source /home/rs2694021ez6eg8n/virtualenv/public_html/comparer/3.11/bin/activate

# Test 1: Vérifier que la variable est lue
python -c "from dotenv import load_dotenv; import os; from pathlib import Path; load_dotenv(Path('.env')); print('DB_PASSWORD lu:', 'OUI' if os.getenv('DB_PASSWORD') else 'NON')"

# Test 2: Essayer dbshell
python manage.py dbshell

# Test 3: Vérifier la configuration Django
python manage.py check --deploy
```

## 📋 Checklist de vérification

- [ ] Le fichier `.env` existe à `/home/rs2694021ez6eg8n/comparer1/comparateur-prix/.env`
- [ ] La ligne `DB_PASSWORD=BlackEurtz8282@` est présente dans le fichier
- [ ] Il n'y a **pas d'espaces** autour du signe `=`
- [ ] Il n'y a **pas de guillemets** autour de la valeur
- [ ] Les permissions du fichier sont `600` (`chmod 600 .env`)
- [ ] Le script de diagnostic confirme que `DB_PASSWORD` est lu
- [ ] `DJANGO_DEBUG=False` dans le fichier `.env`
- [ ] `DB_ENGINE=mysql` dans le fichier `.env`

## 🔍 Si le problème persiste

Si après toutes ces vérifications le problème persiste :

1. **Vérifiez les logs détaillés** :
   ```bash
   python manage.py check --deploy --verbosity 2
   ```

2. **Vérifiez que python-dotenv est installé** :
   ```bash
   pip list | grep dotenv
   ```

3. **Réinstallez python-dotenv** :
   ```bash
   pip install --upgrade python-dotenv
   ```

4. **Vérifiez le chemin exact du fichier .env** :
   Le code Django cherche le fichier `.env` dans `BASE_DIR`, qui est le répertoire parent de `config/`. 
   Donc si votre structure est :
   ```
   /home/rs2694021ez6eg8n/comparer1/comparateur-prix/
   ├── config/
   │   └── settings.py
   └── .env  ← Doit être ici
   ```

5. **Testez avec un fichier .env minimal** :
   Créez un fichier `.env.test` avec juste :
   ```bash
   DB_ENGINE=mysql
   DB_NAME=rs2694021ez6eg8n_soutenance2.0
   DB_USER=rs2694021ez6eg8n_db_user
   DB_PASSWORD=BlackEurtz8282@
   DJANGO_DEBUG=False
   ```
   Puis testez :
   ```bash
   cp .env .env.backup
   cp .env.test .env
   python manage.py check --deploy
   ```

## 📞 Informations à fournir en cas de problème persistant

Si le problème persiste, collectez ces informations :

```bash
# 1. Emplacement du fichier .env
ls -la .env

# 2. Contenu de la ligne DB_PASSWORD (masqué)
grep DB_PASSWORD .env | sed 's/=.*/=***/'

# 3. Résultat du script de diagnostic
python scripts/diagnostic_env.py

# 4. Test de lecture directe
python -c "from dotenv import load_dotenv; import os; from pathlib import Path; load_dotenv(Path('.env')); print('DB_PASSWORD présent:', bool(os.getenv('DB_PASSWORD')))"

# 5. Version de python-dotenv
pip show python-dotenv
```

