import django_filters as filters
from .models import Magasin, Ville, Region


class RegionFilter(filters.FilterSet):
    nom = filters.CharFilter(field_name="nom", lookup_expr="icontains")

    class Meta:
        model = Region
        fields = ["nom"]


class VilleFilter(filters.FilterSet):
    region = filters.NumberFilter(field_name="region__id")
    nom = filters.CharFilter(field_name="nom", lookup_expr="icontains")

    class Meta:
        model = Ville
        fields = ["region", "nom"]


class MagasinFilter(filters.FilterSet):
    ville = filters.NumberFilter(field_name="ville__id")
    type = filters.CharFilter(field_name="type")
    actif = filters.BooleanFilter()
    q = filters.CharFilter(method="filter_q")
    region = filters.NumberFilter(field_name="ville__region__id")
    region_nom = filters.CharFilter(field_name="ville__region__nom", lookup_expr="icontains")
    ville_nom = filters.CharFilter(field_name="ville__nom", lookup_expr="icontains")

    def filter_q(self, queryset, name, value):
        return queryset.filter(nom__icontains=value)

    class Meta:
        model = Magasin
        fields = ["ville", "type", "actif", "region", "region_nom", "ville_nom"]
