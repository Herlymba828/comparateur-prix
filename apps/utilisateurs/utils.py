from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from decimal import Decimal
import json
from datetime import timedelta
import os
import secrets

class CacheUtilisateur:
    """Classe utilitaire pour la gestion du cache des utilisateurs"""
    
    CACHE_PREFIX = 'utilisateur'
    DUREE_CACHE = 3600  # 1 heure
    
    @classmethod
    def get_cle_utilisateur(cls, utilisateur_id):
        """Génère une clé de cache pour un utilisateur"""
        return f'{cls.CACHE_PREFIX}_{utilisateur_id}'
    
    @classmethod
    def get_statistiques_utilisateur(cls, utilisateur_id):
        """Récupère les statistiques utilisateur depuis le cache"""
        cle = cls.get_cle_utilisateur(utilisateur_id)
        return cache.get(cle)
    
    @classmethod
    def set_statistiques_utilisateur(cls, utilisateur_id, statistiques):
        """Enregistre les statistiques utilisateur dans le cache"""
        cle = cls.get_cle_utilisateur(utilisateur_id)
        cache.set(cle, statistiques, cls.DUREE_CACHE)
    
    @classmethod
    def invalider_cache_utilisateur(cls, utilisateur_id):
        """Invalide le cache d'un utilisateur"""
        cle = cls.get_cle_utilisateur(utilisateur_id)
        cache.delete(cle)

class CalculateurRemise:
    """Classe utilitaire pour les calculs de remise"""
    
    @staticmethod
    def calculer_remise(prix_original, pourcentage_remise):
        """Calcule le prix après remise"""
        if pourcentage_remise <= 0:
            return prix_original, Decimal('0.00')
        
        montant_remise = (prix_original * Decimal(pourcentage_remise)) / 100
        prix_remise = prix_original - montant_remise
        
        return prix_remise, montant_remise
    
    @staticmethod
    def calculer_pourcentage_remise(prix_original, prix_remise):
        """Calcule le pourcentage de remise appliqué"""
        if prix_original <= 0:
            return Decimal('0.00')
        
        economie = prix_original - prix_remise
        pourcentage = (economie / prix_original) * 100
        
        return round(pourcentage, 2)
    
    @staticmethod
    def appliquer_remises_cumulatives(prix_original, remises):
        """
        Applique plusieurs remises de manière cumulative
        
        Args:
            prix_original: Prix original
            remises: Liste des pourcentages de remise
        
        Returns:
            tuple: (prix_final, montant_total_remise)
        """
        prix_courant = prix_original
        montant_total_remise = Decimal('0.00')
        
        for remise in remises:
            prix_apres_remise, montant_remise = CalculateurRemise.calculer_remise(
                prix_courant, remise
            )
            montant_total_remise += montant_remise
            prix_courant = prix_apres_remise
        
        return prix_courant, montant_total_remise

class ValidateurUtilisateur:
    """Classe utilitaire pour la validation des données utilisateur"""
    
    @staticmethod
    def valider_email(email):
        """Valide le format d'un email"""
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False
    
    @staticmethod
    def valider_telephone(telephone):
        """Valide le format d'un numéro de téléphone"""
        import re
        
        pattern = r'^\+?1?\d{9,15}$'
        return re.match(pattern, telephone) is not None
    
    @staticmethod
    def valider_code_postal(code_postal):
        """Valide le format d'un code postal français"""
        import re
        
        pattern = r'^\d{5}$'
        return re.match(pattern, code_postal) is not None
    
    @staticmethod
    def valider_mot_de_passe(mot_de_passe):
        """
        Valide la force d'un mot de passe
        
        Returns:
            tuple: (est_valide, erreurs)
        """
        erreurs = []
        
        if len(mot_de_passe) < 8:
            erreurs.append("Le mot de passe doit contenir au moins 8 caractères")
        
        if not any(c.isdigit() for c in mot_de_passe):
            erreurs.append("Le mot de passe doit contenir au moins un chiffre")
        
        if not any(c.isupper() for c in mot_de_passe):
            erreurs.append("Le mot de passe doit contenir au moins une majuscule")
        
        if not any(c.islower() for c in mot_de_passe):
            erreurs.append("Le mot de passe doit contenir au moins une minuscule")
        
        return len(erreurs) == 0, erreurs

class GenerateurRapport:
    """Classe utilitaire pour la génération de rapports"""
    
    @staticmethod
    def generer_rapport_utilisateurs(utilisateurs, date_debut, date_fin):
        """Génère un rapport détaillé sur les utilisateurs"""
        rapport = {
            'periode': {
                'debut': date_debut.isoformat(),
                'fin': date_fin.isoformat()
            },
            'statistiques_generales': {
                'total_utilisateurs': utilisateurs.count(),
                'nouveaux_utilisateurs': utilisateurs.filter(
                    date_creation__range=[date_debut, date_fin]
                ).count(),
                'utilisateurs_actifs': utilisateurs.filter(
                    derniere_connexion__range=[date_debut, date_fin]
                ).count(),
            },
            'repartition_type_utilisateur': {},
            'repartition_niveau_fidelite': {},
            'top_utilisateurs': []
        }
        
        # Répartition par type d'utilisateur
        for type_utilisateur, label in Utilisateur.TypesUtilisateur.choices:
            count = utilisateurs.filter(type_utilisateur=type_utilisateur).count()
            rapport['repartition_type_utilisateur'][label] = count
        
        # Répartition par niveau de fidélité
        for niveau in range(1, 6):
            count = utilisateurs.filter(niveau_fidelite=niveau).count()
            rapport['repartition_niveau_fidelite'][f'Niveau {niveau}'] = count
        
        # Top utilisateurs par achats
        top_acheteurs = utilisateurs.order_by('-total_achats')[:10]
        for utilisateur in top_acheteurs:
            rapport['top_utilisateurs'].append({
                'username': utilisateur.username,
                'email': utilisateur.email,
                'total_achats': float(utilisateur.total_achats),
                'niveau_fidelite': utilisateur.niveau_fidelite
            })
        
        return rapport
    
    @staticmethod
    def formater_rapport_json(rapport):
        """Formate un rapport en JSON lisible"""
        return json.dumps(rapport, indent=2, ensure_ascii=False)

# --- Activation email utils ---
from django.core import signing  # noqa: E402
from django.conf import settings  # noqa: E402
from django.contrib.auth.tokens import default_token_generator  # noqa: E402
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode  # noqa: E402
from django.utils.encoding import force_bytes, force_str  # noqa: E402

ACTIVATION_SALT = "utilisateur-activation"
RESET_SALT = "utilisateur-reset-mdp"

def generer_token_activation(utilisateur_id: int, email: str) -> str:
    """Génère un token signé et horodaté pour l'activation de compte."""
    payload = {"uid": utilisateur_id, "email": email}
    return signing.TimestampSigner(salt=ACTIVATION_SALT).sign_object(payload)

def verifier_token_activation(token: str, max_age_seconds: int = 60 * 60 * 24) -> dict | None:
    """Vérifie et retourne le payload si valide; None sinon."""
    try:
        data = signing.TimestampSigner(salt=ACTIVATION_SALT).unsign_object(token, max_age=max_age_seconds)
        return data if isinstance(data, dict) and "uid" in data and "email" in data else None
    except Exception:
        return None

def construire_lien_activation(token: str) -> str:
    """Construit l'URL d'activation à inclure dans l'email.
    Utilise FRONTEND_URL si défini, sinon l'endpoint API.
    """
    base_front = os.getenv("FRONTEND_URL")
    if base_front:
        # Exemple de route front: /activer-compte?token=...
        sep = "&" if "?" in base_front else "?"
        return f"{base_front.rstrip('/')}/activer-compte{sep}token={token}"
    # Fallback: endpoint API
    api_base = os.getenv("BACKEND_URL", "http://localhost:8000")
    return f"{api_base.rstrip('/')}/api/utilisateurs/api/auth/activation/confirmer/{token}/"

# --- UIDB64 + token (standard Django) activation helpers ---
def make_activation_uid_token(user):
    """Retourne (uidb64, token) pour l'activation (standard Django tokens)."""
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return uidb64, token

def check_activation_uid_token(uidb64: str, token: str, user_model):
    """Valide (uidb64, token) et retourne l'utilisateur si valide, sinon None."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = user_model.objects.get(pk=uid)
    except Exception:
        return None
    if default_token_generator.check_token(user, token):
        return user
    return None

def build_activation_link_uid(uidb64: str, token: str) -> str:
    """Construit le lien public: {PUBLIC_BASE_URL}/activate/<uidb64>/<token>/"""
    base = os.getenv("PUBLIC_BASE_URL") or getattr(settings, "PUBLIC_BASE_URL", "https://mon-domaine.com")
    return f"{base.rstrip('/')}/activate/{uidb64}/{token}/"

# --- Reset mot de passe utils ---
def generer_token_reset(utilisateur_id: int, email: str) -> str:
    payload = {"uid": utilisateur_id, "email": email}
    return signing.TimestampSigner(salt=RESET_SALT).sign_object(payload)

def verifier_token_reset(token: str, max_age_seconds: int = 60 * 60) -> dict | None:
    try:
        data = signing.TimestampSigner(salt=RESET_SALT).unsign_object(token, max_age=max_age_seconds)
        return data if isinstance(data, dict) and "uid" in data and "email" in data else None
    except Exception:
        return None

def construire_lien_reset(token: str) -> str:
    base_front = os.getenv("FRONTEND_URL")
    if base_front:
        sep = "&" if "?" in base_front else "?"
        return f"{base_front.rstrip('/')}/reinitialiser-mot-de-passe{sep}token={token}"
    api_base = os.getenv("BACKEND_URL", "http://localhost:8000")
    return f"{api_base.rstrip('/')}/api/utilisateurs/api/auth/mot-de-passe/confirmer/{token}/"

# --- Code d'activation (6 chiffres) ---
def generer_code_activation() -> str:
    """Génère un code d'activation de 6 chiffres."""
    try:
        code = f"{secrets.randbelow(1000000):06d}"
        return code
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la génération du code d'activation: {type(e).__name__} - {str(e)}")
        raise

def stocker_code_activation(user_id: int, code: str, expiration_minutes: int = 15) -> None:
    """Stocke le code d'activation dans le cache avec expiration."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        cache_key = f"activation_code_{user_id}"
        cache.set(cache_key, code, timeout=expiration_minutes * 60)
        logger.debug(f"Code d'activation stocké pour user_id: {user_id}, expiration: {expiration_minutes} minutes")
    except Exception as e:
        error_msg = f"Erreur lors du stockage du code d'activation. User ID: {user_id}, Type: {type(e).__name__}, Message: {str(e)}"
        logger.error(error_msg)
        # Ne pas lever l'exception pour ne pas faire échouer l'inscription
        # Le code sera quand même généré et envoyé par email

def verifier_code_activation(user_id: int, code: str) -> bool:
    """Vérifie si le code d'activation est valide pour l'utilisateur."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        cache_key = f"activation_code_{user_id}"
        stored_code = cache.get(cache_key)
        if stored_code is None:
            logger.warning(f"Code d'activation non trouvé ou expiré pour user_id: {user_id}")
            return False
        # Comparaison sécurisée pour éviter les attaques par timing
        is_valid = secrets.compare_digest(str(stored_code), str(code))
        if is_valid:
            logger.info(f"Code d'activation vérifié avec succès pour user_id: {user_id}")
        else:
            logger.warning(f"Code d'activation invalide pour user_id: {user_id}")
        return is_valid
    except Exception as e:
        error_msg = f"Erreur lors de la vérification du code d'activation. User ID: {user_id}, Type: {type(e).__name__}, Message: {str(e)}"
        logger.error(error_msg)
        # En cas d'erreur, considérer le code comme invalide pour la sécurité
        return False

def supprimer_code_activation(user_id: int) -> None:
    """Supprime le code d'activation du cache."""
    import logging
    logger = logging.getLogger(__name__)
    try:
        cache_key = f"activation_code_{user_id}"
        cache.delete(cache_key)
        logger.debug(f"Code d'activation supprimé pour user_id: {user_id}")
    except Exception as e:
        # Ne pas lever l'exception, juste logger l'erreur
        error_msg = f"Erreur lors de la suppression du code d'activation. User ID: {user_id}, Type: {type(e).__name__}, Message: {str(e)}"
        logger.warning(error_msg)