"""
Tâches asynchrones pour l'API (logs, analytics, etc.)
"""
from celery import shared_task
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def log_search_event_async(self, q, produit_id=None, utilisateur_id=None, ip_hash=None):
    """
    Log asynchrone des recherches (ne bloque pas la réponse API).
    
    Args:
        q: Terme de recherche
        produit_id: ID du produit (optionnel)
        utilisateur_id: ID de l'utilisateur (optionnel)
        ip_hash: Hash de l'IP (optionnel)
    """
    try:
        from .models import SearchEvent
        from apps.produits.models import Produit
        from apps.utilisateurs.models import Utilisateur
        
        produit_obj = None
        if produit_id:
            try:
                produit_obj = Produit.objects.only('id').get(id=produit_id)
            except Produit.DoesNotExist:
                produit_obj = None
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération du produit {produit_id}: {e}")
                produit_obj = None
        
        user_obj = None
        if utilisateur_id:
            try:
                user_obj = Utilisateur.objects.only('id').get(id=utilisateur_id)
            except Utilisateur.DoesNotExist:
                user_obj = None
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération de l'utilisateur {utilisateur_id}: {e}")
                user_obj = None
        
        # Créer l'événement de recherche dans une transaction
        with transaction.atomic():
            SearchEvent.objects.create(
                q=q,
                produit=produit_obj,
                utilisateur=user_obj,
                ip_hash=ip_hash
            )
        
        logger.debug(f"Événement de recherche loggé: q={q}, produit_id={produit_id}, user_id={utilisateur_id}")
        
    except Exception as e:
        logger.error(f"Erreur lors du log de recherche asynchrone: {e}", exc_info=True)
        # Réessayer si ce n'est pas la dernière tentative
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        else:
            logger.error(f"Échec définitif du log de recherche après {self.max_retries} tentatives")

