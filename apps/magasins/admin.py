from django.contrib import admin
from .models import Region, Ville, Magasin


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("nom",)
    search_fields = ("nom",)


@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ("nom", "region")
    list_filter = ("region",)
    search_fields = ("nom",)


@admin.register(Magasin)
class MagasinAdmin(admin.ModelAdmin):
    list_display = ("nom", "type", "ville", "actif")
    list_filter = ("type", "actif", "ville")
    search_fields = ("nom", "adresse")
