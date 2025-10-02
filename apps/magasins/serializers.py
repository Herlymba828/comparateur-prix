from rest_framework import serializers
from .models import Magasin, Ville, Region


class SerialiseurRegion(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'nom']


class SerialiseurVille(serializers.ModelSerializer):
    region = SerialiseurRegion(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(source='region', queryset=Region.objects.all(), write_only=True)

    class Meta:
        model = Ville
        fields = ['id', 'nom', 'region', 'region_id']


class SerialiseurMagasin(serializers.ModelSerializer):
    ville = SerialiseurVille(read_only=True)
    ville_id = serializers.PrimaryKeyRelatedField(source='ville', queryset=Ville.objects.all(), write_only=True)
    region = serializers.SerializerMethodField(read_only=True)
    distance_km = serializers.SerializerMethodField(read_only=True)
    duration_min = serializers.SerializerMethodField(read_only=True)
    score = serializers.SerializerMethodField(read_only=True)
    rating = serializers.SerializerMethodField(read_only=True)
    avg_price = serializers.SerializerMethodField(read_only=True)

    def get_region(self, obj):
        if obj.ville_id and getattr(obj.ville, 'region_id', None):
            return {'id': obj.ville.region.id, 'nom': obj.ville.region.nom}
        return None

    class Meta:
        model = Magasin
        fields = ['id', 'nom', 'slug', 'type', 'adresse', 'ville', 'ville_id', 'region', 'latitude', 'longitude', 'actif', 'date_creation', 'date_modification', 'distance_km', 'duration_min', 'score', 'rating', 'avg_price']
        read_only_fields = ['slug', 'date_creation', 'date_modification']

    def valider_nom(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Le nom du magasin est requis.")
        return value.strip()

    def valider(self, attrs):
        latitude = attrs.get('latitude')
        longitude = attrs.get('longitude')
        if latitude is not None and (latitude < -90 or latitude > 90):
            raise serializers.ValidationError({'latitude': 'La latitude doit être comprise entre -90 et 90.'})
        if longitude is not None and (longitude < -180 or longitude > 180):
            raise serializers.ValidationError({'longitude': 'La longitude doit être comprise entre -180 et 180.'})
        return attrs

    def get_distance_km(self, obj):
        val = getattr(obj, 'distance_km', None)
        return round(val, 3) if isinstance(val, (int, float)) else val

    def get_duration_min(self, obj):
        val = getattr(obj, 'duration_min', None)
        return round(val, 1) if isinstance(val, (int, float)) else val

    def get_score(self, obj):
        val = getattr(obj, 'score', None)
        return round(val, 3) if isinstance(val, (int, float)) else val

    def get_rating(self, obj):
        val = getattr(obj, 'rating', None)
        return round(val, 2) if isinstance(val, (int, float)) else val

    def get_avg_price(self, obj):
        val = getattr(obj, 'avg_price', None)
        return round(val, 2) if isinstance(val, (int, float)) else val

# Compatibility aliases for existing imports elsewhere in the project
RegionSerializer = SerialiseurRegion
VilleSerializer = SerialiseurVille
MagasinSerializer = SerialiseurMagasin
