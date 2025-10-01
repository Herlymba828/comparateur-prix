from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

# === MODÈLES DE BASE ===
class Categorie(models.Model):
    nom = models.CharField(_("Nom"), max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sous_categories')
    image = models.ImageField(_("Image"), upload_to='categories/', null=True, blank=True)
    ordre = models.PositiveIntegerField(_("Ordre d'affichage"), default=0)
    date_creation = models.DateTimeField(_("Date de création"), auto_now_add=True)
    date_modification = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    class Meta:
        verbose_name = _("Catégorie")
        verbose_name_plural = _("Catégories")
        ordering = ['ordre', 'nom']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
        ]
    
    def __str__(self):
        return self.nom
    
    def get_niveau(self):
        niveau = 0
        parent = self.parent
        while parent is not None:
            niveau += 1
            parent = parent.parent
        return niveau
    
    @property
    def est_racine(self):
        return self.parent is None
    
    def get_chemin(self):
        chemin = [self.nom]
        parent = self.parent
        while parent is not None:
            chemin.insert(0, parent.nom)
            parent = parent.parent
        return ' > '.join(chemin)

class Marque(models.Model):
    nom = models.CharField(_("Nom"), max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), max_length=100, unique=True)
    description = models.TextField(_("Description"), blank=True)
    logo = models.ImageField(_("Logo"), upload_to='marques/', null=True, blank=True)
    site_web = models.URLField(_("Site web"), blank=True)
    pays_origine = models.CharField(_("Pays d'origine"), max_length=50, blank=True)
    date_creation = models.DateTimeField(_("Date de création"), auto_now_add=True)
    date_modification = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    class Meta:
        verbose_name = _("Marque")
        verbose_name_plural = _("Marques")
        ordering = ['nom']
        indexes = [
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.nom

class UniteMesure(models.Model):
    nom = models.CharField(_("Nom"), max_length=20, unique=True)
    symbole = models.CharField(_("Symbole"), max_length=10, unique=True)
    description = models.CharField(_("Description"), max_length=100, blank=True)
    
    class Meta:
        verbose_name = _("Unité de mesure")
        verbose_name_plural = _("Unités de mesure")
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.symbole})"

class Produit(models.Model):
    # Identifiants
    code_barre = models.CharField(_("Code-barres"), max_length=20, unique=True, db_index=True)
    nom = models.CharField(_("Nom du produit"), max_length=200)
    slug = models.SlugField(_("Slug"), max_length=200, unique=True)
    
    # Classification
    categorie = models.ForeignKey(Categorie, on_delete=models.PROTECT, related_name='produits')
    marque = models.ForeignKey(Marque, on_delete=models.PROTECT, related_name='produits', null=True, blank=True)
    
    # Caractéristiques physiques
    poids = models.DecimalField(_("Poids"), max_digits=8, decimal_places=3, null=True, blank=True)
    volume = models.DecimalField(_("Volume"), max_digits=8, decimal_places=3, null=True, blank=True)
    unite_mesure = models.ForeignKey(UniteMesure, on_delete=models.PROTECT)
    quantite_unite = models.DecimalField(_("Quantité par unité"), max_digits=8, decimal_places=3, default=1, validators=[MinValueValidator(0.001)])
    
    # Informations nutritionnelles
    energie_kcal = models.PositiveIntegerField(_("Énergie (kcal)"), null=True, blank=True)
    proteines_g = models.DecimalField(_("Protéines (g)"), max_digits=5, decimal_places=2, null=True, blank=True)
    glucides_g = models.DecimalField(_("Glucides (g)"), max_digits=5, decimal_places=2, null=True, blank=True)
    lipides_g = models.DecimalField(_("Lipides (g)"), max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Images
    image_principale = models.ImageField(_("Image principale"), upload_to='produits/', null=True, blank=True)
    images_secondaires = models.JSONField(_("Images secondaires"), default=list, blank=True)
    
    # Métadonnées
    est_actif = models.BooleanField(_("Est actif"), default=True)
    date_creation = models.DateTimeField(_("Date de création"), auto_now_add=True)
    date_modification = models.DateTimeField(_("Date de modification"), auto_now=True)
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Créé par"))
    
    class Meta:
        verbose_name = _("Produit")
        verbose_name_plural = _("Produits")
        ordering = ['nom']
        indexes = [
            models.Index(fields=['code_barre']),
            models.Index(fields=['slug']),
            models.Index(fields=['categorie']),
            models.Index(fields=['marque']),
            models.Index(fields=['est_actif']),
        ]
    
    def __str__(self):
        return f"{self.nom} ({self.code_barre})"
    
    # Méthodes statistiques UNIFIÉES
    def get_statistiques_prix(self):
        from django.db.models import Min, Max, Avg, Count
        return self.prix_set.filter(est_disponible=True).aggregate(
            min=Min('prix_actuel'),
            max=Max('prix_actuel'),
            avg=Avg('prix_actuel'),
            count=Count('id')
        )
    
    @property
    def prix_min(self):
        stats = self.get_statistiques_prix()
        return stats['min']
    
    @property
    def prix_max(self):
        stats = self.get_statistiques_prix()
        return stats['max']
    
    @property
    def prix_moyen(self):
        stats = self.get_statistiques_prix()
        return stats['avg']
    
    @property
    def nombre_magasins(self):
        stats = self.get_statistiques_prix()
        return stats['count']

# === MODÈLES PRIX PRINCIPAUX ===
class Prix(models.Model):
    """Modèle principal pour les prix - REMPLACE Offre"""
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='prix')
    magasin = models.ForeignKey('magasins.Magasin', on_delete=models.CASCADE, related_name='prix')
    
    prix_actuel = models.DecimalField(_("Prix actuel"), max_digits=8, decimal_places=2, validators=[MinValueValidator(0.01)])
    prix_origine = models.DecimalField(_("Prix d'origine"), max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Métriques dérivées (remplace Offre.cheapness_score etc.)
    cheapness_score = models.FloatField(null=True, blank=True)
    popularity_count = models.IntegerField(default=0)
    recommendation_score = models.FloatField(null=True, blank=True)
    
    # Champs existants...
    est_promotion = models.BooleanField(_("Est en promotion"), default=False)
    est_disponible = models.BooleanField(_("Est disponible"), default=True)
    quantite_stock = models.PositiveIntegerField(_("Quantité en stock"), null=True, blank=True)
    niveau_stock = models.CharField(_("Niveau de stock"), max_length=20, default='disponible')
    source_prix = models.CharField(_("Source du prix"), max_length=50, default='scraping')
    confiance_prix = models.DecimalField(_("Niveau de confiance"), max_digits=3, decimal_places=2, default=1.0)
    date_creation = models.DateTimeField(_("Date de création"), auto_now_add=True)
    date_modification = models.DateTimeField(_("Date de modification"), auto_now=True)
    
    class Meta:
        verbose_name = _("Prix")
        verbose_name_plural = _("Prix")
        unique_together = [('produit', 'magasin')]
        ordering = ['-date_modification']
        indexes = [
            models.Index(fields=['produit', 'magasin']),
            models.Index(fields=['prix_actuel']),
        ]

    def __str__(self) -> str:
        return f"{self.produit.nom} @ {self.magasin_id} = {self.prix_actuel}"

    @property
    def pourcentage_promotion(self):
        if self.est_promotion and self.prix_origine and self.prix_origine > 0:
            try:
                return (self.prix_origine - self.prix_actuel) * 100 / self.prix_origine
            except Exception:
                return 0
        return 0

    @property
    def est_promotion_valide(self):
        return bool(self.est_promotion)

    @property
    def prix_par_unite(self):
        try:
            if self.produit and self.produit.quantite_unite:
                return self.prix_actuel / self.produit.quantite_unite
        except Exception:
            pass
        return None

    def save(self, *args, **kwargs):
        # Déterminer automatiquement la promotion si prix_origine > prix_actuel
        if self.prix_origine and self.prix_origine > self.prix_actuel:
            self.est_promotion = True
class HistoriquePrix(models.Model):
    """Historique des changements d'un enregistrement Prix (fusion depuis app prix)."""
    prix = models.ForeignKey(Prix, on_delete=models.CASCADE, related_name='historique', verbose_name=("Prix"))
    ancien_prix = models.DecimalField(("Ancien prix"), max_digits=10, decimal_places=2)
    nouveau_prix = models.DecimalField(("Nouveau prix"), max_digits=10, decimal_places=2)
    variation = models.DecimalField(("Variation"), max_digits=10, decimal_places=2)
    pourcentage_variation = models.DecimalField(("Pourcentage de variation"), max_digits=6, decimal_places=2)
    raison = models.CharField(
        ("Raison du changement"),
        max_length=20,
        choices=[
            ('promotion', ("Promotion")),
            ('fin_promotion', ("Fin de promotion")),
            ('augmentation', ("Augmentation de prix")),
            ('reduction', ("Réduction de prix")),
            ('correction', ("Correction")),
            ('a_jour', ("Mise à jour")),
        ],
        default='a_jour',
    )
    date_changement = models.DateTimeField(("Date du changement"), auto_now_add=True)
    
    class Meta:
        verbose_name = ("Historique des prix")
        verbose_name_plural = ("Historique des prix")
        ordering = ['-date_changement']

class AvisProduit(models.Model):
    NOTE_CHOICES = [
        (1, '1 - Très mauvais'),
        (2, '2 - Mauvais'),
        (3, '3 - Moyen'),
        (4, '4 - Bon'),
        (5, '5 - Excellent'),
    ]
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='avis', verbose_name=("Produit"))
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='avis_produits', verbose_name=("Utilisateur"))
    note = models.PositiveSmallIntegerField(("Note"), choices=NOTE_CHOICES, validators=[MinValueValidator(1), MaxValueValidator(5)])
    titre = models.CharField(("Titre de l'avis"), max_length=100)
    commentaire = models.TextField(("Commentaire"), blank=True)
    est_verifie = models.BooleanField(("Avis vérifié"), default=False)
    date_creation = models.DateTimeField(("Date de création"), auto_now_add=True)
    date_modification = models.DateTimeField(("Date de modification"), auto_now=True)
    
    class Meta:
        verbose_name = ("Avis produit")
        verbose_name_plural = ("Avis produits")
        unique_together = [('produit', 'utilisateur')]
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['produit', 'note']),
            models.Index(fields=['utilisateur']),
        ]
    
    def __str__(self):
        return f"Avis de {self.utilisateur} sur {self.produit}"

class CaracteristiqueProduit(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='caracteristiques', verbose_name=("Produit"))
    nom = models.CharField(("Nom de la caractéristique"), max_length=100)
    valeur = models.CharField(("Valeur"), max_length=200)
    ordre = models.PositiveIntegerField(("Ordre d'affichage"), default=0)
    
    class Meta:
        verbose_name = ("Caractéristique produit")
        verbose_name_plural = ("Caractéristiques produits")
        ordering = ['ordre', 'nom']
        unique_together = [('produit', 'nom')]
    
    def __str__(self):
        return f"{self.nom}: {self.valeur}"

class HistoriquePrixProduit(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='historique_prix', verbose_name=("Produit"))
    date = models.DateField(("Date"))
    prix_moyen = models.DecimalField(("Prix moyen"), max_digits=10, decimal_places=2)
    prix_min = models.DecimalField(("Prix minimum"), max_digits=10, decimal_places=2)
    prix_max = models.DecimalField(("Prix maximum"), max_digits=10, decimal_places=2)
    nombre_magasins = models.PositiveIntegerField(("Nombre de magasins"))
    class Meta:
        verbose_name = ("Historique prix produit")
        verbose_name_plural = ("Historique prix produits")
        unique_together = [('produit', 'date')]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['produit', 'date']),
        ]
    
    def __str__(self):
        return f"Historique {self.produit} - {self.date}"

# === Modèles réintroduits depuis l'app prix ===
class AlertePrix(models.Model):
    FREQUENCE_CHOICES = [
        ('quotidienne', 'Quotidienne'),
        ('hebdomadaire', 'Hebdomadaire'),
        ('mensuelle', 'Mensuelle'),
    ]
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alertes_prix')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='alertes_prix')
    magasins = models.ManyToManyField('magasins.Magasin', related_name='alertes_prix', blank=True)
    prix_souhaite = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pourcentage_reduction = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    est_active = models.BooleanField(default=True)
    frequence_verification = models.CharField(max_length=20, choices=FREQUENCE_CHOICES, default='quotidienne')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_derniere_alerte = models.DateTimeField(null=True, blank=True)
    nombre_alertes_envoyees = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Alerte de prix"
        verbose_name_plural = "Alertes de prix"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'produit']),
            models.Index(fields=['est_active']),
        ]

    def __str__(self):
        return f"Alerte {self.utilisateur} -> {self.produit}"

    @property
    def prix_actuel_minimum(self):
        from django.db.models import Min
        qs = self.produit.prix.filter(est_disponible=True)
        if self.magasins.exists():
            qs = qs.filter(magasin__in=self.magasins.all())
        agg = qs.aggregate(min=Min('prix_actuel'))
        return agg['min']

    @property
    def est_seuil_atteint(self):
        min_prix = self.prix_actuel_minimum
        if min_prix is None:
            return False
        if self.prix_souhaite is not None:
            return min_prix <= self.prix_souhaite
        if self.pourcentage_reduction is not None:
            from django.db.models import Min
            ref = self.produit.prix.filter(est_disponible=True).aggregate(m=Min('prix_actuel'))['m']
            if ref:
                seuil = ref * (1 - (self.pourcentage_reduction / 100))
                return min_prix <= seuil
        return False


class SuggestionPrix(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('approuve', 'Approuvé'),
        ('rejete', 'Rejeté'),
    ]
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suggestions_prix')
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='suggestions_prix')
    magasin = models.ForeignKey('magasins.Magasin', on_delete=models.CASCADE, related_name='suggestions_prix')
    prix_suggere = models.DecimalField(max_digits=10, decimal_places=2)
    date_observation = models.DateTimeField()
    photo_preuve = models.ImageField(upload_to='suggestions_preuve/', null=True, blank=True)
    commentaire = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    verifie_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='suggestions_verifiees')
    date_verification = models.DateTimeField(null=True, blank=True)
    raison_rejet = models.CharField(max_length=200, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Suggestion de prix"
        verbose_name_plural = "Suggestions de prix"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['produit', 'magasin']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return f"Suggestion {self.utilisateur} -> {self.produit} @ {self.magasin}"


class ComparaisonPrix(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='comparaisons')
    date_comparaison = models.DateTimeField(auto_now_add=True)
    prix_minimum = models.DecimalField(max_digits=10, decimal_places=2)
    prix_maximum = models.DecimalField(max_digits=10, decimal_places=2)
    prix_moyen = models.DecimalField(max_digits=10, decimal_places=2)
    nombre_magasins = models.PositiveIntegerField()
    ecart_type = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    coefficient_variation = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    magasin_prix_min = models.ForeignKey('magasins.Magasin', on_delete=models.SET_NULL, null=True, related_name='comparaisons_prix_min')
    magasin_prix_max = models.ForeignKey('magasins.Magasin', on_delete=models.SET_NULL, null=True, related_name='comparaisons_prix_max')

    class Meta:
        verbose_name = "Comparaison de prix"
        verbose_name_plural = "Comparaisons de prix"
        ordering = ['-date_comparaison']

    def __str__(self):
        return f"Comparaison {self.produit} ({self.date_comparaison.date()})"


class Offre(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name='offres')
    magasin = models.ForeignKey('magasins.Magasin', on_delete=models.CASCADE, related_name='offres')
    prix_actuel = models.DecimalField(max_digits=10, decimal_places=2)
    prix_origine = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    est_promotion = models.BooleanField(default=False)
    cheapness_score = models.FloatField(null=True, blank=True)
    popularity_count = models.IntegerField(default=0)
    recommendation_score = models.FloatField(null=True, blank=True)
    source = models.CharField(max_length=30, default='scraping')
    date_observation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Offre"
        verbose_name_plural = "Offres"
        indexes = [
            models.Index(fields=['produit', 'magasin']),
            models.Index(fields=['est_promotion']),
        ]

    def __str__(self):
        return f"Offre {self.produit} @ {self.magasin}"


class HomologationProduit(models.Model):
    nom = models.CharField(max_length=255)
    format = models.CharField(max_length=120, blank=True)
    marque = models.CharField(max_length=120, blank=True)
    categorie = models.CharField(max_length=120, default='Non classé')
    sous_categorie = models.CharField(max_length=120, blank=True)
    reference_titre = models.CharField(max_length=255, blank=True)
    reference_numero = models.CharField(max_length=120, blank=True)
    reference_url = models.CharField(max_length=200, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Produit homologué (référence)"
        verbose_name_plural = "Produits homologués (référence)"
        indexes = [
            models.Index(fields=['nom', 'marque']),
            models.Index(fields=['categorie', 'sous_categorie']),
        ]

    def __str__(self):
        return f"{self.nom} ({self.format})"


class PrixHomologue(models.Model):
    produit = models.ForeignKey(HomologationProduit, on_delete=models.CASCADE, related_name='prix_homologues')
    date_publication = models.DateField(null=True, blank=True)
    unite = models.CharField(max_length=60, blank=True)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    prix_detail = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prix_par_kilo = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prix_gros = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prix_demi_gros = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    periode_debut = models.DateField(null=True, blank=True)
    periode_fin = models.DateField(null=True, blank=True)
    localisation = models.CharField(max_length=60, blank=True, default='')
    source = models.CharField(max_length=60, blank=True, default='')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Prix homologué"
        verbose_name_plural = "Prix homologués"
        ordering = ['-date_publication', '-date_creation']
        indexes = [
            models.Index(fields=['produit', 'date_publication']),
            models.Index(fields=['localisation']),
        ]

    def __str__(self):
        return f"PH {self.produit} {self.date_publication} {self.unite} {self.prix_unitaire}"