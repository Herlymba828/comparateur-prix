# Guide de Parsing DGCCRF - Page Liste Produits

## Vue d'ensemble

Le scraper DGCCRF a été amélioré pour mieux parser la page [https://www.dgccrf.ga/echo-liste-produit](https://www.dgccrf.ga/echo-liste-produit) qui contient la liste des 67 produits défiscalisés à prix bloqués.

## Améliorations apportées

### 1. Détection des catégories

Le parser détecte maintenant automatiquement les catégories de produits qui précèdent chaque tableau :
- **VIANDE DE PORC**
- **VIANDE DE BOEUF**
- **VOLAILLE**
- **POISSON**
- **CONSERVES DE POISSON**
- **CONSERVES DE LEGUMES**
- **PATES ALIMENTAIRES**
- **LAITS MATIERES GRASSES ANIMALES**
- **LAITS MATIERES GRASSES VEGETALES**
- **LAITS INFANTILES**
- **RIZ PARFUME AU JASMIN ENTIER**
- **HUILE RAFFINEE**
- **SUCRE**
- **POISSON DE PECHE LOCALE**

Ces catégories sont stockées dans le champ `sous_categorie` de chaque produit.

### 2. Parsing des colonnes de tableaux

Le parser gère correctement les colonnes suivantes :
- **N** : Numéro de référence (stocké dans `reference_numero`)
- **DESIGNATION** : Nom du produit (stocké dans `nom`)
- **PRIX GROS** : Prix de gros (stocké dans `extra.prix_gros`)
- **PRIX DEMI GROS** : Prix demi-gros (stocké dans `extra.prix_demi_gros`)
- **PRIX DETAIL** : Prix au détail (stocké dans `prix_detail` et `prix_unitaire`)

### 3. Extraction de l'origine

Le parser extrait automatiquement l'origine depuis les parenthèses dans la désignation :
- Exemple : "Cuisses de Poulet (USA)" → `nom: "Cuisses de Poulet"`, `extra.origine: "USA"`
- Exemple : "Maquereaux 300g - 500g (ASIE)" → `nom: "Maquereaux 300g - 500g"`, `extra.origine: "ASIE"`

### 4. Parsing des conditionnements

Le parser gère maintenant plusieurs formats de conditionnement :

#### Formats supportés :
- `125g x 50` → 50 unités de 125g = 6250g total
- `400g x 24` → 24 unités de 400g = 9600g total
- `10lbs ou 4,54Kg x 10` → 10 unités de 4,54kg = 45,4kg total (prend la partie après "ou")
- `1L` → 1 unité de 1L
- `500ml` → 1 unité de 500ml

#### Conversion automatique :
- Les livres (lbs) sont automatiquement converties en kilogrammes (1 lb = 0.453592 kg)
- Les formats avec "ou" utilisent la partie métrique (après "ou")

### 5. Extraction de la marque

Le parser tente d'extraire la marque depuis la désignation en cherchant des mots en majuscules :
- Exemple : "Sardines à huile Princesse 125g" → `marque: "PRINCESSE"`

## Utilisation

### Exemple basique

```python
from scripts.scraper_dgccrf import DgccrfScraper

scraper = DgccrfScraper()

# Parser la page liste produits
for item in scraper.iter_from_liste_produit_page():
    print(f"Produit: {item['nom']}")
    print(f"Catégorie: {item['sous_categorie']}")
    print(f"Prix détail: {item['prix_detail']} FCFA")
    print(f"Prix gros: {item.get('extra', {}).get('prix_gros')} FCFA")
    print(f"Origine: {item.get('extra', {}).get('origine')}")
    print("---")
```

### Exemple avec sauvegarde en base de données

```python
from scripts.scraper_dgccrf import DgccrfScraper

scraper = DgccrfScraper()
items = list(scraper.iter_from_liste_produit_page())

# Sauvegarder en base de données
if scraper._init_django():
    created_prod, created_prix = scraper.persist_items(items)
    print(f"Créés: {created_prod} produits, {created_prix} prix")
```

### Exemple avec export JSON

```python
import json
from scripts.scraper_dgccrf import DgccrfScraper

scraper = DgccrfScraper()
items = list(scraper.iter_from_liste_produit_page())

# Exporter en JSON
with open('produits_dgccrf.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)
```

### Utilisation en ligne de commande

```bash
# Parser uniquement la page liste produits
python scripts/scraper_dgccrf.py --sources liste_produit --out data/produits.json

# Parser et sauvegarder en base de données
python scripts/scraper_dgccrf.py --sources liste_produit --save

# Parser et exporter en CSV
python scripts/scraper_dgccrf.py --sources liste_produit --csv data/produits.csv
```

## Structure des données extraites

Chaque produit extrait a la structure suivante :

```json
{
  "nom": "Cotis de Porc viandé",
  "categorie": "Produits défiscalisés",
  "sous_categorie": "VIANDE DE PORC",
  "format": "1.0unite",
  "marque": "",
  "prix_unitaire": 1875.0,
  "unite": "unite",
  "prix_detail": 1875.0,
  "prix_par_kilo": null,
  "date_publication": null,
  "periode_debut": null,
  "periode_fin": null,
  "reference_titre": "Produits défiscalisés",
  "reference_numero": "1",
  "reference_url": "https://www.dgccrf.ga/echo-liste-produit",
  "description": "1 | Cotis de Porc viandé | 16 340 F CFA | 16 990 F CFA | 1 875 F CFA",
  "zone": "",
  "devise": "FCFA",
  "type_prix": "detail",
  "extra": {
    "prix_gros": 16340.0,
    "prix_demi_gros": 16990.0,
    "origine": null,
    "conditionnement": {}
  }
}
```

## Tests

Les tests unitaires sont disponibles dans `tests/scraper/test_dgccrf_parsing.py` :

```bash
python -m pytest tests/scraper/test_dgccrf_parsing.py
```

## Notes importantes

1. **Respect des robots.txt** : Le scraper respecte par défaut le fichier robots.txt du site
2. **Délai entre requêtes** : Un délai de 1 seconde est appliqué entre les requêtes pour éviter de surcharger le serveur
3. **Gestion des erreurs** : Le scraper gère automatiquement les erreurs de réseau avec retry et backoff
4. **Détection de changements** : Le scraper peut détecter si la page a changé depuis la dernière extraction

## Configuration

Les variables d'environnement suivantes peuvent être utilisées pour configurer le scraper :

- `DGCCRF_BASE_URL` : URL de base du site (défaut: `https://www.dgccrf.ga/`)
- `DGCCRF_LISTE_PRODUIT_URL` : URL de la page liste produits (défaut: `https://www.dgccrf.ga/echo-liste-produit`)
- `DGCCRF_REQUEST_DELAY` : Délai entre requêtes en secondes (défaut: `1.0`)
- `DGCCRF_TIMEOUT` : Timeout des requêtes en secondes (défaut: `30`)
- `DGCCRF_MAX_RETRIES` : Nombre maximum de tentatives (défaut: `3`)
- `DGCCRF_RESPECT_ROBOTS` : Respecter robots.txt (défaut: `true`)

