from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid

class Utilisateur(AbstractUser):
    """Modèle utilisateur personnalisé avec système de fidélité"""
    
    class TypesUtilisateur(models.TextChoices):
        PARTICULIER = 'particulier', _('Particulier')
        PROFESSIONNEL = 'professionnel', _('Professionnel')
        ADMINISTRATEUR = 'administrateur', _('Administrateur')
    
    # Champs de base
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    type_utilisateur = models.CharField(
        max_length=20,
        choices=TypesUtilisateur.choices,
        default=TypesUtilisateur.PARTICULIER
    )
    telephone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')]
    )
    date_naissance = models.DateField(null=True, blank=True)
    code_postal = models.CharField(max_length=10, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    # Géolocalisation (dernière position connue)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_at = models.DateTimeField(null=True, blank=True)
    
    # Champs d'audit
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    derniere_connexion = models.DateTimeField(null=True, blank=True)
    est_verifie = models.BooleanField(default=False)
    
    # Champs pour les professionnels
    nom_entreprise = models.CharField(max_length=200, blank=True)
    siret = models.CharField(max_length=14, blank=True)
    
    # Système de fidélité
    points_fidelite = models.PositiveIntegerField(default=0)
    niveau_fidelite = models.PositiveSmallIntegerField(default=1, validators=[
        MinValueValidator(1), MaxValueValidator(5)
    ])
    date_dernier_achat = models.DateTimeField(null=True, blank=True)
    total_achats = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    nombre_commandes = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'utilisateurs'
        verbose_name = _('Utilisateur')
        verbose_name_plural = _('Utilisateurs')
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['type_utilisateur']),
            models.Index(fields=['date_creation']),
            models.Index(fields=['code_postal', 'ville']),
            models.Index(fields=['points_fidelite']),
            models.Index(fields=['niveau_fidelite']),
            models.Index(fields=['latitude', 'longitude']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.get_type_utilisateur_display()})"
    
    @property
    def age(self):
        if self.date_naissance:
            today = timezone.now().date()
            return today.year - self.date_naissance.year - (
                (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
            )
        return None
    
    @property
    def est_nouveau(self):
        return self.date_creation > timezone.now() - timedelta(days=7)
    
    @property
    def est_client_fidele(self):
        """Détermine si l'utilisateur est un client fidèle"""
        return self.niveau_fidelite >= 3 and self.nombre_commandes >= 5
    
    @property
    def pourcentage_remise_fidelite(self):
        """Retourne le pourcentage de remise selon le niveau de fidélité"""
        remises = {1: 0, 2: 2, 3: 5, 4: 10, 5: 15}
        return remises.get(self.niveau_fidelite, 0)
    
    def mettre_a_jour_connexion(self):
        """Met à jour la date de dernière connexion"""
        self.derniere_connexion = timezone.now()
        self.save(update_fields=['derniere_connexion'])
    
    def ajouter_points_fidelite(self, points, montant_achat=0):
        """Ajoute des points de fidélité et met à jour le niveau"""
        self.points_fidelite += points
        if montant_achat > 0:
            self.total_achats += montant_achat
            self.nombre_commandes += 1
            self.date_dernier_achat = timezone.now()
        
        # Mettre à jour le niveau de fidélité
        self._mettre_a_jour_niveau_fidelite()
        self.save()
    
    def _mettre_a_jour_niveau_fidelite(self):
        """Met à jour le niveau de fidélité selon le total des achats"""
        if self.total_achats >= 1000:
            self.niveau_fidelite = 5
        elif self.total_achats >= 500:
            self.niveau_fidelite = 4
        elif self.total_achats >= 200:
            self.niveau_fidelite = 3
        elif self.total_achats >= 50:
            self.niveau_fidelite = 2
        else:
            self.niveau_fidelite = 1
    
    def appliquer_remise_fidelite(self, prix_original, categorie_produit=None):
        """
        Applique la remise fidélité au prix
        
        Args:
            prix_original: Prix original du produit
            categorie_produit: Catégorie du produit pour remise spécifique
        
        Returns:
            tuple: (prix_remise, montant_remise)
        """
        remise_base = self.pourcentage_remise_fidelite
        
        # Remise supplémentaire pour certaines catégories
        remise_categorie = self._get_remise_categorie(categorie_produit)
        
        remise_totale = remise_base + remise_categorie
        montant_remise = (prix_original * remise_totale) / 100
        prix_remise = prix_original - montant_remise
        
        return prix_remise, montant_remise
    
    def _get_remise_categorie(self, categorie_produit):
        """Retourne la remise supplémentaire pour une catégorie"""
        if not categorie_produit or self.niveau_fidelite < 3:
            return 0
        
        # Catégories avec remise supplémentaire pour clients fidèles
        categories_privilegiees = {
            'bio': 3,
            'premium': 5,
            'local': 2,
            'durable': 2
        }
        
        nom_categorie = categorie_produit.nom.lower() if hasattr(categorie_produit, 'nom') else str(categorie_produit).lower()
        
        for mot_cle, remise in categories_privilegiees.items():
            if mot_cle in nom_categorie:
                return remise
        
        return 0

class ProfilUtilisateur(models.Model):
    """Profil étendu pour les utilisateurs"""
    
    utilisateur = models.OneToOneField(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name='profil'
    )
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/', 
        blank=True, 
        null=True
    )
    bio = models.TextField(blank=True, max_length=500)
    site_web = models.URLField(blank=True)
    notifications_actives = models.BooleanField(default=True)
    newsletter_abonnement = models.BooleanField(default=False)
    
    # Préférences utilisateur
    preferences_recherche = models.JSONField(default=dict)
    rayon_recherche_km = models.PositiveIntegerField(default=10)
    magasins_preferes = models.ManyToManyField(
        'magasins.Magasin', 
        blank=True,
        related_name='utilisateurs_preferant'
    )
    
    # Préférences de remise
    alertes_remises = models.BooleanField(default=True)
    categories_preferees_remises = models.ManyToManyField(
        'produits.Categorie',
        blank=True,
        related_name='utilisateurs_interesses'
    )
    
    class Meta:
        db_table = 'profils_utilisateur'
        verbose_name = _('Profil utilisateur')
        verbose_name_plural = _('Profils utilisateur')
    
    def __str__(self):
        return f"Profil de {self.utilisateur.username}"

class HistoriqueConnexion(models.Model):
    """Historique des connexions utilisateur"""
    
    utilisateur = models.ForeignKey(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name='historique_connexions'
    )
    date_connexion = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    reussi = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'historique_connexions'
        verbose_name = _('Historique de connexion')
        verbose_name_plural = _('Historiques de connexion')
        ordering = ['-date_connexion']
        indexes = [
            models.Index(fields=['utilisateur', 'date_connexion']),
        ]
    
    def __str__(self):
        status = "réussie" if self.reussi else "échouée"
        return f"Connexion {status} de {self.utilisateur} le {self.date_connexion}"

class Abonnement(models.Model):
    """Système d'abonnement pour les utilisateurs"""
    
    class TypeAbonnement(models.TextChoices):
        GRATUIT = 'gratuit', _('Gratuit')
        PREMIUM = 'premium', _('Premium')
        PROFESSIONNEL = 'professionnel', _('Professionnel')
    
    utilisateur = models.OneToOneField(
        Utilisateur, 
        on_delete=models.CASCADE, 
        related_name='abonnement'
    )
    type_abonnement = models.CharField(
        max_length=20,
        choices=TypeAbonnement.choices,
        default=TypeAbonnement.GRATUIT
    )
    date_debut = models.DateTimeField(auto_now_add=True)
    date_fin = models.DateTimeField()
    est_actif = models.BooleanField(default=True)
    
    # Avantages de l'abonnement
    remise_supplementaire = models.PositiveIntegerField(default=0)  # en pourcentage
    livraison_gratuite = models.BooleanField(default=False)
    acces_prioritaire = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'abonnements'
        verbose_name = _('Abonnement')
        verbose_name_plural = _('Abonnements')
    
    def __str__(self):
        return f"Abonnement {self.type_abonnement} - {self.utilisateur}"
    
    @property
    def est_valide(self):
        return self.est_actif and self.date_fin > timezone.now()
    
    def get_remise_totale(self, utilisateur):
        """Retourne la remise totale (fidélité + abonnement)"""
        return utilisateur.pourcentage_remise_fidelite + self.remise_supplementaire

class HistoriqueRemises(models.Model):
    """Historique des remises appliquées aux utilisateurs"""
    
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.CASCADE,
        related_name='historique_remises'
    )
    produit = models.ForeignKey(
        'produits.Produit',
        on_delete=models.CASCADE,
        related_name='remises_appliquees'
    )
    prix_original = models.DecimalField(max_digits=10, decimal_places=2)
    prix_remise = models.DecimalField(max_digits=10, decimal_places=2)
    pourcentage_remise = models.DecimalField(max_digits=5, decimal_places=2)
    montant_economise = models.DecimalField(max_digits=10, decimal_places=2)
    date_application = models.DateTimeField(auto_now_add=True)
    type_remise = models.CharField(max_length=20, choices=[
        ('fidelite', 'Fidélité'),
        ('abonnement', 'Abonnement'),
        ('promotion', 'Promotion'),
        ('combinee', 'Combinée')
    ])
    
    class Meta:
        db_table = 'historique_remises'
        verbose_name = _('Historique de remise')
        verbose_name_plural = _('Historiques de remises')
        ordering = ['-date_application']
        indexes = [
            models.Index(fields=['utilisateur', 'date_application']),
            models.Index(fields=['produit', 'date_application']),
        ]
    
    def __str__(self):
        return f"Remise de {self.pourcentage_remise}% pour {self.utilisateur} sur {self.produit}"