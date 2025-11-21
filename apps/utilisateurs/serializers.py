from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _
from .models import Utilisateur, ProfilUtilisateur, Abonnement, HistoriqueRemises, HistoriqueConnexion

class InscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour l'inscription des utilisateurs"""
    
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirmation = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = Utilisateur
        fields = [
            'username', 'email', 'password', 'password_confirmation',
            'first_name', 'last_name', 'type_utilisateur', 'telephone',
            'code_postal', 'ville', 'date_naissance'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
        }
    
    def validate_username(self, value):
        """Valider l'unicité du username"""
        if Utilisateur.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(_('Un utilisateur avec ce nom d\'utilisateur existe déjà.'))
        return value
    
    def validate_email(self, value):
        """Valider l'unicité de l'email"""
        if Utilisateur.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(_('Un utilisateur avec cet email existe déjà.'))
        return value.lower().strip() if value else value
    
    def validate_telephone(self, value):
        """Valider et normaliser le numéro de téléphone"""
        if not value or not value.strip():
            return ''  # Retourner chaîne vide si pas de téléphone
        
        # Normaliser le numéro (supprimer espaces, tirets, etc.)
        digits_only = ''.join(filter(str.isdigit, value))
        
        # Si pas de chiffres après normalisation, retourner vide
        if not digits_only:
            return ''
        
        # Si déjà au format international avec +
        if value.strip().startswith('+'):
            return value.strip()
        
        # Ajouter le préfixe international pour la France
        if digits_only.startswith('0'):
            normalized = '+33' + digits_only[1:]
        else:
            normalized = '+33' + digits_only
        
        # Vérifier que le numéro normalisé respecte le validateur (9-15 chiffres après +)
        if len(normalized) < 10 or len(normalized) > 16:  # +33 + 9-15 chiffres
            # Si invalide, retourner vide plutôt que de lever une erreur
            return ''
        
        return normalized
    
    def validate(self, attrs):
        """Validation globale"""
        # Vérifier que password et password_confirmation sont présents
        password = attrs.get('password')
        password_confirmation = attrs.get('password_confirmation')
        
        if not password:
            raise serializers.ValidationError({
                'password': _('Le mot de passe est requis.')
            })
        
        if not password_confirmation:
            raise serializers.ValidationError({
                'password_confirmation': _('La confirmation du mot de passe est requise.')
            })
        
        if password != password_confirmation:
            raise serializers.ValidationError({
                'password_confirmation': _('Les mots de passe ne correspondent pas.')
            })
        
        # Vérifications supplémentaires d'unicité (au cas où)
        email = attrs.get('email')
        username = attrs.get('username')
        
        if not email:
            raise serializers.ValidationError({
                'email': _('L\'email est requis.')
            })
        
        if not username:
            raise serializers.ValidationError({
                'username': _('Le nom d\'utilisateur est requis.')
            })
        
        if Utilisateur.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({
                'email': _('Un utilisateur avec cet email existe déjà.')
            })
        
        if Utilisateur.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError({
                'username': _('Un utilisateur avec ce nom d\'utilisateur existe déjà.')
            })
        
        return attrs

    def create(self, validated_data):
        """Créer un nouvel utilisateur avec mot de passe hashé"""
        # Retirer les champs qui ne sont pas dans le modèle
        validated_data = validated_data.copy()  # Copie pour éviter de modifier l'original
        password_confirmation = validated_data.pop('password_confirmation', None)
        password = validated_data.pop('password', None)
        
        # Vérifier que le mot de passe est présent
        if not password:
            raise serializers.ValidationError({
                'password': _('Le mot de passe est requis.')
            })
        
        # Extraire les champs obligatoires
        username = validated_data.pop('username', None)
        email = validated_data.pop('email', None)
        
        if not username:
            raise serializers.ValidationError({
                'username': _('Le nom d\'utilisateur est requis.')
            })
        
        if not email:
            raise serializers.ValidationError({
                'email': _('L\'email est requis.')
            })
        
        # Extraire les champs optionnels
        first_name = validated_data.pop('first_name', '')
        last_name = validated_data.pop('last_name', '')
        type_utilisateur = validated_data.pop('type_utilisateur', None)
        telephone = validated_data.pop('telephone', '')
        code_postal = validated_data.pop('code_postal', '')
        ville = validated_data.pop('ville', '')
        date_naissance = validated_data.pop('date_naissance', None)
        
        # Créer l'utilisateur avec create_user() qui gère mieux le mot de passe
        try:
            user = Utilisateur.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            
            # Mettre à jour les champs personnalisés
            if type_utilisateur:
                user.type_utilisateur = type_utilisateur
            if telephone:
                user.telephone = telephone
            if code_postal:
                user.code_postal = code_postal
            if ville:
                user.ville = ville
            if date_naissance:
                user.date_naissance = date_naissance
            
            # Mettre à jour les autres champs optionnels restants
            for key, value in validated_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            # L'utilisateur est actif par défaut
            user.is_active = True
            user.save()
            
        except Exception as e:
            # Si create_user échoue, lever une ValidationError avec le message
            raise serializers.ValidationError({
                'non_field_errors': [f'Erreur lors de la création de l\'utilisateur: {str(e)}']
            })
        
        return user

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
    """Serializer pour l'authentification (username OU email + password)."""
    
    identifiant = serializers.CharField(required=False)
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        # Supporter: identifiant | username | email
        identifiant = (
            attrs.get('identifiant')
            or attrs.get('username')
            or attrs.get('email')
            or ''
        )
        identifiant = str(identifiant).strip()
        password = attrs.get('password')
        
        if identifiant and password:
            username = identifiant
            # Si c'est un email explicite ou un identifiant contenant '@', mapper vers username
            is_email = bool(attrs.get('email')) or ('@' in str(identifiant))
            if is_email:
                try:
                    utilisateur = Utilisateur.objects.get(email__iexact=identifiant)
                    username = utilisateur.username
                except Utilisateur.DoesNotExist:
                    raise serializers.ValidationError(
                        {'detail': _('Identifiants invalides.')}, code='authorization'
                    )
            user = authenticate(
                request=self.context.get('request'),
                username=username,
                password=password
            )
            if not user:
                raise serializers.ValidationError(
                    {'detail': _('Identifiants invalides.')}, code='authorization'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    {'detail': _('Ce compte est désactivé.')}, code='authorization'
                )
            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                {'detail': _('Doit inclure "username" ou "email" et "password".')},
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