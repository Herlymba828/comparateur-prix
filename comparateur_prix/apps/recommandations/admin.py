from django.contrib import admin
from .models import HistoriqueRecommandation, FeedbackRecommandation, ModeleML


@admin.register(HistoriqueRecommandation)
class HistoriqueRecommandationAdmin(admin.ModelAdmin):
    list_display = ['utilisateur', 'produit_recommande', 'algorithme_utilise', 'score_confiance', 'date_creation']
    list_filter = ['algorithme_utilise', 'date_creation']
    search_fields = ['utilisateur__username', 'produit_recommande__nom']
    readonly_fields = ['date_creation']
    date_hierarchy = 'date_creation'


@admin.register(FeedbackRecommandation)
class FeedbackRecommandationAdmin(admin.ModelAdmin):
    list_display = ['historique', 'note_utilisateur', 'aime', 'date_feedback']
    list_filter = ['aime', 'date_feedback']
    search_fields = ['historique__utilisateur__username', 'historique__produit_recommande__nom']
    readonly_fields = ['date_feedback']


@admin.register(ModeleML)
class ModeleMLAdmin(admin.ModelAdmin):
    list_display = ['nom', 'version', 'type_modele', 'precision', 'est_actif', 'date_entrainement']
    list_filter = ['type_modele', 'est_actif']
    readonly_fields = ['date_entrainement']
    list_editable = ['est_actif']