from celery import shared_task
import logging
from django.core.cache import cache
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
            produits = list(Produit.objects.values('id', 'nom', 'categorie', 'marque', 'description'))
            gestionnaire.modele_contenu.entrainer(produits)
            
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
            from apps.prix.models import HistoriquePrix
            prix_data = list(HistoriquePrix.objects.values(
                'produit__categorie', 'produit__marque', 'magasin__nom', 
                'magasin__ville', 'prix', 'date'
            )[:50000])
            
            if prix_data:
                gestionnaire.modele_prix.entrainer(prix_data)
                
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