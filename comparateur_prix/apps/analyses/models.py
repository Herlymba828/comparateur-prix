from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.produits.models import Produit, Categorie
from apps.magasins.models import Magasin, Ville, Region
from apps.produits.models import Prix

import uuid

User = get_user_model()

class AnalysePrix(models.Model):
    """Modèle pour stocker les analyses de prix"""
    
    TYPE_ANALYSE_CHOICES = [
        ('comparaison_enseigne', 'Comparaison entre enseignes'),
        ('evolution_temporelle', 'Évolution temporelle des prix'),
        ('analyse_ecart', 'Analyse des écarts de prix'),
        ('prediction_tendance', 'Prédiction de tendance'),
        ('benchmark_categorie', 'Benchmark par catégorie'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    type_analyse = models.CharField(max_length=50, choices=TYPE_ANALYSE_CHOICES)
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Paramètres de l'analyse
    parametres = models.JSONField(default=dict)
    
    # Résultats de l'analyse
    resultats = models.JSONField(default=dict)
    
    # Métriques de performance
    metriques = models.JSONField(default=dict)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    date_maj = models.DateTimeField(auto_now=True)
    date_debut_periode = models.DateField()
    date_fin_periode = models.DateField()
    
    class Meta:
        db_table = 'analyses_prix'
        verbose_name = 'Analyse de prix'
        verbose_name_plural = 'Analyses de prix'
        indexes = [
            models.Index(fields=['type_analyse', 'date_creation']),
            models.Index(fields=['utilisateur', 'date_creation']),
            models.Index(fields=['date_debut_periode', 'date_fin_periode']),
        ]
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} ({self.get_type_analyse_display()})"

class RapportAnalyse(models.Model):
    """Modèle pour générer des rapports d'analyse formatés"""
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
    ]
    
    STATUT_CHOICES = [
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('erreur', 'Erreur')
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analyse = models.ForeignKey(AnalysePrix, on_delete=models.CASCADE, related_name='rapports')
    format_rapport = models.CharField(max_length=10, choices=FORMAT_CHOICES)
    fichier_rapport = models.FileField(upload_to='rapports_analyses/', null=True, blank=True)
    
    # Configuration du rapport
    configuration = models.JSONField(default=dict)
    
    date_generation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_cours')
    
    class Meta:
        db_table = 'rapports_analyse'
        verbose_name = 'Rapport d\'analyse'
        verbose_name_plural = 'Rapports d\'analyse'
        indexes = [
            models.Index(fields=['analyse', 'date_generation']),
        ]
    
    def __str__(self):
        return f"Rapport {self.format_rapport} - {self.analyse.titre}"

class IndicateurPerformance(models.Model):
    """Modèle pour suivre les indicateurs de performance des analyses"""
    
    TENDANCE_CHOICES = [
        ('hausse', 'Hausse'),
        ('baisse', 'Baisse'), 
        ('stable', 'Stable')
    ]
    
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    valeur_actuelle = models.FloatField()
    valeur_cible = models.FloatField()
    unite = models.CharField(max_length=20)
    tendance = models.CharField(max_length=10, choices=TENDANCE_CHOICES)
    
    date_calcul = models.DateTimeField(auto_now=True)
    periode_mesure = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'indicateurs_performance'
        verbose_name = 'Indicateur de performance'
        verbose_name_plural = 'Indicateurs de performance'
        indexes = [
            models.Index(fields=['nom', 'date_calcul']),
        ]
    
    def __str__(self):
        return f"{self.nom}: {self.valeur_actuelle} {self.unite}"

class CacheAnalyse(models.Model):
    """Cache pour optimiser les requêtes d'analyse fréquentes"""
    
    cle_cache = models.CharField(max_length=255, unique=True)
    donnees_cache = models.JSONField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_expiration = models.DateTimeField()
    
    # Métadonnées pour l'invalidation intelligente du cache
    metadata = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'cache_analyses'
        verbose_name = 'Cache d\'analyse'
        verbose_name_plural = 'Caches d\'analyse'
        indexes = [
            models.Index(fields=['cle_cache', 'date_expiration']),
            models.Index(fields=['date_expiration']),
        ]
    
    def __str__(self):
        return f"Cache: {self.cle_cache}"

class AnalysisType(models.TextChoices):
    TENDANCE = 'tendance', 'Tendance'
    PRIX = 'prix', 'Analyse Prix'
    RECOMMANDATION = 'recommandation', 'Recommandation'

class AnalysisResult(models.Model):
    """Résultats d'analyse génériques avec portée optionnelle"""
    
    type = models.CharField(max_length=32, choices=AnalysisType.choices)
    nom = models.CharField(max_length=150)
    
    # Portée optionnelle
    produit = models.ForeignKey(Produit, null=True, blank=True, on_delete=models.CASCADE)
    categorie = models.ForeignKey(Categorie, null=True, blank=True, on_delete=models.SET_NULL)
    ville = models.ForeignKey(Ville, null=True, blank=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    
    donnees = models.JSONField(default=dict, blank=True)
    calcule_le = models.DateTimeField(auto_now_add=True)
    ttl_seconds = models.PositiveIntegerField(default=3600)
    
    class Meta:
        db_table = 'analysis_results'
        verbose_name = 'Résultat d\'analyse'
        verbose_name_plural = 'Résultats d\'analyse'
        indexes = [
            models.Index(fields=['type', 'nom']),
            models.Index(fields=['produit']),
            models.Index(fields=['categorie']),
            models.Index(fields=['ville']),
            models.Index(fields=['region']),
            models.Index(fields=['calcule_le']),
        ]
        ordering = ['-calcule_le']
    
    def __str__(self):
        return f"{self.type}:{self.nom}"

class PriceAggregate(models.Model):
    """Agrégats de prix par fenêtre temporelle"""
    
    produit = models.ForeignKey(Produit, null=True, blank=True, on_delete=models.CASCADE)
    categorie = models.ForeignKey(Categorie, null=True, blank=True, on_delete=models.SET_NULL)
    ville = models.ForeignKey(Ville, null=True, blank=True, on_delete=models.SET_NULL)
    region = models.ForeignKey(Region, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Fenêtre temporelle
    fenetre_debut = models.DateTimeField()
    fenetre_fin = models.DateTimeField()
    
    # Statistiques
    prix_min = models.DecimalField(max_digits=12, decimal_places=2)
    prix_max = models.DecimalField(max_digits=12, decimal_places=2)
    prix_moyen = models.DecimalField(max_digits=12, decimal_places=2)
    echantillons = models.PositiveIntegerField(default=0)
    
    calcule_le = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'price_aggregates'
        verbose_name = 'Agrégat de prix'
        verbose_name_plural = 'Agrégats de prix'
        indexes = [
            models.Index(fields=['produit', 'fenetre_debut', 'fenetre_fin']),
            models.Index(fields=['categorie', 'fenetre_debut', 'fenetre_fin']),
            models.Index(fields=['ville', 'fenetre_debut', 'fenetre_fin']),
            models.Index(fields=['region', 'fenetre_debut', 'fenetre_fin']),
            models.Index(fields=['fenetre_debut', 'fenetre_fin']),
        ]
        ordering = ['-fenetre_debut']
    
    def __str__(self):
        cible = self.produit or self.categorie or self.ville or self.region or 'Global'
        return f"Agg {cible} [{self.fenetre_debut:%Y-%m-%d} -> {self.fenetre_fin:%Y-%m-%d}]"


# === Graph analytics (snapshots & metrics) ===
class GraphSnapshot(models.Model):
    """Snapshot d'un graphe calculé (ex: projection magasin–magasin)"""
    SNAPSHOT_TYPES = (
        ("magasin-magasin", "Magasin–Magasin"),
        ("client-client", "Client–Client"),
        ("produit-produit", "Produit–Produit"),
    )

    type = models.CharField(max_length=32, choices=SNAPSHOT_TYPES, default="magasin-magasin")
    params_hash = models.CharField(max_length=64, help_text="Hash des paramètres (fenêtre, seuils)")
    window_start = models.DateTimeField(null=True, blank=True)
    window_end = models.DateTimeField(null=True, blank=True)
    node_count = models.PositiveIntegerField(default=0)
    edge_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Snapshot de graphe"
        verbose_name_plural = "Snapshots de graphe"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["type", "created_at"]),
            models.Index(fields=["type", "params_hash"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["type", "params_hash", "window_start", "window_end"], name="unique_graphsnapshot_key")
        ]

    def __str__(self):
        return f"GraphSnapshot({self.type}) {self.window_start} -> {self.window_end}"


class NodeMetric(models.Model):
    """Métriques par nœud pour un snapshot (magasins, clients, produits)."""
    snapshot = models.ForeignKey(GraphSnapshot, on_delete=models.CASCADE, related_name="nodes")
    node_key = models.CharField(max_length=128, db_index=True)
    label = models.CharField(max_length=255, blank=True, default="")

    degree = models.FloatField(default=0)
    weightedDegree = models.FloatField(default=0)
    pagerank = models.FloatField(default=0)
    community = models.IntegerField(default=-1)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Métrique de nœud"
        verbose_name_plural = "Métriques de nœud"
        indexes = [
            models.Index(fields=["snapshot", "node_key"]),
            models.Index(fields=["snapshot", "pagerank"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["snapshot", "node_key"], name="unique_node_metric")
        ]

    def __str__(self):
        return f"NodeMetric({self.node_key})@{self.snapshot_id}"


class EdgeMetric(models.Model):
    """Métriques par arête pour un snapshot (graphe non orienté)."""
    snapshot = models.ForeignKey(GraphSnapshot, on_delete=models.CASCADE, related_name="edges")
    source_key = models.CharField(max_length=128)
    target_key = models.CharField(max_length=128)
    weight = models.FloatField(default=0)
    similarity = models.FloatField(default=0)
    extra = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Métrique d'arête"
        verbose_name_plural = "Métriques d'arête"
        indexes = [
            models.Index(fields=["snapshot", "source_key", "target_key"]),
            models.Index(fields=["snapshot", "weight"]),
        ]
        constraints = [
            models.CheckConstraint(check=~models.Q(source_key=models.F("target_key")), name="edge_no_self_loop"),
            models.UniqueConstraint(fields=["snapshot", "source_key", "target_key"], name="unique_edge_metric")
        ]

    def __str__(self):
        return f"EdgeMetric({self.source_key}->{self.target_key})@{self.snapshot_id}"