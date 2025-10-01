from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import logging
from .utils import construire_lien_activation, construire_lien_reset

logger = logging.getLogger(__name__)

@shared_task
def task_mise_a_jour_niveaux_fidelite():
    """
    Tâche périodique pour mettre à jour les niveaux de fidélité
    """
    from .models import Utilisateur
    from .services import ServiceFidelite
    
    try:
        utilisateurs = Utilisateur.objects.filter(
            total_achats__gt=0
        )
        
        for utilisateur in utilisateurs:
            ancien_niveau = utilisateur.niveau_fidelite
            nouveau_niveau = ServiceFidelite.calculer_niveau_fidelite(
                utilisateur.total_achats
            )
            
            if nouveau_niveau != ancien_niveau:
                utilisateur.niveau_fidelite = nouveau_niveau
                utilisateur.save(update_fields=['niveau_fidelite'])
                
                logger.info(
                    f"Mise à jour niveau fidélité: {utilisateur.username} "
                    f"({ancien_niveau} -> {nouveau_niveau})"
                )
        
        logger.info("Mise à jour des niveaux de fidélité terminée")
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des niveaux: {e}")
        raise

@shared_task
def send_reset_email(user_email: str, reset_token: str):
    """Envoie l'email de réinitialisation de mot de passe avec lien signé."""
    try:
        lien = construire_lien_reset(reset_token)
        sujet = _("Réinitialisation de votre mot de passe")
        message = _(
            "Bonjour,\n\n"
            "Vous avez demandé à réinitialiser votre mot de passe. Cliquez sur le lien suivant :\n"
            f"{lien}\n\n"
            "Ce lien est valable 1 heure. Si vous n'êtes pas à l'origine de cette demande, ignorez cet email.\n\n"
            "Cordialement,\nL'équipe Comparateur Prix"
        )
        send_mail(
            sujet,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
            [user_email],
            fail_silently=False,
        )
        logger.info("Email de réinitialisation envoyé à %s", user_email)
    except Exception as e:
        logger.error("Erreur envoi email de réinitialisation à %s: %s", user_email, e)
        raise

@shared_task
def send_activation_email(user_email: str, activation_token: str):
    """Envoie l'email d'activation de compte avec lien signé."""
    try:
        lien = construire_lien_activation(activation_token)
        sujet = _("Activation de votre compte")
        message = _(
            "Bonjour,\n\n"
            "Merci de votre inscription. Pour activer votre compte, cliquez sur le lien suivant :\n"
            f"{lien}\n\n"
            "Ce lien est valable 24 heures.\n\n"
            "Cordialement,\nL'équipe Comparateur Prix"
        )
        send_mail(
            sujet,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
            [user_email],
            fail_silently=False,
        )
        logger.info("Email d'activation envoyé à %s", user_email)
    except Exception as e:
        logger.error("Erreur envoi email d'activation à %s: %s", user_email, e)
        raise

@shared_task
def task_nettoyage_historique():
    """
    Tâche de nettoyage de l'historique ancien
    """
    from .models import HistoriqueConnexion, HistoriqueRemises
    
    try:
        # Supprimer les historiques de plus de 2 ans
        date_limite = timezone.now() - timezone.timedelta(days=730)
        
        # Historique des connexions
        connexions_supprimees, _ = HistoriqueConnexion.objects.filter(
            date_connexion__lt=date_limite
        ).delete()
        
        # Historique des remises
        remises_supprimees, _ = HistoriqueRemises.objects.filter(
            date_application__lt=date_limite
        ).delete()
        
        logger.info(
            f"Nettoyage historique: "
            f"{connexions_supprimees} connexions, "
            f"{remises_supprimees} remises supprimées"
        )
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage de l'historique: {e}")
        raise

@shared_task
def task_verification_abonnements():
    """
    Tâche de vérification des abonnements expirés
    """
    from .models import Abonnement
    
    try:
        maintenant = timezone.now()
        
        # Désactiver les abonnements expirés
        abonnements_expires = Abonnement.objects.filter(
            est_actif=True,
            date_fin__lt=maintenant
        )
        
        for abonnement in abonnements_expires:
            abonnement.est_actif = False
            abonnement.save(update_fields=['est_actif'])
            
            # Envoyer notification d'expiration
            task_envoyer_notification_expiration.delay(abonnement.id)
        
        logger.info(f"{abonnements_expires.count()} abonnements désactivés")
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des abonnements: {e}")
        raise

@shared_task
def task_envoyer_notification_expiration(abonnement_id):
    """
    Envoie une notification d'expiration d'abonnement
    """
    from .models import Abonnement
    
    try:
        abonnement = Abonnement.objects.get(id=abonnement_id)
        utilisateur = abonnement.utilisateur
        
        sujet = _("Votre abonnement a expiré")
        message = _(
            f"Bonjour {utilisateur.first_name},\n\n"
            f"Votre abonnement {abonnement.get_type_abonnement_display()} "
            f"a expiré le {abonnement.date_fin.strftime('%d/%m/%Y')}.\n\n"
            f"Pour continuer à bénéficier de vos avantages, "
            f"renouvelez votre abonnement dès maintenant.\n\n"
            f"Cordialement,\nL'équipe de comparaison de prix"
        )
        
        send_mail(
            sujet,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [utilisateur.email],
            fail_silently=False,
        )
        
        logger.info(f"Notification expiration envoyée à {utilisateur.email}")
        
    except Exception as e:
        logger.error(f"Erreur envoi notification expiration: {e}")
        raise

@shared_task
def task_rapport_fidelite_quotidien():
    """
    Tâche de génération de rapport quotidien de fidélité
    """
    from .services import ServiceFidelite
    
    try:
        hier = timezone.now() - timezone.timedelta(days=1)
        date_debut = hier.replace(hour=0, minute=0, second=0, microsecond=0)
        date_fin = hier.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        rapport = ServiceFidelite.generer_rapport_fidelite(date_debut, date_fin)
        
        # Envoyer le rapport par email aux administrateurs
        sujet = _("Rapport quotidien de fidélité")
        message = _(
            f"Rapport de fidélité pour le {date_debut.strftime('%d/%m/%Y')}:\n\n"
            f"Utilisateurs actifs: {rapport['utilisateurs_actifs']}\n"
            f"Total achats: {rapport['total_achats']}€\n"
            f"Remises appliquées: {rapport['remises_appliquees']}\n"
            f"Économies totales: {rapport['total_economies']}€\n\n"
            f"Répartition par niveau:\n"
            f"Niveau 1: {rapport['repartition_niveaux'][1]}\n"
            f"Niveau 2: {rapport['repartition_niveaux'][2]}\n"
            f"Niveau 3: {rapport['repartition_niveaux'][3]}\n"
            f"Niveau 4: {rapport['repartition_niveaux'][4]}\n"
            f"Niveau 5: {rapport['repartition_niveaux'][5]}\n"
        )
        
        if settings.ADMINS:
            emails_admin = [admin[1] for admin in settings.ADMINS]
            send_mail(
                sujet,
                message,
                settings.DEFAULT_FROM_EMAIL,
                emails_admin,
                fail_silently=False,
            )
        
        logger.info("Rapport quotidien de fidélité généré et envoyé")
        
    except Exception as e:
        logger.error(f"Erreur génération rapport fidélité: {e}")
        raise