# TODO - Optimisations Comparateur de Prix

## 🚀 Priorité Haute

### 1. Cache pour enrichissement des prix
- [ ] Créer `apps/produits/services/price_enrichment.py`
- [ ] Implémenter `PriceEnrichmentService` avec méthodes:
  - [ ] `get_enriched_price(produit_id, magasin_id=None)`
  - [ ] `get_price_stats(produit_id)`
  - [ ] `invalidate_cache(produit_id=None, magasin_id=None)`
- [ ] Intégrer dans `PrixViewSet` et `ProduitViewSet`
- [ ] Ajouter métriques de cache (hit/miss)
- [ ] Tests unitaires pour le service

### 2. Endpoint batch pour prix
- [ ] Créer action `batch` dans `PrixViewSet`
- [ ] Créer `BatchPrixSerializer` dans `serializers.py`
- [ ] Implémenter validation (max 100 items)
- [ ] Optimiser requête avec `select_related`/`prefetch_related`
- [ ] Ajouter tests d'intégration
- [ ] Documenter l'API dans Swagger

## 🎨 Priorité Moyenne

### 3. Améliorations pages
- [ ] **Profil**:
  - [ ] Statistiques détaillées
  - [ ] Historique recherches
  - [ ] Préférences utilisateur
- [ ] **Explore**:
  - [ ] Filtres avancés
  - [ ] Vue carte/liste/grille
  - [ ] Tri multi-critères
- [ ] **Auth**:
  - [ ] Messages d'erreur améliorés
  - [ ] Indicateur force mot de passe
  - [ ] Animations de chargement

### 4. Animations et transitions
- [ ] Transitions de page
- [ ] Skeleton screens
- [ ] Micro-interactions boutons
- [ ] Animations de liste
- [ ] Transitions modales

## ✅ Priorité Basse

### 5. Tests responsive
- [ ] Tests mobile (< 768px)
- [ ] Tests tablette (768-1024px)
- [ ] Tests desktop (> 1024px)
- [ ] Tests cross-browser
- [ ] Tests appareils réels

---

**Dernière mise à jour** : 2025-11-14

