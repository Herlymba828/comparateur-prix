from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import Utilisateur, ProfilUtilisateur, Abonnement, HistoriqueRemises, HistoriqueConnexion

class InscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription des utilisateurs"""
    
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirmation = serializers.CharField(write_only=True)
    
    class Meta:
        model = Utilisateur
        fields = [
            'username', 'email', 'password', 'password_confirmation',
            'first_name', 'last_name', 'type_utilisateur', 'telephone',
            'code_postal', 'ville', 'date_naissance'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirmation'):
            raise serializers.ValidationError({
                'password': _('Les mots de passe ne correspondent pas.')
            })
        
        if Utilisateur.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({
                'email': _('Un utilisateur avec cet email existe déjà.')
            })
        
        return attrs

class HistoriqueConnexionSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des connexions utilisateur."""
    class Meta:
        model = HistoriqueConnexion
        fields = [
            'id', 'date_connexion', 'ip_address', 'user_agent', 'reussi'
        ]

class DemandeResetMotDePasseSerializer(serializers.Serializer):
    """Serializer pour la demande de réinitialisation de mot de passe"""
    email = serializers.EmailField()

    def validate_email(self, value):
        # Ne pas révéler l'existence du compte; validation basique
        return value

class ConfirmationResetMotDePasseSerializer(serializers.Serializer):
    """Serializer pour la confirmation de réinitialisation de mot de passe"""
    nouveau_mot_de_passe = serializers.CharField(write_only=True, min_length=8)
    confirmation_mot_de_passe = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['nouveau_mot_de_passe'] != attrs['confirmation_mot_de_passe']:
            raise serializers.ValidationError({
                'confirmation_mot_de_passe': _('Les mots de passe ne correspondent pas.')
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirmation', None)
        user = Utilisateur.objects.create_user(**validated_data)
        return user

class ConnexionSerializer(serializers.Serializer):
    """Serializer pour l'authentification"""
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    _('Identifiants invalides.'),
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    _('Ce compte est désactivé.'),
                    code='authorization'
                )
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                _('Must include "username" and "password".'),
                code='authorization'
            )
        
        return attrs

class ProfilUtilisateurSerializer(serializers.ModelSerializer):
    """Serializer pour le profil utilisateur"""
    
    class Meta:
        model = ProfilUtilisateur
        fields = [
            'avatar', 'bio', 'site_web', 'notifications_actives',
            'newsletter_abonnement', 'preferences_recherche',
            'rayon_recherche_km', 'alertes_remises',
            'categories_preferees_remises'
        ]

class StatistiquesFideliteSerializer(serializers.Serializer):
    """Serializer pour les statistiques de fidélité"""
    
    points_fidelite = serializers.IntegerField()
    niveau_fidelite = serializers.IntegerField()
    pourcentage_remise = serializers.DecimalField(max_digits=5, decimal_places=2)
    total_achats = serializers.DecimalField(max_digits=10, decimal_places=2)
    nombre_commandes = serializers.IntegerField()
    est_client_fidele = serializers.BooleanField()
    prochain_niveau_seuil = serializers.DecimalField(max_digits=10, decimal_places=2)
    progression_niveau = serializers.DecimalField(max_digits=5, decimal_places=2)

class UtilisateurSerializer(serializers.ModelSerializer):
    """Serializer complet pour les utilisateurs"""
    
    profil = ProfilUtilisateurSerializer(read_only=True)
    statistiques_fidelite = StatistiquesFideliteSerializer(read_only=True)
    age = serializers.ReadOnlyField()
    est_nouveau = serializers.ReadOnlyField()
    est_client_fidele = serializers.ReadOnlyField()
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'uuid', 'username', 'email', 'first_name', 'last_name',
            'type_utilisateur', 'telephone', 'date_naissance', 'code_postal',
            'ville', 'preferences', 'date_creation', 'derniere_connexion',
            'est_verifie', 'nom_entreprise', 'siret', 'profil',
            'points_fidelite', 'niveau_fidelite', 'total_achats', 
            'nombre_commandes', 'statistiques_fidelite', 'age', 'est_nouveau',
            'est_client_fidele'
        ]
        read_only_fields = [
            'id', 'uuid', 'date_creation', 'derniere_connexion',
            'points_fidelite', 'niveau_fidelite', 'total_achats', 'nombre_commandes'
        ]

class UtilisateurLightSerializer(serializers.ModelSerializer):
    """Serializer léger pour les listes"""
    
    est_client_fidele = serializers.ReadOnlyField()
    
    class Meta:
        model = Utilisateur
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'type_utilisateur', 'est_client_fidele'
        ]

class MiseAJourUtilisateurSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour des utilisateurs"""
    
    class Meta:
        model = Utilisateur
        fields = [
            'first_name', 'last_name', 'telephone', 'date_naissance',
            'code_postal', 'ville', 'preferences'
        ]
    
    def validate_telephone(self, value):
        if value and not value.startswith('+'):
            value = f"+33{value.lstrip('0')}"
        return value

class AbonnementSerializer(serializers.ModelSerializer):
    """Serializer pour les abonnements"""
    
    est_valide = serializers.ReadOnlyField()
    remise_totale = serializers.SerializerMethodField()
    
    class Meta:
        model = Abonnement
        fields = [
            'type_abonnement', 'date_debut', 'date_fin', 
            'est_actif', 'est_valide', 'remise_supplementaire',
            'livraison_gratuite', 'acces_prioritaire', 'remise_totale'
        ]
    
    def get_remise_totale(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_remise_totale(request.user)
        return obj.remise_supplementaire

class ChangementMotDePasseSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe"""
    
    ancien_mot_de_passe = serializers.CharField(write_only=True)
    nouveau_mot_de_passe = serializers.CharField(write_only=True, min_length=8)
    confirmation_mot_de_passe = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['nouveau_mot_de_passe'] != attrs['confirmation_mot_de_passe']:
            raise serializers.ValidationError({
                'confirmation_mot_de_passe': _('Les mots de passe ne correspondent pas.')
            })
        return attrs

class HistoriqueRemisesSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des remises"""
    
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_marque = serializers.CharField(source='produit.marque', read_only=True)
    
    class Meta:
        model = HistoriqueRemises
        fields = [
            'id', 'produit', 'produit_nom', 'produit_marque', 'prix_original',
            'prix_remise', 'pourcentage_remise', 'montant_economise',
            'date_application', 'type_remise'
        ]
        read_only_fields = fields

class ApplicationRemiseSerializer(serializers.Serializer):
    """Serializer pour l'application d'une remise"""
    
    produit_id = serializers.IntegerField()
    prix_original = serializers.DecimalField(max_digits=10, decimal_places=2)
    categorie_id = serializers.IntegerField(required=False, allow_null=True)
    
    def validate(self, attrs):
        # Vérifier que le produit existe
        from apps.produits.models import Produit
        try:
            produit = Produit.objects.get(id=attrs['produit_id'])
            attrs['produit'] = produit
        except Produit.DoesNotExist:
            raise serializers.ValidationError({
                'produit_id': _('Produit non trouvé.')
            })
        
        return attrs