# Liste complète des endpoints API

## 📋 Table des matières
- [Authentification](#authentification)
- [Utilisateurs](#utilisateurs)
- [Produits](#produits)
- [Magasins](#magasins)
- [Recommandations](#recommandations)
- [Analyses](#analyses)
- [API Générale](#api-générale)
- [Documentation](#documentation)
- [OAuth Social](#oauth-social)

---

## 🔐 Authentification

### JWT (JSON Web Tokens)
- `POST /api/auth/token/` - Obtenir un token JWT (access + refresh)
- `POST /api/auth/token/refresh/` - Rafraîchir le token d'accès

### Session & Inscription
- `POST /api/auth/register/` - Inscription d'un nouvel utilisateur
- `POST /api/auth/login/` - Connexion (session)
- `POST /api/auth/activate/` - Activer un compte utilisateur
- `GET /activate/<uid>/<token>/` - Page web d'activation (avec UID)
- `GET /activate/<token>` - Page web d'activation (token seul)

### Gestion des sessions
- `GET /api/auth/sessions/` - Lister toutes les sessions actives
- `POST /api/auth/sessions/revoke/` - Révoquer une session
- `POST /api/auth/logout_all/` - Déconnexion de toutes les sessions

### DRF Session Auth
- `GET /api/auth/session/login/` - Page de connexion DRF (browsable API)
- `POST /api/auth/session/login/` - Connexion via session DRF
- `POST /api/auth/session/logout/` - Déconnexion session DRF

---

## 👥 Utilisateurs

### Base CRUD (ViewSet)
- `GET /api/utilisateurs/` - Liste des utilisateurs
- `POST /api/utilisateurs/` - Créer un utilisateur
- `GET /api/utilisateurs/{id}/` - Détails d'un utilisateur
- `PUT /api/utilisateurs/{id}/` - Mettre à jour un utilisateur (complet)
- `PATCH /api/utilisateurs/{id}/` - Mettre à jour un utilisateur (partiel)
- `DELETE /api/utilisateurs/{id}/` - Supprimer un utilisateur

### Actions personnalisées UtilisateurViewSet
- `GET /api/utilisateurs/moi/` - Obtenir les informations de l'utilisateur connecté
- `POST /api/utilisateurs/moi/` - Mettre à jour le profil de l'utilisateur connecté
- `GET /api/utilisateurs/statistiques-fidelite/` - Statistiques de fidélité
- `GET /api/utilisateurs/historique-remises/` - Historique des remises
- `POST /api/utilisateurs/appliquer-remise/` - Appliquer une remise
- `POST /api/utilisateurs/update-location/` - Mettre à jour la localisation
- `POST /api/utilisateurs/renvoyer-activation/` - Renvoyer l'email d'activation
- `GET /api/utilisateurs/utilisateurs-verifies/` - Liste des utilisateurs vérifiés (admin)
- `POST /api/utilisateurs/assign-role/` - Assigner un rôle (admin)
- `POST /api/utilisateurs/revoke-role/` - Révoquer un rôle (admin)
- `GET /api/utilisateurs/mon-profil/` - Profil de l'utilisateur connecté
- `GET /api/utilisateurs/connexions-all/` - Toutes les connexions (admin)
- `POST /api/utilisateurs/twofa-setup/` - Configurer l'authentification à deux facteurs
- `POST /api/utilisateurs/twofa-verify/` - Vérifier le code 2FA
- `POST /api/utilisateurs/twofa-disable/` - Désactiver le 2FA

### Profils
- `GET /api/profils/` - Liste des profils
- `POST /api/profils/` - Créer un profil
- `GET /api/profils/{id}/` - Détails d'un profil
- `PUT /api/profils/{id}/` - Mettre à jour un profil
- `PATCH /api/profils/{id}/` - Mettre à jour partiellement un profil
- `DELETE /api/profils/{id}/` - Supprimer un profil

### Actions personnalisées ProfilViewSet
- `POST /api/profils/{id}/ajouter-categorie-preference/` - Ajouter une catégorie aux préférences [Auth]
- `POST /api/profils/{id}/retirer-categorie-preference/` - Retirer une catégorie des préférences [Auth]

### Abonnements
- `GET /api/abonnements/` - Liste des abonnements
- `POST /api/abonnements/` - Créer un abonnement
- `GET /api/abonnements/{id}/` - Détails d'un abonnement
- `PUT /api/abonnements/{id}/` - Mettre à jour un abonnement
- `PATCH /api/abonnements/{id}/` - Mettre à jour partiellement un abonnement
- `DELETE /api/abonnements/{id}/` - Supprimer un abonnement

---

## 🛍️ Produits

### Produits (ViewSet)
- `GET /api/produits/produits/` - Liste des produits
- `POST /api/produits/produits/` - Créer un produit
- `GET /api/produits/produits/{id}/` - Détails d'un produit
- `PUT /api/produits/produits/{id}/` - Mettre à jour un produit
- `PATCH /api/produits/produits/{id}/` - Mettre à jour partiellement un produit
- `DELETE /api/produits/produits/{id}/` - Supprimer un produit

### Actions personnalisées ProduitViewSet
- `GET /api/produits/produits/populaires/` - Produits populaires
- `GET /api/produits/produits/{id}/prix/` - Prix d'un produit
- `GET /api/produits/produits/{id}/magasins/` - Magasins vendant le produit
- `GET /api/produits/produits/{id}/comparaison/` - Comparaison de prix
- `POST /api/produits/produits/{id}/comparer/` - Comparer un produit avec d'autres
- `GET /api/produits/produits/{id}/comparer/` - Comparaison (alias GET)
- `POST /api/produits/produits/{id}/alerte/` - Créer une alerte prix
- `POST /api/produits/produits/{id}/suggestion/` - Suggérer un prix
- `GET /api/produits/produits/{id}/statistiques/` - Statistiques du produit
- `GET /api/produits/produits/{id}/historique/` - Historique des prix
- `GET /api/produits/produits/{id}/tendances/` - Tendances de prix
- `GET /api/produits/produits/{id}/avis/` - Avis sur le produit
- `POST /api/produits/produits/{id}/avis/` - Ajouter un avis
- `GET /api/produits/produits/{id}/recommandations/` - Recommandations pour le produit
- `GET /api/produits/produits/{id}/similaires/` - Produits similaires
- `GET /api/produits/produits/{id}/offres/` - Offres spéciales
- `GET /api/produits/produits/{id}/caracteristiques/` - Caractéristiques du produit
- `GET /api/produits/produits/{id}/homologation/` - Informations d'homologation
- `GET /api/produits/produits/{id}/statistiques-ventes/` - Statistiques de ventes
- `GET /api/produits/produits/{id}/meilleurs-prix/` - Meilleurs prix
- `GET /api/produits/produits/{id}/evolution-prix/` - Évolution des prix
- `GET /api/produits/produits/{id}/magasins-proches/` - Magasins proches
- `POST /api/produits/produits/{id}/like/` - Liker un produit [Auth]
- `DELETE /api/produits/produits/{id}/like/` - Retirer le like d'un produit [Auth]
- `POST /api/produits/produits/{id}/favoris/` - Ajouter aux favoris [Auth]
- `GET /api/produits/produits/{id}/favoris/` - Vérifier si favori [Auth]
- `GET /api/produits/produits/favoris/` - Liste des favoris de l'utilisateur [Auth]

### Prix (ViewSet)
- `GET /api/produits/prix/` - Liste des prix
- `POST /api/produits/prix/` - Créer un prix
- `GET /api/produits/prix/{id}/` - Détails d'un prix
- `PUT /api/produits/prix/{id}/` - Mettre à jour un prix
- `PATCH /api/produits/prix/{id}/` - Mettre à jour partiellement un prix
- `DELETE /api/produits/prix/{id}/` - Supprimer un prix

### Alertes Prix (ViewSet)
- `GET /api/produits/alertes-prix/` - Liste des alertes prix
- `POST /api/produits/alertes-prix/` - Créer une alerte prix
- `GET /api/produits/alertes-prix/{id}/` - Détails d'une alerte prix
- `PUT /api/produits/alertes-prix/{id}/` - Mettre à jour une alerte prix
- `PATCH /api/produits/alertes-prix/{id}/` - Mettre à jour partiellement une alerte prix
- `DELETE /api/produits/alertes-prix/{id}/` - Supprimer une alerte prix

### Suggestions Prix (ViewSet)
- `GET /api/produits/suggestions-prix/` - Liste des suggestions prix
- `POST /api/produits/suggestions-prix/` - Créer une suggestion prix
- `GET /api/produits/suggestions-prix/{id}/` - Détails d'une suggestion prix
- `PUT /api/produits/suggestions-prix/{id}/` - Mettre à jour une suggestion prix
- `PATCH /api/produits/suggestions-prix/{id}/` - Mettre à jour partiellement une suggestion prix
- `DELETE /api/produits/suggestions-prix/{id}/` - Supprimer une suggestion prix

### Comparaisons Prix (ViewSet)
- `GET /api/produits/comparaisons-prix/` - Liste des comparaisons prix
- `POST /api/produits/comparaisons-prix/` - Créer une comparaison prix
- `GET /api/produits/comparaisons-prix/{id}/` - Détails d'une comparaison prix
- `PUT /api/produits/comparaisons-prix/{id}/` - Mettre à jour une comparaison prix
- `PATCH /api/produits/comparaisons-prix/{id}/` - Mettre à jour partiellement une comparaison prix
- `DELETE /api/produits/comparaisons-prix/{id}/` - Supprimer une comparaison prix

### Statistiques Prix (ViewSet)
- `GET /api/produits/statistiques-prix/` - Liste des statistiques prix
- `GET /api/produits/statistiques-prix/{id}/` - Détails d'une statistique prix

### Homologations Stats (ViewSet)
- `GET /api/produits/homologations-stats/` - Liste des statistiques d'homologation
- `GET /api/produits/homologations-stats/{id}/` - Détails d'une statistique d'homologation

### Offres (ViewSet)
- `GET /api/produits/offres/` - Liste des offres
- `POST /api/produits/offres/` - Créer une offre
- `GET /api/produits/offres/{id}/` - Détails d'une offre
- `PUT /api/produits/offres/{id}/` - Mettre à jour une offre
- `PATCH /api/produits/offres/{id}/` - Mettre à jour partiellement une offre
- `DELETE /api/produits/offres/{id}/` - Supprimer une offre

### Catégories (ViewSet)
- `GET /api/produits/categories/` - Liste des catégories
- `POST /api/produits/categories/` - Créer une catégorie
- `GET /api/produits/categories/{id}/` - Détails d'une catégorie
- `PUT /api/produits/categories/{id}/` - Mettre à jour une catégorie
- `PATCH /api/produits/categories/{id}/` - Mettre à jour partiellement une catégorie
- `DELETE /api/produits/categories/{id}/` - Supprimer une catégorie

### Marques (ViewSet)
- `GET /api/produits/marques/` - Liste des marques
- `POST /api/produits/marques/` - Créer une marque
- `GET /api/produits/marques/{id}/` - Détails d'une marque
- `PUT /api/produits/marques/{id}/` - Mettre à jour une marque
- `PATCH /api/produits/marques/{id}/` - Mettre à jour partiellement une marque
- `DELETE /api/produits/marques/{id}/` - Supprimer une marque

### Unités de mesure (ViewSet - ReadOnly)
- `GET /api/produits/unites-mesure/` - Liste des unités de mesure
- `GET /api/produits/unites-mesure/{id}/` - Détails d'une unité de mesure

### Avis Produit (ViewSet)
- `GET /api/produits/avis/` - Liste des avis
- `POST /api/produits/avis/` - Créer un avis
- `GET /api/produits/avis/{id}/` - Détails d'un avis
- `PUT /api/produits/avis/{id}/` - Mettre à jour un avis
- `PATCH /api/produits/avis/{id}/` - Mettre à jour partiellement un avis
- `DELETE /api/produits/avis/{id}/` - Supprimer un avis

### Caractéristiques Produit (ViewSet)
- `GET /api/produits/caracteristiques/` - Liste des caractéristiques
- `POST /api/produits/caracteristiques/` - Créer une caractéristique
- `GET /api/produits/caracteristiques/{id}/` - Détails d'une caractéristique
- `PUT /api/produits/caracteristiques/{id}/` - Mettre à jour une caractéristique
- `PATCH /api/produits/caracteristiques/{id}/` - Mettre à jour partiellement une caractéristique
- `DELETE /api/produits/caracteristiques/{id}/` - Supprimer une caractéristique

### Statistiques Produits (ViewSet)
- `GET /api/produits/statistiques-produits/` - Liste des statistiques produits
- `GET /api/produits/statistiques-produits/{id}/` - Détails d'une statistique produit

### Alias et routes alternatives
- `GET /api/produits/populaires/` - Produits populaires (alias)
- `GET /api/produits/categories/` - Catégories (alias)
- `GET /api/produits/stats/prix/` - Statistiques prix (alias)
- `GET /api/produits/stats/homologations/` - Statistiques homologations (alias)
- `GET /api/categories/` - Catégories (alias global)
- `GET /api/prix/` - Prix (alias global)

---

## 🏪 Magasins

### Régions (ViewSet)
- `GET /api/magasins/regions/` - Liste des régions
- `POST /api/magasins/regions/` - Créer une région
- `GET /api/magasins/regions/{id}/` - Détails d'une région
- `PUT /api/magasins/regions/{id}/` - Mettre à jour une région
- `PATCH /api/magasins/regions/{id}/` - Mettre à jour partiellement une région
- `DELETE /api/magasins/regions/{id}/` - Supprimer une région

### Villes (ViewSet)
- `GET /api/magasins/villes/` - Liste des villes
- `POST /api/magasins/villes/` - Créer une ville
- `GET /api/magasins/villes/{id}/` - Détails d'une ville
- `PUT /api/magasins/villes/{id}/` - Mettre à jour une ville
- `PATCH /api/magasins/villes/{id}/` - Mettre à jour partiellement une ville
- `DELETE /api/magasins/villes/{id}/` - Supprimer une ville

### Magasins (ViewSet)
- `GET /api/magasins/magasins/` - Liste des magasins
- `POST /api/magasins/magasins/` - Créer un magasin
- `GET /api/magasins/magasins/{id}/` - Détails d'un magasin
- `PUT /api/magasins/magasins/{id}/` - Mettre à jour un magasin
- `PATCH /api/magasins/magasins/{id}/` - Mettre à jour partiellement un magasin
- `DELETE /api/magasins/magasins/{id}/` - Supprimer un magasin

### Actions personnalisées MagasinViewSet
- `GET /api/magasins/magasins/proximite/` - Magasins à proximité

### Routes alternatives
- `GET /api/magasins/regions/` - Liste des régions (route directe)
- `GET /api/magasins/regions/{id}/` - Détails d'une région (route directe)
- `GET /api/magasins/villes/` - Liste des villes (route directe)
- `GET /api/magasins/villes/{id}/` - Détails d'une ville (route directe)
- `GET /api/magasins/magasins/` - Liste des magasins (route directe)
- `GET /api/magasins/magasins/{id}/` - Détails d'un magasin (route directe)
- `GET /api/magasin/` - Magasins (alias)
- `GET /api/stores/` - Magasins (alias anglais)

---

## 🎯 Recommandations

### Recommandations (ViewSet)
- `GET /api/recommandations/recommandations/` - Liste des recommandations
- `POST /api/recommandations/recommandations/` - Créer une recommandation
- `GET /api/recommandations/recommandations/{id}/` - Détails d'une recommandation
- `PUT /api/recommandations/recommandations/{id}/` - Mettre à jour une recommandation
- `PATCH /api/recommandations/recommandations/{id}/` - Mettre à jour partiellement une recommandation
- `DELETE /api/recommandations/recommandations/{id}/` - Supprimer une recommandation

### Actions personnalisées RecommandationViewSet
- `POST /api/recommandations/recommandations/{id}/like/` - Liker une recommandation [Auth]
- `POST /api/recommandations/recommandations/{id}/dislike/` - Disliker une recommandation [Auth]
- `GET /api/recommandations/recommandations/pour_moi/` - Recommandations pour l'utilisateur connecté [Auth]
- `GET /api/recommandations/recommandations/populaires/` - Recommandations populaires
- `POST /api/recommandations/recommandations/pour_produit/` - Recommandations pour un produit
- `GET /api/recommandations/recommandations/tendances/` - Tendances
- `POST /api/recommandations/recommandations/feedback/` - Envoyer un feedback [Auth]
- `POST /api/recommandations/recommandations/{id}/feedback/` - Feedback sur une recommandation [Auth]

### Historique Recommandations (ViewSet)
- `GET /api/recommandations/historique/` - Liste de l'historique
- `POST /api/recommandations/historique/` - Créer un historique
- `GET /api/recommandations/historique/{id}/` - Détails d'un historique
- `PUT /api/recommandations/historique/{id}/` - Mettre à jour un historique
- `PATCH /api/recommandations/historique/{id}/` - Mettre à jour partiellement un historique
- `DELETE /api/recommandations/historique/{id}/` - Supprimer un historique

### Feedback Recommandations (ViewSet)
- `GET /api/recommandations/feedback/` - Liste des feedbacks
- `POST /api/recommandations/feedback/` - Créer un feedback
- `GET /api/recommandations/feedback/{id}/` - Détails d'un feedback
- `PUT /api/recommandations/feedback/{id}/` - Mettre à jour un feedback
- `PATCH /api/recommandations/feedback/{id}/` - Mettre à jour partiellement un feedback
- `DELETE /api/recommandations/feedback/{id}/` - Supprimer un feedback

### Modèles ML (ViewSet)
- `GET /api/recommandations/modeles-ml/` - Liste des modèles ML
- `POST /api/recommandations/modeles-ml/` - Créer un modèle ML
- `GET /api/recommandations/modeles-ml/{id}/` - Détails d'un modèle ML
- `PUT /api/recommandations/modeles-ml/{id}/` - Mettre à jour un modèle ML
- `PATCH /api/recommandations/modeles-ml/{id}/` - Mettre à jour partiellement un modèle ML
- `DELETE /api/recommandations/modeles-ml/{id}/` - Supprimer un modèle ML

### Routes fonctionnelles
- `GET /api/recommandations/statut-modeles/` - Statut des modèles ML
- `GET /api/recommandations/pour_moi/` - Recommandations pour l'utilisateur connecté
- `GET /api/recommandations/populaires/` - Recommandations populaires
- `GET /api/recommandations/pour_produit/` - Recommandations pour un produit

### Routes legacy et alias
- `GET /api/recommandations/recommandations/utilisateur/` - Recommandations utilisateur (legacy)
- `GET /api/recommandations/recommandations/produit/{produit_id}/` - Recommandations produit (legacy)
- `GET /api/recommandations/reco/pour-vous/` - Recommandations pour vous (alias)
- `GET /api/recommandations/reco/tendances/` - Tendances (alias)
- `GET /api/reco/pour-vous/` - Recommandations pour vous (alias global)
- `GET /api/reco/tendances/` - Tendances (alias global)
- `GET /api/reco/produits/{produit_id}/similaires/` - Produits similaires (alias global)

---

## 📊 Analyses

### Analyses Prix (ViewSet)
- `GET /api/analyses/api/analyses/` - Liste des analyses
- `POST /api/analyses/api/analyses/` - Créer une analyse
- `GET /api/analyses/api/analyses/{id}/` - Détails d'une analyse
- `PUT /api/analyses/api/analyses/{id}/` - Mettre à jour une analyse
- `PATCH /api/analyses/api/analyses/{id}/` - Mettre à jour partiellement une analyse
- `DELETE /api/analyses/api/analyses/{id}/` - Supprimer une analyse

### Actions personnalisées AnalysePrixViewSet
- `POST /api/analyses/api/analyses/{id}/executer/` - Exécuter une analyse [Auth]
- `GET /api/analyses/api/analyses/resultats/` - Résultats des analyses
- `GET /api/analyses/api/analyses/statistiques/` - Statistiques des analyses
- `GET /api/analyses/api/analyses/{id}/rapport/` - Rapport d'une analyse

### Rapports Analyse (ViewSet)
- `GET /api/analyses/api/rapports/` - Liste des rapports
- `POST /api/analyses/api/rapports/` - Créer un rapport
- `GET /api/analyses/api/rapports/{id}/` - Détails d'un rapport
- `PUT /api/analyses/api/rapports/{id}/` - Mettre à jour un rapport
- `PATCH /api/analyses/api/rapports/{id}/` - Mettre à jour partiellement un rapport
- `DELETE /api/analyses/api/rapports/{id}/` - Supprimer un rapport

### Indicateurs Performance (ViewSet)
- `GET /api/analyses/api/indicateurs/` - Liste des indicateurs
- `POST /api/analyses/api/indicateurs/` - Créer un indicateur
- `GET /api/analyses/api/indicateurs/{id}/` - Détails d'un indicateur
- `PUT /api/analyses/api/indicateurs/{id}/` - Mettre à jour un indicateur
- `PATCH /api/analyses/api/indicateurs/{id}/` - Mettre à jour partiellement un indicateur
- `DELETE /api/analyses/api/indicateurs/{id}/` - Supprimer un indicateur

### Résultats Analyse (ViewSet)
- `GET /api/analyses/api/resultats/` - Liste des résultats
- `POST /api/analyses/api/resultats/` - Créer un résultat
- `GET /api/analyses/api/resultats/{id}/` - Détails d'un résultat
- `PUT /api/analyses/api/resultats/{id}/` - Mettre à jour un résultat
- `PATCH /api/analyses/api/resultats/{id}/` - Mettre à jour partiellement un résultat
- `DELETE /api/analyses/api/resultats/{id}/` - Supprimer un résultat

### Agrégats Prix (ViewSet)
- `GET /api/analyses/api/aggregats/` - Liste des agrégats
- `POST /api/analyses/api/aggregats/` - Créer un agrégat
- `GET /api/analyses/api/aggregats/{id}/` - Détails d'un agrégat
- `PUT /api/analyses/api/aggregats/{id}/` - Mettre à jour un agrégat
- `PATCH /api/analyses/api/aggregats/{id}/` - Mettre à jour partiellement un agrégat
- `DELETE /api/analyses/api/aggregats/{id}/` - Supprimer un agrégat

### Analyses Optimisées (ViewSet)
- `GET /api/analyses/api/analyses-optimisees/` - Liste des analyses optimisées
- `POST /api/analyses/api/analyses-optimisees/` - Créer une analyse optimisée
- `GET /api/analyses/api/analyses-optimisees/{id}/` - Détails d'une analyse optimisée
- `PUT /api/analyses/api/analyses-optimisees/{id}/` - Mettre à jour une analyse optimisée
- `PATCH /api/analyses/api/analyses-optimisees/{id}/` - Mettre à jour partiellement une analyse optimisée
- `DELETE /api/analyses/api/analyses-optimisees/{id}/` - Supprimer une analyse optimisée

### Graph Analytics (optionnel)
- `GET /api/analyses/api/graph/snapshots/` - Liste des snapshots de graphe
- `POST /api/analyses/api/graph/snapshots/` - Créer un snapshot de graphe
- `GET /api/analyses/api/graph/snapshots/{id}/` - Détails d'un snapshot
- `GET /api/analyses/api/graph/nodes/` - Liste des nœuds du graphe
- `GET /api/analyses/api/graph/nodes/{id}/` - Détails d'un nœud
- `GET /api/analyses/api/graph/edges/` - Liste des arêtes du graphe
- `GET /api/analyses/api/graph/edges/{id}/` - Détails d'une arête
- `GET /api/analyses/api/graph/latest/` - Dernier graphe

### Statistiques
- `GET /api/analyses/api/stats/prix/overview` - Vue d'ensemble des statistiques de prix
- `GET /api/analyses/api/stats/magasins_plus_actifs` - Magasins les plus actifs
- `GET /api/analyses/api/stats/produits_plus_recherches` - Produits les plus recherchés
- `GET /api/analyses/api/stats/tendances` - Tendances des prix

---

## 🔍 API Générale

### Health & Test
- `GET /api/health/` - Vérifier l'état de l'API
- `GET /api/test-connection/` - Tester la connexion à la base de données

### Recherche
- `GET /api/search/produits/` - Rechercher des produits
- `GET /api/search/autocomplete/` - Autocomplétion pour la recherche de produits

### Comparaison & Statistiques
- `POST /api/compare/` - Comparer des offres
- `GET /api/nearby/prix/` - Prix à proximité (géolocalisation)
- `GET /api/stats/prix/` - Statistiques générales des prix
- `GET /api/homologations-stats/` - Statistiques d'homologation
- `GET /api/stats/homologations/` - Statistiques d'homologation (alias)

---

## 📚 Documentation

### OpenAPI / Swagger
- `GET /api/schema/` - Schéma OpenAPI (JSON/YAML)
- `GET /api/docs/` - Interface Swagger UI (documentation interactive)
- `GET /` - Redirige vers Swagger UI (en DEBUG) ou vue JSON (en production)

---

## 🔗 OAuth Social

### OAuth Providers (social-auth-app-django)
- `GET /oauth/login/google-oauth2/` - Connexion via Google
- `GET /oauth/login/facebook/` - Connexion via Facebook
- `GET /oauth/login/apple-id/` - Connexion via Apple (si configuré)
- `GET /oauth/complete/{provider}/` - Callback OAuth après authentification
- `GET /oauth/disconnect/{provider}/` - Déconnexion d'un provider OAuth
- `GET /oauth/error/` - Page d'erreur OAuth

---

## 🎛️ Administration

### Django Admin
- `GET /admin/` - Interface d'administration Django (configurable via `DJANGO_ADMIN_URL`)

---

## 📝 Notes importantes

### Authentification
- La plupart des endpoints nécessitent une authentification (JWT ou Session)
- Les endpoints publics sont généralement en lecture seule (`GET`)
- Les endpoints nécessitant une authentification sont marqués avec `[Auth]` dans la documentation Swagger

### Méthodes HTTP
- `GET` - Lecture seule (list, retrieve)
- `POST` - Création (create, actions personnalisées)
- `PUT` - Mise à jour complète
- `PATCH` - Mise à jour partielle
- `DELETE` - Suppression

### Pagination
- La plupart des listes sont paginées (20 résultats par page par défaut)
- Utiliser les paramètres `?page=2` pour naviguer

### Filtrage & Recherche
- Utiliser les paramètres de query pour filtrer les résultats
- Exemple: `/api/produits/produits/?search=chocolat&categorie=1`

### Alias et Routes Legacy
- Certains endpoints ont des alias pour la compatibilité avec le frontend
- Les routes legacy sont maintenues pour la rétrocompatibilité mais peuvent être dépréciées

---

## 🔢 Statistiques des Endpoints

**Total des endpoints : ~200+**

- Authentification : 9 endpoints
- Utilisateurs : 30+ endpoints
- Produits : 80+ endpoints
- Magasins : 20+ endpoints
- Recommandations : 25+ endpoints
- Analyses : 30+ endpoints
- API Générale : 8 endpoints
- Documentation : 3 endpoints
- OAuth : 5+ endpoints
- Administration : 1 endpoint

---

*Dernière mise à jour : 2025-11-26*