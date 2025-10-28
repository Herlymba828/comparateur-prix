from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import Utilisateur, ProfilUtilisateur, Abonnement, HistoriqueConnexion, HistoriqueRemises


@admin.register(Utilisateur)
class UtilisateurAdmin(DjangoUserAdmin):
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff',
        'type_utilisateur', 'est_verifie', 'date_creation', 'derniere_connexion',
    )
    list_filter = (
        'is_active', 'is_staff', 'is_superuser', 'type_utilisateur', 'est_verifie',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_creation',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'telephone')}),
        ('Profil', {'fields': ('type_utilisateur', 'date_naissance', 'code_postal', 'ville')}),
        ('Géolocalisation', {'fields': ('latitude', 'longitude')}),
        ('Statut', {'fields': ('is_active', 'est_verifie')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_active', 'is_staff', 'is_superuser')
        }),
    )


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'rayon_recherche_km', 'notifications_actives', 'newsletter_abonnement')
    search_fields = ('utilisateur__username', 'utilisateur__email')


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_abonnement', 'date_debut', 'date_fin', 'est_actif')
    list_filter = ('type_abonnement', 'est_actif')
    search_fields = ('utilisateur__username', 'utilisateur__email')


@admin.register(HistoriqueConnexion)
class HistoriqueConnexionAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date_connexion', 'ip_address', 'reussi')
    list_filter = ('reussi', 'date_connexion')
    search_fields = ('utilisateur__username', 'utilisateur__email', 'ip_address')


@admin.register(HistoriqueRemises)
class HistoriqueRemisesAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'produit', 'pourcentage_remise', 'montant_economise', 'date_application', 'type_remise')
    list_filter = ('type_remise', 'date_application')
    search_fields = ('utilisateur__username', 'utilisateur__email', 'produit__nom')
