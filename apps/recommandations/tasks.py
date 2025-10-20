from celery import shared_task
import logging
from django.core.cache import cache
from django.conf import settings
from pathlib import Path
from .modeles_ml import GestionnaireRecommandations
from .models import ModeleML

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def entrainer_modele_recommandation(self, modele_type='contenu'):
    """Tâche Celery pour l'entraînement asynchrone des modèles"""
    try:
        logger.info(f"Début de l'entraînement du modèle: {modele_type}")
        
        gestionnaire = GestionnaireRecommandations()
        
        if modele_type == 'contenu':
            # Entraînement du modèle de contenu
            from apps.produits.models import Produit
            produits_qs = Produit.objects.select_related('categorie', 'marque').values(
                'id', 'nom', 'categorie__nom', 'marque__nom', 'description'
            )
            produits = [
                {
                    'id': r['id'],
                    'nom': r.get('nom') or '',
                    'categorie': r.get('categorie__nom') or '',
                    'marque': r.get('marque__nom') or '',
                    'description': r.get('description') or '',
                }
                for r in produits_qs
            ]
            gestionnaire.modele_contenu.entrainer(produits)
            # Sauvegarde artefact
            out_dir = Path(getattr(settings, 'ML_ARTIFACTS_DIR', Path('ml_models') / 'artifacts'))
            out_dir.mkdir(parents=True, exist_ok=True)
            contenu_path = out_dir / 'modele_recommandation_contenu_latest.joblib'
            try:
                gestionnaire.modele_contenu.sauvegarder(str(contenu_path))
            except Exception as _e:
                logger.warning(f"Sauvegarde artefact contenu échouée: {_e}")
            # Registry cache
            reg = cache.get('ml_registry') or {}
            reg['contenu'] = str(contenu_path)
            cache.set('ml_registry', reg, None)
            
            # Sauvegarder les métadonnées
            ModeleML.objects.update_or_create(
                nom='recommandation_contenu',
                defaults={
                    'version': '1.0.0',
                    'type_modele': 'recommandation',
                    'precision': 0.85,  # Valeur exemple
                    'est_actif': True,
                    'parametres': {'n_composantes': 100}
                }
            )
            
        elif modele_type == 'prix':
            # Entraînement du modèle de prix
            from apps.produits.models import Prix
            prix_qs = Prix.objects.select_related(
                'produit__categorie', 'produit__marque', 'produit__unite_mesure', 'magasin__ville'
            ).values(
                'produit__categorie__nom',
                'produit__marque__nom',
                'produit__unite_mesure__symbole',
                'produit__quantite_unite',
                'magasin__nom',
                'magasin__ville__nom',
                'magasin__type',
                'magasin__zone',
                'type_prix',
                'prix_actuel',
                'date_modification'
            )[:50000]
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
                    'prix': r.get('prix_actuel'),
                    'date': r.get('date_modification'),
                }
                for r in prix_qs
            ]
            
            if prix_data:
                gestionnaire.modele_prix.entrainer(prix_data)
                # Sauvegarde artefact
                out_dir = Path(getattr(settings, 'ML_ARTIFACTS_DIR', Path('ml_models') / 'artifacts'))
                out_dir.mkdir(parents=True, exist_ok=True)
                prix_path = out_dir / 'modele_prediction_prix_latest.joblib'
                try:
                    from ml_models.modele_prediction_prix import ModelePredictionPrix as _Tmp  # noqa
                except Exception:
                    pass
                try:
                    # Le modèle interne n'a pas de méthode save exposée ici, on persiste via joblib si besoin
                    # mais on s'en tient à l'API existante (sauvegarde non critique)
                    import joblib
                    joblib.dump(gestionnaire.modele_prix, str(prix_path))
                except Exception as _e:
                    logger.warning(f"Sauvegarde artefact prix échouée: {_e}")
                reg = cache.get('ml_registry') or {}
                reg['prix'] = str(prix_path)
                cache.set('ml_registry', reg, None)
                
                ModeleML.objects.update_or_create(
                    nom='prediction_prix',
                    defaults={
                        'version': '1.0.0',
                        'type_modele': 'prediction_prix',
                        'precision': 0.78,  # Valeur exemple
                        'est_actif': True
                    }
                )
        
        # Vider le cache des recommandations
        cache.clear()
        
        logger.info(f"Entraînement terminé pour: {modele_type}")
        return f"Modèle {modele_type} entraîné avec succès"
        
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement: {e}")
        raise self.retry(countdown=60 * 5, exc=e)  # Retry après 5 minutes

@shared_task
def generer_recommandations_quotidiennes():
    """Tâche pour générer des recommandations quotidiennes pour tous les utilisateurs"""
    try:
        from django.contrib.auth import get_user_model
        from .models import HistoriqueRecommandation
        from apps.produits.models import Produit
        
        User = get_user_model()
        gestionnaire = GestionnaireRecommandations()
        
        utilisateurs_actifs = User.objects.filter(is_active=True)[:1000]  # Limiter pour les tests
        
        for utilisateur in utilisateurs_actifs:
            try:
                recommandations = gestionnaire.get_recommandations_utilisateur(
                    utilisateur.id, 
                    n_recommandations=5
                )
                
                # Sauvegarder les meilleures recommandations
                for reco in recommandations[:3]:
                    produit = Produit.objects.get(id=reco['produit']['id'])
                    HistoriqueRecommandation.objects.create(
                        utilisateur=utilisateur,
                        produit_recommande=produit,
                        score_confiance=reco['score_similarite'],
                        algorithme_utilise=reco['algorithme']
                    )
                    
            except Exception as e:
                logger.error(f"Erreur pour utilisateur {utilisateur.id}: {e}")
                continue
        
        logger.info(f"Recommandations quotidiennes générées pour {len(utilisateurs_actifs)} utilisateurs")
        
    except Exception as e:
        logger.error(f"Erreur génération recommandations quotidiennes: {e}")

@shared_task
def nettoyer_historique_ancien():
    """Nettoyage de l'historique des recommandations anciennes"""
    from django.utils import timezone
    from datetime import timedelta
    from .models import HistoriqueRecommandation
    
    date_limite = timezone.now() - timedelta(days=90)  # Garder 3 mois
    supprimes = HistoriqueRecommandation.objects.filter(
        date_creation__lt=date_limite
    ).delete()
    
    logger.info(f"Historique nettoyé: {supprimes[0]} enregistrements supprimés")