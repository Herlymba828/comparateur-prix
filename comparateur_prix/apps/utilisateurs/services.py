from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class ServiceFidelite:
    """Service de gestion de la fidélité des utilisateurs"""
    
    # Seuils de fidélité (en euros)
    SEUILS_NIVEAUX = {
        1: 0,      # Débutant
        2: 50,     # Occasionnel
        3: 200,    # Fidèle
        4: 500,    # Premium
        5: 1000    # VIP
    }
    
    # Pourcentages de remise par niveau
    REMISES_NIVEAUX = {
        1: 0,      # 0%
        2: 2,      # 2%
        3: 5,      # 5%
        4: 10,     # 10%
        5: 15      # 15%
    }
    
    # Points par euro dépensé
    POINTS_PAR_EURO = 1
    
    @classmethod
    def calculer_points_achat(cls, montant_achat):
        """Calcule les points à attribuer pour un achat"""
        return int(montant_achat * cls.POINTS_PAR_EURO)
    
    @classmethod
    def calculer_niveau_fidelite(cls, total_achats):
        """Calcule le niveau de fidélité selon le total des achats"""
        for niveau, seuil in sorted(cls.SEUILS_NIVEAUX.items(), reverse=True):
            if total_achats >= seuil:
                return niveau
        return 1
    
    @classmethod
    def traiter_achat(cls, utilisateur, montant_achat, produits=None):
        """
        Traite un achat et met à jour la fidélité
        
        Args:
            utilisateur: Instance de l'utilisateur
            montant_achat: Montant total de l'achat
            produits: Liste des produits achetés (optionnel)
        """
        try:
            with transaction.atomic():
                # Calculer les points
                points_gagnes = cls.calculer_points_achat(montant_achat)
                
                # Mettre à jour l'utilisateur
                utilisateur.ajouter_points_fidelite(points_gagnes, montant_achat)
                
                # Enregistrer l'achat dans l'historique
                if produits:
                    cls._enregistrer_achat_details(utilisateur, produits, montant_achat)
                
                logger.info(
                    f"Achat traité pour {utilisateur.username}: "
                    f"{montant_achat}€ -> {points_gagnes} points"
                )
                
                return points_gagnes
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'achat: {e}")
            raise
    
    @classmethod
    def _enregistrer_achat_details(cls, utilisateur, produits, montant_achat):
        """Enregistre les détails d'un achat"""
        from .models import HistoriqueAchat  # À créer si nécessaire
        
        for produit in produits:
            HistoriqueAchat.objects.create(
                utilisateur=utilisateur,
                produit=produit,
                montant=produit.prix,
                quantite=produit.quantite,
                date_achat=timezone.now()
            )
    
    @classmethod
    def get_remise_categorie(cls, utilisateur, categorie):
        """
        Retourne la remise supplémentaire pour une catégorie
        
        Args:
            utilisateur: Instance de l'utilisateur
            categorie: Instance de la catégorie
        
        Returns:
            Decimal: Pourcentage de remise supplémentaire
        """
        if not categorie or utilisateur.niveau_fidelite < 3:
            return Decimal('0.00')
        
        # Vérifier si la catégorie a une remise fidélité active
        if (hasattr(categorie, 'remise_fidele_active') and 
            categorie.remise_fidele_active and
            utilisateur.niveau_fidelite >= categorie.niveau_fidelite_requis):
            return categorie.remise_fidele_pourcentage
        
        return Decimal('0.00')
    
    @classmethod
    def appliquer_remise_utilisateur(cls, utilisateur, prix_original, categorie=None):
        """
        Applique la remise fidélité complète
        
        Args:
            utilisateur: Instance de l'utilisateur
            prix_original: Prix original du produit
            categorie: Catégorie du produit (optionnel)
        
        Returns:
            tuple: (prix_remise, montant_remise, pourcentage_remise)
        """
        # Remise de base selon le niveau
        remise_base = cls.REMISES_NIVEAUX.get(utilisateur.niveau_fidelite, 0)
        
        # Remise catégorielle supplémentaire
        remise_categorie = cls.get_remise_categorie(utilisateur, categorie)
        
        # Remise abonnement
        remise_abonnement = cls._get_remise_abonnement(utilisateur)
        
        remise_totale = remise_base + remise_categorie + remise_abonnement
        
        # Limiter la remise totale à 30%
        remise_totale = min(remise_totale, 30)
        
        montant_remise = (prix_original * Decimal(remise_totale)) / 100
        prix_remise = prix_original - montant_remise
        
        return prix_remise, montant_remise, remise_totale
    
    @classmethod
    def _get_remise_abonnement(cls, utilisateur):
        """Retourne la remise de l'abonnement"""
        if hasattr(utilisateur, 'abonnement') and utilisateur.abonnement.est_valide:
            return utilisateur.abonnement.remise_supplementaire
        return 0
    
    @classmethod
    def generer_rapport_fidelite(cls, date_debut, date_fin):
        """
        Génère un rapport de fidélité pour une période
        
        Args:
            date_debut: Date de début de la période
            date_fin: Date de fin de la période
        
        Returns:
            dict: Statistiques de fidélité
        """
        from .models import Utilisateur, HistoriqueRemises
        
        utilisateurs_actifs = Utilisateur.objects.filter(
            date_dernier_achat__range=[date_debut, date_fin]
        )
        
        total_achats = sum(u.total_achats for u in utilisateurs_actifs)
        remises_appliquees = HistoriqueRemises.objects.filter(
            date_application__range=[date_debut, date_fin]
        )
        
        total_economies = sum(r.montant_economise for r in remises_appliquees)
        
        return {
            'periode': {'debut': date_debut, 'fin': date_fin},
            'utilisateurs_actifs': utilisateurs_actifs.count(),
            'total_achats': total_achats,
            'remises_appliquees': remises_appliquees.count(),
            'total_economies': total_economies,
            'repartition_niveaux': cls._get_repartition_niveaux(utilisateurs_actifs)
        }
    
    @classmethod
    def _get_repartition_niveaux(cls, utilisateurs):
        """Retourne la répartition des utilisateurs par niveau"""
        repartition = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for utilisateur in utilisateurs:
            niveau = utilisateur.niveau_fidelite
            if niveau in repartition:
                repartition[niveau] += 1
        
        return repartition

class ServiceNotifications:
    """Service de gestion des notifications utilisateurs"""
    
    @classmethod
    def envoyer_notification_remise(cls, utilisateur, produit, remise):
        """Envoie une notification de remise à un utilisateur"""
        # Implémentation de l'envoi de notification
        # (email, push notification, etc.)
        pass
    
    @classmethod
    def envoyer_alerte_niveau(cls, utilisateur, ancien_niveau, nouveau_niveau):
        """Envoie une alerte de changement de niveau"""
        if nouveau_niveau > ancien_niveau:
            # Félicitations pour la progression
            pass
        # Implémentation des alertes
        pass