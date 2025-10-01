from rest_framework import serializers
from .models import AnalysePrix, RapportAnalyse, IndicateurPerformance, AnalysisResult, PriceAggregate
from apps.produits.serializers import ProduitListSerializer
from apps.magasins.serializers import MagasinSerializer, VilleSerializer, RegionSerializer

class AnalysisResultSerializer(serializers.ModelSerializer):
    produit = ProduitListSerializer(read_only=True)
    ville = VilleSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    
    class Meta:
        model = AnalysisResult
        fields = ['id', 'type', 'nom', 'produit', 'categorie', 'ville', 'region', 
                 'donnees', 'calcule_le', 'ttl_seconds']
        read_only_fields = ['calcule_le']

class PriceAggregateSerializer(serializers.ModelSerializer):
    produit = ProduitListSerializer(read_only=True)
    ville = VilleSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    
    class Meta:
        model = PriceAggregate
        fields = ['id', 'produit', 'categorie', 'ville', 'region', 
                 'fenetre_debut', 'fenetre_fin', 'prix_min', 'prix_max', 
                 'prix_moyen', 'echantillons', 'calcule_le']
        read_only_fields = ['calcule_le']

class IndicateurPerformanceSerializer(serializers.ModelSerializer):
    progression = serializers.SerializerMethodField()
    statut = serializers.SerializerMethodField()
    
    class Meta:
        model = IndicateurPerformance
        fields = ['id', 'nom', 'description', 'valeur_actuelle', 'valeur_cible', 
                 'unite', 'tendance', 'progression', 'statut', 'date_calcul', 'periode_mesure']
        read_only_fields = ['date_calcul']
    
    def get_progression(self, obj):
        if obj.valeur_cible == 0:
            return 0
        return round((obj.valeur_actuelle / obj.valeur_cible) * 100, 2)
    
    def get_statut(self, obj):
        progression = self.get_progression(obj)
        if progression >= 100:
            return 'atteint'
        elif progression >= 80:
            return 'proche'
        else:
            return 'a_ameliorer'

class RapportAnalyseSerializer(serializers.ModelSerializer):
    taille_fichier = serializers.SerializerMethodField()
    url_telechargement = serializers.SerializerMethodField()
    
    class Meta:
        model = RapportAnalyse
        fields = ['id', 'analyse', 'format_rapport', 'fichier_rapport', 
                 'taille_fichier', 'url_telechargement', 'date_generation', 'statut', 'configuration']
        read_only_fields = ['date_generation']
    
    def get_taille_fichier(self, obj):
        if obj.fichier_rapport:
            return obj.fichier_rapport.size
        return None
    
    def get_url_telechargement(self, obj):
        if obj.fichier_rapport:
            return obj.fichier_rapport.url
        return None

class AnalysePrixSerializer(serializers.ModelSerializer):
    rapports = RapportAnalyseSerializer(many=True, read_only=True)
    duree_analyse = serializers.SerializerMethodField()
    nombre_produits_analyses = serializers.SerializerMethodField()
    nombre_magasins_analyses = serializers.SerializerMethodField()
    
    class Meta:
        model = AnalysePrix
        fields = ['id', 'utilisateur', 'type_analyse', 'titre', 'description',
                 'parametres', 'resultats', 'metriques', 'rapports',
                 'duree_analyse', 'nombre_produits_analyses', 'nombre_magasins_analyses',
                 'date_creation', 'date_maj', 'date_debut_periode', 'date_fin_periode']
        read_only_fields = ['resultats', 'metriques', 'date_creation', 'date_maj']
    
    def get_duree_analyse(self, obj):
        if obj.metriques and 'duree_calcul' in obj.metriques:
            return obj.metriques['duree_calcul']
        return None
    
    def get_nombre_produits_analyses(self, obj):
        if obj.metriques and 'nombre_produits' in obj.metriques:
            return obj.metriques['nombre_produits']
        return 0
    
    def get_nombre_magasins_analyses(self, obj):
        if obj.metriques and 'nombre_magasins' in obj.metriques:
            return obj.metriques['nombre_magasins']
        return 0

class AnalysePrixCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysePrix
        fields = ['type_analyse', 'titre', 'description', 'parametres', 
                 'date_debut_periode', 'date_fin_periode']

class ResultatAnalyseDetailSerializer(serializers.Serializer):
    """Serializer pour les résultats détaillés d'analyse"""
    
    produit = ProduitListSerializer()
    magasin = MagasinSerializer()
    prix_moyen = serializers.FloatField()
    prix_minimum = serializers.FloatField()
    prix_maximum = serializers.FloatField()
    ecart_type = serializers.FloatField()
    variation_7j = serializers.FloatField()
    variation_30j = serializers.FloatField()
    
    class Meta:
        fields = ['produit', 'magasin', 'prix_moyen', 'prix_minimum', 
                 'prix_maximum', 'ecart_type', 'tendance', 'variation_7j', 'variation_30j']


# === Graph analytics serializers ===
from .models import GraphSnapshot, NodeMetric, EdgeMetric


class GraphSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = GraphSnapshot
        fields = ['id', 'type', 'params_hash', 'window_start', 'window_end', 'node_count', 'edge_count', 'created_at']


class NodeMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeMetric
        fields = ['id', 'snapshot', 'node_key', 'label', 'degree', 'weightedDegree', 'pagerank', 'community', 'extra']


class EdgeMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = EdgeMetric
        fields = ['id', 'snapshot', 'source_key', 'target_key', 'weight', 'similarity', 'extra']