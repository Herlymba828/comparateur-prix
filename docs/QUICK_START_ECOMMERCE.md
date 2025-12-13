# 🚀 DÉMARRAGE RAPIDE E-COMMERCE

## 🎯 MVP en 2 mois - Plan d'action

### Semaine 1-2 : Panier d'achat

```bash
# 1. Créer l'app ecommerce
python manage.py startapp ecommerce

# 2. Ajouter à INSTALLED_APPS
# config/settings.py
INSTALLED_APPS = [
    ...
    'apps.ecommerce',
]

# 3. Créer les modèles
# Copier les modèles Panier et ItemPanier depuis ECOMMERCE_EVOLUTION.md

# 4. Migrations
python manage.py makemigrations ecommerce
python manage.py migrate

# 5. Créer les serializers et views
# apps/ecommerce/serializers.py
# apps/ecommerce/views.py

# 6. Tester
python manage.py test apps.ecommerce
```

### Semaine 3-5 : Système de commandes

```bash
# 1. Ajouter les modèles Commande et LigneCommande

# 2. Migrations
python manage.py makemigrations
python manage.py migrate

# 3. Créer l'API de commande
# POST /api/commandes/creer/
# GET /api/commandes/
# GET /api/commandes/{id}/

# 4. Tester le flow complet
# Panier → Commande → Confirmation
```

### Semaine 6 : Paiement Stripe

```bash
# 1. Installer Stripe
pip install stripe

# 2. Configuration
# .env
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# 3. Créer l'endpoint de paiement
# POST /api/paiements/creer-intent/
# POST /api/paiements/confirmer/

# 4. Tester avec cartes de test Stripe
```

### Semaine 7-8 : Livraison basique

```bash
# 1. Modèles ZoneLivraison et Livraison

# 2. Calculer frais de livraison
# GET /api/livraison/calculer-frais/

# 3. Assigner livraison
# POST /api/livraison/assigner/

# 4. Tracking simple
# GET /api/livraison/tracking/{code}/
```

---

## 📦 STRUCTURE DU PROJET E-COMMERCE

```
apps/
├── ecommerce/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── panier.py
│   │   ├── commande.py
│   │   ├── paiement.py
│   │   └── livraison.py
│   ├── serializers/
│   │   ├── __init__.py
│   │   ├── panier.py
│   │   ├── commande.py
│   │   └── paiement.py
│   ├── views/
│   │   ├── __init__.py
│   │   ├── panier.py
│   │   ├── commande.py
│   │   ├── paiement.py
│   │   └── livraison.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── panier_service.py
│   │   ├── commande_service.py
│   │   ├── paiement_service.py
│   │   └── livraison_service.py
│   ├── tasks.py
│   ├── urls.py
│   └── tests/
```

---

## 🔧 COMMANDES UTILES

```bash
# Créer l'app
python manage.py startapp ecommerce

# Migrations
python manage.py makemigrations ecommerce
python manage.py migrate

# Créer des données de test
python manage.py shell
>>> from apps.ecommerce.factories import create_test_data
>>> create_test_data()

# Tests
python manage.py test apps.ecommerce

# Lancer le serveur
python manage.py runserver

# Celery (pour tâches async)
celery -A config worker -l info
celery -A config beat -l info
```

---

## 📱 INTÉGRATION MOBILE

### React Native - Panier

```javascript
// screens/PanierScreen.js
import { usePanier } from '../hooks/usePanier';

export default function PanierScreen() {
  const { panier, ajouterItem, retirerItem, viderPanier } = usePanier();
  
  return (
    <View>
      <FlatList
        data={panier.items}
        renderItem={({ item }) => (
          <PanierItem
            item={item}
            onIncrement={() => ajouterItem(item.produit, 1)}
            onDecrement={() => retirerItem(item.id)}
          />
        )}
      />
      <Text>Total: {panier.total}€</Text>
      <Button title="Commander" onPress={handleCommander} />
    </View>
  );
}
```

### React Native - Paiement Stripe

```javascript
// screens/PaiementScreen.js
import { CardField, useStripe } from '@stripe/stripe-react-native';

export default function PaiementScreen({ route }) {
  const { confirmPayment } = useStripe();
  const { commande } = route.params;
  
  const handlePaiement = async () => {
    // 1. Créer payment intent
    const { clientSecret } = await api.post('/paiements/creer-intent/', {
      commande_id: commande.id
    });
    
    // 2. Confirmer le paiement
    const { error } = await confirmPayment(clientSecret, {
      paymentMethodType: 'Card',
    });
    
    if (error) {
      Alert.alert('Erreur', error.message);
    } else {
      navigation.navigate('Confirmation', { commande });
    }
  };
  
  return (
    <View>
      <CardField onCardChange={(cardDetails) => {}} />
      <Button title="Payer" onPress={handlePaiement} />
    </View>
  );
}
```

---

## 🧪 TESTS

```python
# apps/ecommerce/tests/test_panier.py
from django.test import TestCase
from apps.ecommerce.models import Panier, ItemPanier
from apps.produits.models import Produit

class PanierTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('test', 'test@test.com', 'pass')
        self.produit = Produit.objects.create(nom='Test', prix=10.00)
        self.panier = Panier.objects.create(utilisateur=self.user)
    
    def test_ajouter_item(self):
        item = ItemPanier.objects.create(
            panier=self.panier,
            produit=self.produit,
            quantite=2,
            prix_unitaire=10.00
        )
        self.assertEqual(self.panier.get_total(), 20.00)
    
    def test_vider_panier(self):
        ItemPanier.objects.create(
            panier=self.panier,
            produit=self.produit,
            quantite=1,
            prix_unitaire=10.00
        )
        self.panier.items.all().delete()
        self.assertEqual(self.panier.get_nombre_items(), 0)
```

---

## 📊 MÉTRIQUES À SUIVRE

### KPIs E-Commerce

1. **Taux de conversion** : Visiteurs → Acheteurs
2. **Panier moyen** : Montant moyen par commande
3. **Taux d'abandon de panier** : Paniers non convertis
4. **Taux de retour** : Commandes retournées
5. **NPS** : Net Promoter Score

### Dashboard

```python
# apps/ecommerce/views/analytics.py
@api_view(['GET'])
def dashboard_metrics(request):
    today = timezone.now().date()
    
    metrics = {
        'ventes_jour': Commande.objects.filter(
            date_commande__date=today
        ).aggregate(total=Sum('total'))['total'] or 0,
        
        'commandes_jour': Commande.objects.filter(
            date_commande__date=today
        ).count(),
        
        'panier_moyen': Commande.objects.filter(
            date_commande__date=today
        ).aggregate(avg=Avg('total'))['avg'] or 0,
        
        'taux_conversion': calculate_conversion_rate(today),
    }
    
    return Response(metrics)
```

---

## 🎯 CHECKLIST MVP

### Backend
- [ ] Modèles Panier, Commande, Paiement, Livraison
- [ ] API REST complète
- [ ] Intégration Stripe
- [ ] Calcul frais de livraison
- [ ] Emails de confirmation
- [ ] Tests unitaires

### Frontend Mobile
- [ ] Écran Panier
- [ ] Écran Commande
- [ ] Écran Paiement
- [ ] Écran Tracking
- [ ] Notifications push
- [ ] Tests E2E

### Infrastructure
- [ ] Déploiement Railway
- [ ] Variables d'environnement
- [ ] Monitoring Sentry
- [ ] Backup automatique
- [ ] CI/CD GitHub Actions

---

## 🚀 LANCEMENT

```bash
# 1. Vérifier que tout fonctionne
python scripts/diagnostic_et_reparation.py

# 2. Créer des données de test
python manage.py seed_ecommerce_data

# 3. Tester l'API
python scripts/test_ecommerce_api.py

# 4. Déployer
git push railway main

# 5. Vérifier en production
curl https://api.example.com/api/health/
```

---

## 📚 RESSOURCES

- [Documentation complète](./ECOMMERCE_EVOLUTION.md)
- [Stripe Docs](https://stripe.com/docs)
- [Django E-Commerce](https://github.com/django-oscar/django-oscar)
- [React Native Stripe](https://github.com/stripe/stripe-react-native)

---

**Prêt à lancer votre MVP e-commerce ?** 🛒🚀
