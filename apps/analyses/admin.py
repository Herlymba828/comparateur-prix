from django.contrib import admin
from .models import AnalysePrix, RapportAnalyse, IndicateurPerformance, CacheAnalyse, AnalysisResult, PriceAggregate

@admin.register(AnalysePrix)
class AnalysePrixAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_analyse', 'utilisateur', 'date_creation', 'date_debut_periode', 'date_fin_periode')
    list_filter = ('type_analyse', 'date_creation', 'utilisateur')
    search_fields = ('titre', 'description')
    readonly_fields = ('date_creation', 'date_maj')
    date_hierarchy = 'date_creation'

@admin.register(RapportAnalyse)
class RapportAnalyseAdmin(admin.ModelAdmin):
    list_display = ('analyse', 'format_rapport', 'statut', 'date_generation')
    list_filter = ('format_rapport', 'statut', 'date_generation')
    readonly_fields = ('date_generation',)

@admin.register(IndicateurPerformance)
class IndicateurPerformanceAdmin(admin.ModelAdmin):
    list_display = ('nom', 'valeur_actuelle', 'valeur_cible', 'unite', 'tendance', 'date_calcul')
    list_editable = ('valeur_cible',)
    readonly_fields = ('date_calcul',)

@admin.register(CacheAnalyse)
class CacheAnalyseAdmin(admin.ModelAdmin):
    list_display = ('cle_cache', 'date_creation', 'date_expiration')
    readonly_fields = ('date_creation',)
    list_filter = ('date_expiration',)

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = ('type', 'nom', 'produit', 'categorie', 'ville', 'region', 'calcule_le')
    list_filter = ('type', 'calcule_le')
    search_fields = ('nom',)
    readonly_fields = ('calcule_le',)

@admin.register(PriceAggregate)
class PriceAggregateAdmin(admin.ModelAdmin):
    list_display = ('produit', 'categorie', 'ville', 'region', 'fenetre_debut', 'fenetre_fin', 'prix_moyen', 'echantillons')
    list_filter = ('fenetre_debut', 'fenetre_fin')
    readonly_fields = ('calcule_le',)