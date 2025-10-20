import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
# Importer xgboost/lightgbm de façon optionnelle et paresseuse dans les méthodes
import joblib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
from django.conf import settings
from django.core.cache import cache
from django.db.models import Count

logger = logging.getLogger(__name__)

class ModeleRecommandationContenu:
    """Modèle de recommandation basé sur le contenu des produits"""
    
    def __init__(self, n_composantes: int = 100, use_embeddings: bool = False, embedding_model_name: str = 'paraphrase-multilingual-MiniLM-L12-v2'):
        self.n_composantes = n_composantes
        # Certaines versions de scikit-learn n'acceptent que 'english'.
        # On évite l'erreur en mettant None (sans stopwords) pour compatibilité.
        self.vectoriseur = TfidfVectorizer(
            max_features=5000,
            stop_words=None,
            ngram_range=(1, 2)
        )
        self.svd = TruncatedSVD(n_components=n_composantes, random_state=42)
        self.matrice_similarite = None
        self.produits_data = None
        self.est_entraine = False
        # Embeddings optionnels
        self.use_embeddings = use_embeddings
        self.embedding_model_name = embedding_model_name
        self._embedder = None
        
    def preparer_donnees(self, produits_data: List[Dict]) -> pd.DataFrame:
        """Prépare les données pour l'entraînement"""
        df = pd.DataFrame(produits_data)
        
        # Si le DataFrame est vide, retourner un DF avec la bonne colonne vide
        if df.empty:
            df = pd.DataFrame({'caracteristiques': []})
            return df
        
        # Garantir des Series pour chaque champ (évite .fillna sur str)
        def col_or_empty_series(name: str) -> pd.Series:
            if name in df.columns:
                return df[name].astype(str).fillna('')
            # Créer une Series vide/valeurs vides de même longueur que df
            return pd.Series([''] * len(df))
        
        nom_s = col_or_empty_series('nom')
        categorie_s = col_or_empty_series('categorie')
        marque_s = col_or_empty_series('marque')
        description_s = col_or_empty_series('description')
        
        # Création d'une colonne de caractéristiques combinées
        df['caracteristiques'] = (nom_s + ' ' + categorie_s + ' ' + marque_s + ' ' + description_s).fillna('')
        
        return df
    
    def entrainer(self, produits_data: List[Dict]):
        """Entraîne le modèle de recommandation"""
        try:
            logger.info("Début de l'entraînement du modèle de recommandation par contenu")
            
            self.produits_data = produits_data
            df_produits = self.preparer_donnees(produits_data)
            if df_produits.empty or 'caracteristiques' not in df_produits.columns:
                logger.warning("Aucune donnée produit exploitable pour l'entraînement du modèle de contenu")
                self.est_entraine = False
                return
            
            # Embeddings (si activés), sinon TF-IDF + SVD
            if self.use_embeddings:
                try:
                    from sentence_transformers import SentenceTransformer  # type: ignore
                    if self._embedder is None:
                        self._embedder = SentenceTransformer(self.embedding_model_name)
                    matrice_reduite = self._embedder.encode(df_produits['caracteristiques'].tolist(), show_progress_bar=False)
                except Exception as e:
                    logger.warning(f"Embeddings indisponibles, fallback TF-IDF. Raison: {e}")
                    self.use_embeddings = False
                    matrice_tfidf = self.vectoriseur.fit_transform(df_produits['caracteristiques'])
                    matrice_reduite = self.svd.fit_transform(matrice_tfidf)
            else:
                matrice_tfidf = self.vectoriseur.fit_transform(df_produits['caracteristiques'])
                matrice_reduite = self.svd.fit_transform(matrice_tfidf)
            
            # Calcul de similarité cosinus
            self.matrice_similarite = cosine_similarity(matrice_reduite)
            self.est_entraine = True
            
            logger.info("Entraînement du modèle de recommandation terminé")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement: {e}")
            raise
    
    def recommander(self, produit_id: int, n_recommandations: int = 10) -> List[Dict]:
        """Génère des recommandations pour un produit"""
        if not self.est_entraine or self.produits_data is None:
            return []
        
        try:
            # Trouver l'index du produit
            produit_idx = None
            for idx, produit in enumerate(self.produits_data):
                if produit['id'] == produit_id:
                    produit_idx = idx
                    break
            
            if produit_idx is None:
                return []
            
            # Obtenir les similarités
            similarites = self.matrice_similarite[produit_idx]
            
            # Exclure le produit lui-même et trier
            indices_similaires = np.argsort(similarites)[::-1]
            indices_similaires = [idx for idx in indices_similaires if idx != produit_idx][:n_recommandations]
            
            recommandations = []
            for idx in indices_similaires:
                produit = self.produits_data[idx]
                score_similarite = similarites[idx]
                recommandations.append({
                    'produit': produit,
                    'score_similarite': float(score_similarite),
                    'algorithme': 'contenu'
                })
            
            return recommandations
            
        except Exception as e:
            logger.error(f"Erreur lors de la recommandation: {e}")
            return []
    
    def sauvegarder(self, chemin: str):
        """Sauvegarde le modèle entraîné"""
        if not self.est_entraine:
            raise ValueError("Modèle non entraîné")
        
        modele_data = {
            'vectoriseur': self.vectoriseur,
            'svd': self.svd,
            'matrice_similarite': self.matrice_similarite,
            'produits_data': self.produits_data
        }
        
        joblib.dump(modele_data, chemin)
        logger.info(f"Modèle sauvegardé: {chemin}")
    
    def charger(self, chemin: str):
        """Charge un modèle pré-entraîné"""
        if os.path.exists(chemin):
            modele_data = joblib.load(chemin)
            self.vectoriseur = modele_data['vectoriseur']
            self.svd = modele_data['svd']
            self.matrice_similarite = modele_data['matrice_similarite']
            self.produits_data = modele_data['produits_data']
            self.est_entraine = True
            logger.info(f"Modèle chargé: {chemin}")

class ModelePredictionPrix:
    """Modèle de prédiction de prix des produits"""
    
    def __init__(self):
        self.modeles = {}
        self.scalers = {}
        self.encodeurs = {}
        self.est_entraine = False
        self.meilleur_modele = None
        
    def preparer_donnees(self, donnees_prix: List[Dict]) -> tuple:
        """Prépare les données pour l'entraînement"""
        df = pd.DataFrame(donnees_prix)
        
        # Nettoyage / conversions numériques (prix peut être Decimal)
        if 'prix' in df.columns:
            df['prix'] = pd.to_numeric(df['prix'], errors='coerce')
        df = df.dropna(subset=['prix'])
        df = df[df['prix'].astype(float) > 0]
        
        # Feature engineering
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
            df['annee'] = df['date'].dt.year
            df['mois'] = df['date'].dt.month
            df['jour_semaine'] = df['date'].dt.dayofweek
        
        # Encodage des variables catégorielles
        colonnes_categorielles = ['categorie', 'sous_categorie', 'marque', 'magasin', 'ville', 'type_magasin', 'zone', 'type_prix', 'unite_mesure']
        
        for col in colonnes_categorielles:
            if col in df.columns:
                if col not in self.encodeurs:
                    self.encodeurs[col] = LabelEncoder()
                    df[col] = self.encodeurs[col].fit_transform(df[col].fillna('Inconnu'))
                else:
                    df[col] = self.encodeurs[col].transform(df[col].fillna('Inconnu'))
        
        # Sélection des caractéristiques
        # Conversions numériques additionnelles
        if 'quantite_unite' in df.columns:
            df['quantite_unite'] = pd.to_numeric(df['quantite_unite'], errors='coerce').fillna(0.0)
        numeriques_potentielles = ['annee', 'mois', 'jour_semaine', 'quantite_unite']
        caracteristiques = [
            col for col in (
                ['categorie', 'sous_categorie', 'marque', 'magasin', 'ville', 'type_magasin', 'zone', 'type_prix', 'unite_mesure']
                + numeriques_potentielles
            ) if col in df.columns
        ]
        
        X = df[caracteristiques]
        # Transformation log1p pour stabiliser
        y = np.log1p(df['prix'].astype(float))
        
        return X, y, caracteristiques
    
    def entrainer(self, donnees_prix: List[Dict]):
        """Entraîne le modèle de prédiction de prix"""
        try:
            logger.info("Début de l'entraînement du modèle de prédiction de prix")
            
            X, y, caracteristiques = self.preparer_donnees(donnees_prix)
            self.caracteristiques = caracteristiques
            
            # Normalisation
            self.scalers['X'] = StandardScaler()
            X_scaled = self.scalers['X'].fit_transform(X)
            
            # Division train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Modèles à tester (xgboost/lightgbm optionnels)
            self.modeles = {
                'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
            }
            # xgboost (optionnel)
            try:
                import xgboost as xgb  # type: ignore
                self.modeles['xgboost'] = xgb.XGBRegressor(n_estimators=100, random_state=42)
            except Exception:
                logger.info("xgboost non installé: le modèle XGBRegressor sera ignoré")
            # lightgbm (optionnel)
            try:
                import lightgbm as lgb  # type: ignore
                self.modeles['lightgbm'] = lgb.LGBMRegressor(n_estimators=100, random_state=42)
            except Exception:
                logger.info("lightgbm non installé: le modèle LGBMRegressor sera ignoré")
            
            # Entraînement et sélection du meilleur modèle
            meilleur_score = float('inf')
            for nom, modele in self.modeles.items():
                modele.fit(X_train, y_train)
                y_pred = modele.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred)
                
                if mae < meilleur_score:
                    meilleur_score = mae
                    self.meilleur_modele = modele
            
            self.est_entraine = True
            logger.info(f"Entraînement terminé - Meilleur MAE: {meilleur_score:.2f}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'entraînement prix: {e}")
            raise
    
    def predicire_prix(self, caracteristiques_produit: Dict) -> float:
        """Prédit le prix d'un produit"""
        if not self.est_entraine:
            raise ValueError("Modèle non entraîné")
        
        # Préparation des caractéristiques
        df = pd.DataFrame([caracteristiques_produit])
        
        # Encodage
        for col, encodeur in self.encodeurs.items():
            if col in df.columns:
                df[col] = encodeur.transform(df[col].fillna('Inconnu'))
        
        # Sélection des features
        X = df[self.caracteristiques]
        X_scaled = self.scalers['X'].transform(X)
        y_log = float(self.meilleur_modele.predict(X_scaled)[0])
        return float(np.expm1(y_log))

class GestionnaireRecommandations:
    """Gestionnaire principal des recommandations"""
    
    def __init__(self):
        self.modele_contenu = ModeleRecommandationContenu()
        self.modele_prix = ModelePredictionPrix()
        self.est_initialise = False
    
    def initialiser_modeles(self):
        """Initialise les modèles avec les données de la base"""
        try:
            from .models import ModeleML
            from apps.produits.models import Produit
            from apps.produits.models import Prix
            
            # Charger les produits
            # Ne demander que des champs existants sur Produit
            produits_qs = Produit.objects.select_related('categorie', 'marque').values(
                'id', 'nom',
                'categorie__nom',
                'marque__nom',
                'description',
            )
            # Si votre modèle Produit expose une sous-catégorie via Homologation ou autre, adapter ici.
            # On mappe vers les clés attendues par le modèle contenu
            produits = []
            for r in produits_qs:
                produits.append({
                    'id': r['id'],
                    'nom': r.get('nom') or '',
                    'categorie': r.get('categorie__nom') or '',
                    'marque': r.get('marque__nom') or '',
                    'description': r.get('description') or '',
                })
            
            # Charger les données de prix pour l'entraînement depuis Prix (champs existants)
            prix_qs = Prix.objects.select_related(
                'produit__categorie', 'produit__marque', 'produit__unite_mesure', 'magasin__ville'
            ).values(
                'produit__categorie__nom',
                'produit__marque__nom',
                'produit__unite_mesure__symbole',
                'produit__quantite_unite',
                'produit__poids',
                'produit__volume',
                'magasin__nom',
                'magasin__ville__nom',
                'magasin__type',
                'magasin__zone',
                'type_prix',
                'prix_actuel',
                'date_modification'
            )[:10000]
            # Remapper pour correspondre aux clés attendues par le pipeline ML
            prix_data = [
                {
                    'categorie': r.get('produit__categorie__nom'),
                    'sous_categorie': '',
                    'marque': r.get('produit__marque__nom'),
                    'magasin': r.get('magasin__nom'),
                    'ville': r.get('magasin__ville__nom'),
                    'type_magasin': r.get('magasin__type'),
                    'zone': r.get('magasin__zone'),
                    'type_prix': r.get('type_prix'),
                    'unite_mesure': r.get('produit__unite_mesure__symbole'),
                    'quantite_unite': r.get('produit__quantite_unite'),
                    'poids': r.get('produit__poids'),
                    'volume': r.get('produit__volume'),
                    'prix': r.get('prix_actuel'),
                    'date': r.get('date_modification'),
                }
                for r in prix_qs
            ]
            
            # Entraînement des modèles
            self.modele_contenu.entrainer(produits)
            if prix_data:
                self.modele_prix.entrainer(prix_data)
            
            self.est_initialise = True
            logger.info("Gestionnaire de recommandations initialisé")
            
        except Exception as e:
            logger.error(f"Erreur initialisation gestionnaire: {e}")
    
    def get_recommandations_produit(self, produit_id: int, n_recommandations: int = 10) -> List[Dict]:
        """Recommandations basées sur un produit"""
        cache_key = f'recommandations_produit_{produit_id}_{n_recommandations}'
        recommandations = cache.get(cache_key)
        
        if not recommandations:
            recommandations = self.modele_contenu.recommander(produit_id, n_recommandations)
            cache.set(cache_key, recommandations, timeout=3600)  # Cache 1h
        
        return recommandations
    
    def get_recommandations_utilisateur(self, utilisateur_id: int, n_recommandations: int = 10) -> List[Dict]:
        """Recommandations personnalisées pour un utilisateur"""
        try:
            from apps.utilisateurs.models import HistoriqueUtilisateur
            from apps.produits.models import Produit
            
            # Récupérer l'historique utilisateur
            historique = HistoriqueUtilisateur.objects.filter(
                utilisateur_id=utilisateur_id
            ).order_by('-date')[:5]
            
            if historique.exists():
                # Recommander basé sur le dernier produit consulté
                dernier_produit = historique.first().produit_id
                return self.get_recommandations_produit(dernier_produit, n_recommandations)
            else:
                # Fallback: produits populaires
                return self.get_recommandations_populaires(n_recommandations)
                
        except Exception as e:
            logger.error(f"Erreur recommandations utilisateur: {e}")
            return self.get_recommandations_populaires(n_recommandations)
    
    def get_recommandations_populaires(self, n_recommandations: int = 10) -> List[Dict]:
        """Produits les plus populaires"""
        from apps.produits.models import Produit
        
        produits_populaires = Produit.objects.annotate(n=Count('prix')).order_by('-n')[:n_recommandations]
        return [{
            'produit': {
                'id': p.id,
                'nom': p.nom,
            },
            'score_similarite': 1.0,
            'algorithme': 'populaire'
        } for p in produits_populaires]
    
    def predicire_prix_optimal(self, caracteristiques_produit: Dict) -> Dict:
        """Prédit le prix optimal pour un produit"""
        try:
            if self.modele_prix.est_entraine:
                prix_prediction = self.modele_prix.predicire_prix(caracteristiques_produit)
                return {
                    'prix_prediction': prix_prediction,
                    'confiance': 0.8  # Valeur fictive pour l'exemple
                }
            else:
                return {'erreur': 'Modèle de prix non entraîné'}
        except Exception as e:
            logger.error(f"Erreur prédiction prix: {e}")
            return {'erreur': str(e)}