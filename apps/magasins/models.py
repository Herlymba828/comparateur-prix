from django.db import models
from django.utils.text import slugify


class Region(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = 'Région'
        verbose_name_plural = 'Régions'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Ville(models.Model):
    nom = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name='villes')

    class Meta:
        verbose_name = 'Ville'
        verbose_name_plural = 'Villes'
        unique_together = ('nom', 'region')
        indexes = [
            models.Index(fields=['region', 'nom']),
        ]
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.region})"


class Magasin(models.Model):
    CHOIX_TYPE = (
        ('supermarche', 'Supermarché'),
        ('marche', 'Marché'),
        ('boutique', 'Boutique'),
        ('en_ligne', 'En ligne'),
    )

    nom = models.CharField(max_length=200)
    # Slug unique globalement pour simplicité; index déjà défini plus bas
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    type = models.CharField(max_length=20, choices=CHOIX_TYPE)
    # Nouveau alias logique pour répondre aux specs: type_magasin
    type_magasin = models.CharField(max_length=20, choices=CHOIX_TYPE, blank=True)
    adresse = models.CharField(max_length=255, blank=True)
    ville = models.ForeignKey(Ville, on_delete=models.PROTECT, related_name='magasins')
    # Nouvelles métadonnées de localisation/zone (textuelles)
    localisation = models.CharField(max_length=120, blank=True, default='')
    zone = models.CharField(max_length=60, blank=True, default='')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    formatted_address = models.CharField(max_length=255, blank=True, default='')
    place_id = models.CharField(max_length=100, blank=True, default='')
    geocoded_at = models.DateTimeField(blank=True, null=True)
    geocoding_provider = models.CharField(max_length=30, blank=True, default='')
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Magasin'
        verbose_name_plural = 'Magasins'
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['ville']),
            models.Index(fields=['zone']),
        ]
        ordering = ['nom']

    def __str__(self):
        return self.nom

    def nettoyer(self):
        # Valide la lat/long si fournies
        if self.latitude is not None and (self.latitude < -90 or self.latitude > 90):
            from django.core.exceptions import ValidationError
            raise ValidationError({'latitude': 'La latitude doit être comprise entre -90 et 90.'})
        if self.longitude is not None and (self.longitude < -180 or self.longitude > 180):
            from django.core.exceptions import ValidationError
            raise ValidationError({'longitude': 'La longitude doit être comprise entre -180 et 180.'})

    def sauvegarder(self, *args, **kwargs):
        # Génère un slug stable basé sur le nom si absent
        if not self.slug:
            base = slugify(self.nom)
            self.slug = base[:220]
        super().save(*args, **kwargs)
