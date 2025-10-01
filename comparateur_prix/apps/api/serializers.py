# Placeholder serializers for the API package (shared types can be added here later)
from rest_framework import serializers


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()


class ProductSearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    nom = serializers.CharField()
    marque = serializers.CharField(allow_blank=True, required=False)
    categorie_id = serializers.IntegerField()
    categorie_nom = serializers.CharField()
    min_prix = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    devise = serializers.CharField(allow_null=True)


class AutocompleteResultSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    label = serializers.CharField()
