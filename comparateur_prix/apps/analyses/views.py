from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db import models
from django.db.models import Avg, Min, Max, StdDev, Count
from django.utils import timezone
from django.core.cache import cache
from django.db import connection
import datetime
import json

from .models import (
    AnalysePrix, RapportAnalyse, IndicateurPerformance, AnalysisResult, PriceAggregate,
    GraphSnapshot, NodeMetric, EdgeMetric,
)
from .serializers import (
    AnalysePrixSerializer, AnalysePrixCreateSerializer,
    RapportAnalyseSerializer, IndicateurPerformanceSerializer,
    AnalysisResultSerializer, PriceAggregateSerializer,
)
from .filters import AnalysePrixFilter
from .utils import OptimiseurRequetes, CalculateurMetriques


class AnalysePrixViewSet(viewsets.ModelViewSet):
    """ViewSet pour la gestion des analyses de prix avec optimisation des performances"""
    queryset = AnalysePrix.objects.select_related('utilisateur').prefetch_related('rapports')
    serializer_class = AnalysePrixSerializer
    filterset_class = AnalysePrixFilter

    def get_serializer_class(self):
        if self.action == 'create':
            return AnalysePrixCreateSerializer
        return AnalysePrixSerializer

    def perform_create(self, serializer):
        analyse = serializer.save(utilisateur=self.request.user)
        from .tasks import executer_analyse_prix
        executer_analyse_prix.delay(analyse.id)

    @action(detail=True, methods=['post'])
    def generer_rapport(self, request, pk=None):
        analyse = self.get_object()
        format_rapport = request.data.get('format', 'pdf')
        rapport = RapportAnalyse.objects.create(
            analyse=analyse,
            format_rapport=format_rapport,
            configuration=request.data.get('configuration', {})
        )
        from .tasks import generer_rapport_analyse
        generer_rapport_analyse.delay(rapport.id)
        return Response({'message': f'Génération du rapport {format_rapport} lancée', 'rapport_id': rapport.id}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'])
    def analyses_recents(self, request):
        analyses = self.queryset.filter(date_creation__gte=timezone.now() - datetime.timedelta(days=30))[:10]
        serializer = self.get_serializer(analyses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques_globales(self, request):
        cache_key = 'statistiques_analyses_globales'
        donnees_cache = cache.get(cache_key)
        if donnees_cache:
            return Response(donnees_cache)
        aujourdhui = timezone.now().date()
        debut_mois = aujourdhui.replace(day=1)
        stats = {
            'total_analyses': AnalysePrix.objects.count(),
            'analyses_ce_mois': AnalysePrix.objects.filter(date_creation__date__gte=debut_mois).count(),
            'types_analyses': dict(AnalysePrix.objects.values('type_analyse').annotate(count=Count('id')).values_list('type_analyse', 'count')),
            'moyenne_duree_analyse': AnalysePrix.objects.aggregate(moyenne=models.Avg(models.F('metriques__duree_calcul')))['moyenne'] or 0,
        }
        cache.set(cache_key, stats, 3600)
        return Response(stats)


class RapportAnalyseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RapportAnalyse.objects.select_related('analyse')
    serializer_class = RapportAnalyseSerializer

    @action(detail=True, methods=['get'])
    def telecharger(self, request, pk=None):
        rapport = self.get_object()
        if not rapport.fichier_rapport:
            return Response({'error': 'Rapport non disponible'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'url_telechargement': rapport.fichier_rapport.url})


class IndicateurPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IndicateurPerformance.objects.all()
    serializer_class = IndicateurPerformanceSerializer

    @action(detail=False, methods=['get'])
    def tableau_de_bord(self, request):
        cache_key = 'tableau_bord_indicateurs'
        donnees_cache = cache.get(cache_key)
        if donnees_cache:
            return Response(donnees_cache)
        indicateurs = self.get_queryset()
        serializer = self.get_serializer(indicateurs, many=True)
        metrics = {
            'date_actualisation': timezone.now(),
            'nombre_total_indicateurs': indicateurs.count(),
            'indicateurs_atteints': indicateurs.filter(models.Q(valeur_actuelle__gte=models.F('valeur_cible'))).count(),
        }
        resultat = {'indicateurs': serializer.data, 'metriques': metrics}
        cache.set(cache_key, resultat, 1800)
        return Response(resultat)


class AnalysisResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AnalysisResult.objects.select_related('produit', 'categorie', 'ville', 'region')
    serializer_class = AnalysisResultSerializer
    filterset_fields = ['type', 'produit', 'categorie', 'ville', 'region']

    @action(detail=False, methods=['get'])
    def par_type(self, request):
        type_analyse = request.GET.get('type')
        if not type_analyse:
            return Response({'error': 'Paramètre type requis'}, status=400)
        results = self.queryset.filter(type=type_analyse).order_by('-calcule_le')[:50]
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)


class PriceAggregateViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PriceAggregate.objects.select_related('produit', 'categorie', 'ville', 'region')
    serializer_class = PriceAggregateSerializer
    filterset_fields = ['produit', 'categorie', 'ville', 'region']

    @action(detail=False, methods=['get'])
    def evolution_temporelle(self, request):
        produit_id = request.GET.get('produit_id')
        categorie_id = request.GET.get('categorie_id')
        jours = int(request.GET.get('jours', 30))
        date_debut = timezone.now() - datetime.timedelta(days=jours)
        queryset = self.queryset.filter(fenetre_debut__gte=date_debut)
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
        elif categorie_id:
            queryset = queryset.filter(categorie_id=categorie_id)
        aggregates = queryset.order_by('fenetre_debut')
        serializer = self.get_serializer(aggregates, many=True)
        return Response({'periode': f'{jours} jours', 'date_debut': date_debut, 'aggregates': serializer.data})


class AnalyseOptimiseeViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def comparaison_enseignes(self, request):
        categorie_id = request.GET.get('categorie_id')
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        cache_key = f"comparaison_enseignes_{categorie_id}_{date_debut}_{date_fin}"
        resultat_cache = cache.get(cache_key)
        if resultat_cache:
            return Response(resultat_cache)
        optimiseur = OptimiseurRequetes()
        resultats = optimiseur.executer_comparaison_enseignes(categorie_id, date_debut, date_fin)
        cache.set(cache_key, resultats, 900)
        return Response(resultats)

    @action(detail=False, methods=['get'])
    def evolution_prix(self, request):
        produit_id = request.GET.get('produit_id')
        magasin_id = request.GET.get('magasin_id', None)
        periode = request.GET.get('periode', '30j')
        cache_key = f"evolution_prix_{produit_id}_{magasin_id}_{periode}"
        resultat_cache = cache.get(cache_key)
        if resultat_cache:
            return Response(resultat_cache)
        optimiseur = OptimiseurRequetes()
        resultats = optimiseur.executer_analyse_evolution(produit_id, magasin_id, periode)
        cache.set(cache_key, resultats, 600)
        return Response(resultats)


@api_view(["GET"])
def latest_graph(request):
    """Export JSON du dernier snapshot de graphe.

    Params: type (default magasin-magasin), limit_nodes, include_edges.
    """
    gtype = request.GET.get('type', 'magasin-magasin')
    include_edges = request.GET.get('include_edges', 'true').lower() in ('1', 'true', 'yes', 'y')
    order = request.GET.get('order')  # pagerank|degree|cheapness|popularity
    try:
        top = int(request.GET.get('top')) if request.GET.get('top') else None
    except Exception:
        top = None
    try:
        min_weight = float(request.GET.get('min_weight')) if request.GET.get('min_weight') else None
    except Exception:
        min_weight = None
    try:
        limit_nodes = int(request.GET.get('limit_nodes')) if request.GET.get('limit_nodes') else None
    except Exception:
        limit_nodes = None

    snapshot = GraphSnapshot.objects.filter(type=gtype).order_by('-created_at').first()
    if not snapshot:
        return Response({'error': 'Aucun snapshot disponible pour ce type'}, status=404)

    nodes_qs = NodeMetric.objects.filter(snapshot=snapshot)
    # Build nodes list first
    nodes = [{
        'key': n.node_key,
        'label': n.label,
        'degree': n.degree,
        'weightedDegree': n.weightedDegree,
        'pagerank': n.pagerank,
        'community': n.community,
        'extra': n.extra or {},
    } for n in nodes_qs]

    # Sorting/top filters
    if order in ('pagerank', 'degree', 'cheapness', 'popularity'):
        if order == 'cheapness':
            key_fn = lambda x: (x['extra'] or {}).get('cheapness_score') or 0.0
        elif order == 'popularity':
            key_fn = lambda x: (x['extra'] or {}).get('popularity_count') or 0
        else:
            key_fn = (lambda x: x[order])
        nodes.sort(key=key_fn, reverse=True)
    else:
        # default by pagerank desc
        nodes.sort(key=lambda x: x['pagerank'], reverse=True)

    if limit_nodes and limit_nodes > 0:
        nodes = nodes[:limit_nodes]
    if top and top > 0:
        nodes = nodes[:top]

    edges = []
    if include_edges:
        allowed = set(n['key'] for n in nodes)
        edges_qs = EdgeMetric.objects.filter(snapshot=snapshot)
        if nodes:
            edges_qs = edges_qs.filter(source_key__in=allowed, target_key__in=allowed)
        if min_weight is not None:
            edges_qs = edges_qs.filter(weight__gte=min_weight)
        edges = [{
            'source': e.source_key,
            'target': e.target_key,
            'weight': e.weight,
            'similarity': e.similarity,
            'extra': e.extra or {},
        } for e in edges_qs]

    payload = {
        'snapshot': {
            'id': snapshot.id,
            'type': snapshot.type,
            'params_hash': snapshot.params_hash,
            'window_start': snapshot.window_start,
            'window_end': snapshot.window_end,
            'node_count': snapshot.node_count,
            'edge_count': snapshot.edge_count,
            'created_at': snapshot.created_at,
        },
        'nodes': nodes,
        'edges': edges,
        'tops': {
            'pagerank': [{
                'key': n['key'], 'label': n['label'], 'pagerank': n['pagerank']
            } for n in sorted(nodes, key=lambda x: x['pagerank'], reverse=True)[:10]],
            'degree': [{
                'key': n['key'], 'label': n['label'], 'degree': n['degree']
            } for n in sorted(nodes, key=lambda x: x['degree'], reverse=True)[:10]],
        }
    }
    return Response(payload)