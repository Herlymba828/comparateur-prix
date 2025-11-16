# 🔄 Remplacer le fichier WSGI de test par le fichier Django

## 🚨 Problème

cPanel a créé un fichier WSGI de test par défaut qui affiche simplement "It works!". Ce fichier ne configure pas Django et doit être remplacé.

---

## ✅ Solution : Remplacer par le fichier Django

### Étape 1 : Identifier le fichier à remplacer

Le fichier que vous avez montré est probablement :
- `passenger_wsgi.py` (si cPanel l'a créé)
- `application.py` (nom alternatif)
- Ou un autre fichier WSGI dans votre projet

### Étape 2 : Contenu correct pour Django

Remplacez le contenu du fichier par ce code :

```python
"""
Fichier WSGI pour Passenger (cPanel)
Ce fichier est utilisé par Passenger pour démarrer l'application Django
"""
import sys
import os

# Ajouter le répertoire du projet au path Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Activer l'environnement virtuel
# ⚠️ IMPORTANT : Remplacez ce chemin par le chemin réel de votre environnement virtuel
# Vous le trouvez dans cPanel → Setup Python App → Virtual Environment
activate_this = '/home/rs2694021ez6eg8n/virtualenv/nom_de_votre_app/3.11/bin/activate_this.py'
if os.path.exists(activate_this):
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Charger les variables d'environnement depuis .env si python-dotenv est installé
try:
    from dotenv import load_dotenv
    env_path = os.path.join(BASE_DIR, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv n'est pas installé, continuer sans

# Importer l'application WSGI Django
from django.core.wsgi import get_wsgi_application

# Créer l'application WSGI
application = get_wsgi_application()
```

---

## 📝 Instructions étape par étape

### Option A : Via SSH (Recommandé)

1. **Connectez-vous en SSH** à votre serveur

2. **Allez dans le répertoire de votre projet** :
```bash
cd /chemin/vers/votre/projet
# Exemple : cd /home/rs2694021ez6eg8n/public_html/comparer
```

3. **Sauvegardez l'ancien fichier** (au cas où) :
```bash
cp passenger_wsgi.py passenger_wsgi.py.backup
```

4. **Éditez le fichier** :
```bash
nano passenger_wsgi.py
```

5. **Remplacez tout le contenu** par le code ci-dessus

6. **Important** : Modifiez la ligne 13 avec le chemin réel de votre environnement virtuel :
   - Trouvez-le dans cPanel → Setup Python App
   - Il ressemble à : `/home/rs2694021ez6eg8n/virtualenv/nom_app/3.11/bin/activate_this.py`

7. **Sauvegardez** : `Ctrl+O` puis `Enter`, puis `Ctrl+X`

8. **Vérifiez les permissions** :
```bash
chmod 755 passenger_wsgi.py
```

### Option B : Via File Manager de cPanel

1. **Dans cPanel**, allez dans **File Manager**

2. **Naviguez** vers le répertoire de votre projet

3. **Trouvez le fichier** `passenger_wsgi.py` (ou le fichier WSGI)

4. **Cliquez dessus** → **Edit**

5. **Remplacez tout le contenu** par le code ci-dessus

6. **Important** : Modifiez la ligne 13 avec le chemin réel de votre environnement virtuel

7. **Sauvegardez** → **Save Changes**

---

## 🔍 Trouver le chemin de l'environnement virtuel

### Méthode 1 : Dans cPanel

1. Allez dans **Setup Python App**
2. Cliquez sur votre application
3. Regardez la section **Virtual Environment**
4. Le chemin est affiché, par exemple : `/home/rs2694021ez6eg8n/virtualenv/compare2/3.11/`
5. Le chemin complet pour `activate_this.py` sera : `/home/rs2694021ez6eg8n/virtualenv/compare2/3.11/bin/activate_this.py`

### Méthode 2 : Via SSH

```bash
# Chercher les environnements virtuels
find /home/rs2694021ez6eg8n/virtualenv -name "activate_this.py" 2>/dev/null
```

---

## ⚙️ Configuration dans cPanel

Après avoir remplacé le fichier, vérifiez dans cPanel :

1. **Setup Python App** → Votre application
2. Vérifiez que **Application File** est bien `passenger_wsgi.py`
3. Vérifiez que **App Root** pointe vers le bon répertoire
4. Cliquez sur **Restart** pour redémarrer l'application

---

## ✅ Vérification

### Test 1 : Vérifier que le fichier est correct

```bash
# Via SSH
cd /chemin/vers/votre/projet
python -c "import passenger_wsgi; print('OK')"
```

Si vous voyez une erreur, vérifiez :
- Le chemin de l'environnement virtuel
- Que Django est installé dans l'environnement virtuel
- Les permissions du fichier

### Test 2 : Tester l'application

1. **Redémarrez l'application** dans cPanel → Setup Python App → Restart
2. **Testez dans le navigateur** :
   - `https://comparateurdeprix.com/api/health/`
   - Doit retourner : `{"status": "ok"}`

---

## 🚨 Erreurs courantes

### Erreur : "ModuleNotFoundError: No module named 'django'"

**Cause** : Django n'est pas installé dans l'environnement virtuel

**Solution** :
```bash
# Activer l'environnement virtuel
source /home/rs2694021ez6eg8n/virtualenv/nom_app/3.11/bin/activate

# Installer Django et les dépendances
cd /chemin/vers/votre/projet
pip install -r requirements.txt
```

### Erreur : "No module named 'config'"

**Cause** : Le répertoire du projet n'est pas dans le path Python

**Solution** : Vérifiez que `BASE_DIR` dans `passenger_wsgi.py` pointe vers le bon répertoire (celui contenant `manage.py`)

### Erreur : "activate_this.py not found"

**Cause** : Le chemin de l'environnement virtuel est incorrect

**Solution** :
1. Vérifiez le chemin dans cPanel → Setup Python App
2. Vérifiez que le fichier existe :
```bash
ls -la /home/rs2694021ez6eg8n/virtualenv/nom_app/3.11/bin/activate_this.py
```

Si le fichier n'existe pas, utilisez `activate` au lieu de `activate_this.py` :
```python
activate_this = '/home/rs2694021ez6eg8n/virtualenv/nom_app/3.11/bin/activate'
```

---

## 📋 Checklist

- [ ] ✅ Fichier WSGI de test remplacé par le fichier Django
- [ ] ✅ Chemin de l'environnement virtuel correct dans `passenger_wsgi.py`
- [ ] ✅ Application File configuré dans cPanel → Setup Python App
- [ ] ✅ Application redémarrée dans cPanel
- [ ] ✅ Test réussi : `https://comparateurdeprix.com/api/health/`

---

## 🎯 Résumé

**Le fichier que vous avez montré** est un fichier de test qui affiche "It works!". 

**Vous devez le remplacer** par le fichier `passenger_wsgi.py` qui configure Django correctement.

**Points importants** :
1. Remplacez tout le contenu du fichier
2. Modifiez le chemin de l'environnement virtuel (ligne 13)
3. Vérifiez que l'Application File dans cPanel est bien `passenger_wsgi.py`
4. Redémarrez l'application dans cPanel

Une fois fait, votre application Django devrait fonctionner correctement !

