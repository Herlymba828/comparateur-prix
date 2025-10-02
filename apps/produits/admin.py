from django.contrib import admin
from .models import (
    Prix, HistoriquePrix, AlertePrix, SuggestionPrix, ComparaisonPrix, Offre, PrixHomologue,
    Categorie, Marque, UniteMesure, Produit, AvisProduit, CaracteristiqueProduit, HistoriquePrixProduit,
)

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code_barre', 'categorie', 'marque', 'est_actif']
    search_fields = ['nom', 'code_barre']
    list_filter = ['categorie', 'marque', 'est_actif']

@admin.register(Prix)
class PrixAdmin(admin.ModelAdmin):
    list_display = ['produit', 'magasin', 'prix_actuel', 'est_promotion', 'est_disponible', 'date_modification']
    list_filter = ['est_promotion', 'est_disponible', 'magasin']
    search_fields = ['produit__nom', 'magasin__nom']
    readonly_fields = ['date_creation', 'date_modification']
    autocomplete_fields = ['produit', 'magasin']


@admin.register(HistoriquePrix)
class HistoriquePrixAdmin(admin.ModelAdmin):
    list_display = ['prix', 'ancien_prix', 'nouveau_prix', 'variation', 'pourcentage_variation', 'date_changement']
    list_filter = ['date_changement']
    search_fields = ['prix__produit__nom', 'prix__magasin__nom']
    readonly_fields = ['date_changement']


@admin.register(AlertePrix)
class AlertePrixAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'produit', 'est_active', 'frequence_verification', 'date_creation']
    list_filter = ['est_active', 'frequence_verification', 'date_creation']
    search_fields = ['produit__nom', 'utilisateur__username']
    filter_horizontal = ['magasins']


@admin.register(SuggestionPrix)
class SuggestionPrixAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'produit', 'magasin', 'prix_suggere', 'statut', 'date_creation']
    list_filter = ['statut', 'date_creation']
    search_fields = ['produit__nom', 'magasin__nom', 'utilisateur__username']


@admin.register(ComparaisonPrix)
class ComparaisonPrixAdmin(admin.ModelAdmin):
    list_display = ['produit', 'date_comparaison', 'prix_minimum', 'prix_maximum', 'prix_moyen', 'nombre_magasins']
    list_filter = ['date_comparaison']
    search_fields = ['produit__nom']


@admin.register(Offre)
class OffreAdmin(admin.ModelAdmin):
    list_display = ['produit', 'magasin', 'prix_actuel', 'est_promotion', 'date_observation']
    search_fields = ['produit__nom', 'magasin__nom']


@admin.register(PrixHomologue)
class PrixHomologueAdmin(admin.ModelAdmin):
    list_display = ['date_publication', 'localisation', 'source']
    list_filter = ['date_publication', 'localisation']
    search_fields = ['localisation', 'source']