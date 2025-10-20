from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
from .models import Utilisateur, ProfilUtilisateur, Abonnement, HistoriqueRemises
from django.contrib.auth.models import Group
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def creer_profil_utilisateur(sender, instance, created, **kwargs):
    """Créer automatiquement un profil lors de la création d'un utilisateur"""
    if created:
        ProfilUtilisateur.objects.create(utilisateur=instance)
        logger.info(f"Profil créé pour l'utilisateur {instance.username}")

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def creer_abonnement_par_defaut(sender, instance, created, **kwargs):
    """Créer un abonnement gratuit par défaut"""
    if created:
        from datetime import timedelta
        Abonnement.objects.create(
            utilisateur=instance,
            date_fin=timezone.now() + timedelta(days=365*10)  # 10 ans
        )
        logger.info(f"Abonnement par défaut créé pour {instance.username}")

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def rattacher_groupe_user(sender, instance, created, **kwargs):
    """Ajouter automatiquement l'utilisateur au groupe 'user' lors de sa création.

    S'applique à toute création d'utilisateur (inscription classique, logins sociaux, etc.).
    """
    if created:
        try:
            grp_user, _ = Group.objects.get_or_create(name='user')
            instance.groups.add(grp_user)
            logger.info(f"Utilisateur {instance.username} ajouté au groupe 'user'")
        except Exception as e:
            logger.warning(f"Impossible d'ajouter {instance.username} au groupe 'user': {e}")

@receiver(pre_save, sender=Utilisateur)
def logger_changement_niveau_fidelite(sender, instance, **kwargs):
    """Logger les changements de niveau de fidélité"""
    if instance.pk:
        try:
            ancien_utilisateur = Utilisateur.objects.get(pk=instance.pk)
            if ancien_utilisateur.niveau_fidelite != instance.niveau_fidelite:
                logger.info(
                    f"Changement niveau fidélité: {instance.username} "
                    f"({ancien_utilisateur.niveau_fidelite} -> {instance.niveau_fidelite})"
                )
        except Utilisateur.DoesNotExist:
            pass

@receiver(post_save, sender=HistoriqueRemises)
def notifier_remise_appliquee(sender, instance, created, **kwargs):
    """Envoyer une notification lorsqu'une remise est appliquée"""
    if created:
        from .tasks import task_envoyer_notification_remise
        task_envoyer_notification_remise.delay(instance.id)

@receiver(post_save, sender=Abonnement)
def logger_changement_abonnement(sender, instance, created, **kwargs):
    """Logger les changements d'abonnement"""
    if created:
        logger.info(f"Nouvel abonnement créé: {instance}")
    else:
        logger.info(f"Abonnement modifié: {instance}")

@receiver(pre_save, sender=Abonnement)
def verifier_expiration_abonnement(sender, instance, **kwargs):
    """Vérifier et mettre à jour le statut d'expiration"""
    if instance.pk and instance.date_fin < timezone.now():
        instance.est_actif = False
        logger.info(f"Abonnement expiré désactivé: {instance}")

@receiver(post_delete, sender=ProfilUtilisateur)
def supprimer_avatar(sender, instance, **kwargs):
    """Supprimer le fichier avatar lors de la suppression du profil"""
    if instance.avatar:
        instance.avatar.delete(save=False)
        logger.info(f"Avatar supprimé pour le profil de {instance.utilisateur.username}")

@receiver(post_save, sender=ProfilUtilisateur)
def mettre_a_jour_preferences(sender, instance, created, **kwargs):
    """Mettre à jour les préférences utilisateur"""
    if not created and 'preferences_recherche' in instance.get_dirty_fields():
        logger.info(f"Préférences mises à jour pour {instance.utilisateur.username}")