import hashlib
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.db.models import Min

from apps.produits.models import Prix
from apps.magasins.models import Magasin
from apps.analyses.models import GraphSnapshot, NodeMetric, EdgeMetric

import networkx as nx
try:
    import community as community_louvain  # python-louvain
except Exception:  # pragma: no cover
    community_louvain = None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Construit des snapshots de graphes (ex: projection magasin–magasin) pour analyses."

    def add_arguments(self, parser):
        parser.add_argument('--type', default='magasin-magasin', choices=['magasin-magasin'], help='Type de graphe à construire')
        parser.add_argument('--window-days', type=int, default=90, help='Fenêtre temporelle en jours')
        parser.add_argument('--min-interactions', type=int, default=2, help="Seuil minimal d'interactions pour garder une arête")
        parser.add_argument('--dry-run', action='store_true')

    def handle(self, *args, **options):
        gtype = options['type']
        window_days = options['window_days']
        min_interactions = options['min_interactions']
        dry_run = options['dry_run']

        if gtype != 'magasin-magasin':
            self.stdout.write(self.style.WARNING(f"Type non supporté: {gtype}"))
            return

        window_end = timezone.now()
        window_start = window_end - timedelta(days=window_days)
        params_key = f"{gtype}|{window_start.date()}|{window_end.date()}|min={min_interactions}"
        params_hash = hashlib.sha256(params_key.encode('utf-8')).hexdigest()[:32]

        self.stdout.write(f"Construction du graphe {gtype} pour {window_days} jours (hash={params_hash})")

        # 1) Charger activités pertinentes: Prix par magasin et produit, récemment modifiés
        qs = (Prix.objects
              .filter(date_modification__range=(window_start, window_end), est_disponible=True)
              .select_related('produit', 'magasin')
        )

        # Pré-calculs pour KPI magasin
        # a) Prix minimum par produit (fenêtre)
        produit_min = dict(
            qs.values('produit_id').annotate(m=Min('prix_actuel')).values_list('produit_id', 'm')
        )
        # b) Popularité (nb d'observations) et cheapness (moyenne du ratio prix/min_produit)
        from collections import defaultdict
        pop_counts = defaultdict(int)
        cheap_sum = defaultdict(float)
        cheap_cnt = defaultdict(int)
        # c) Couverture produits par magasin (nb de produits distincts)
        product_set_per_mag = defaultdict(set)
        for prod_id, mag_id, p in qs.values_list('produit_id', 'magasin_id', 'prix_actuel'):
            pop_counts[mag_id] += 1
            product_set_per_mag[mag_id].add(prod_id)
            minp = float(produit_min.get(prod_id) or 0) or None
            if minp and float(p) > 0:
                ratio = float(p) / minp  # >= 1.0; plus proche de 1.0 = meilleur marché
                cheap_sum[mag_id] += ratio
                cheap_cnt[mag_id] += 1

        # Construire mapping produit -> set(magasins)
        produit_to_magasins = {}
        for p in qs.values_list('produit_id', 'magasin_id'):
            prod_id, mag_id = p
            produit_to_magasins.setdefault(prod_id, set()).add(mag_id)

        # 2) Graphe magasin–magasin par co-présence sur mêmes produits
        G = nx.Graph()
        # Ajouter noeuds de magasins présents
        magasin_ids = set(m for mags in produit_to_magasins.values() for m in mags)
        for mid in magasin_ids:
            G.add_node(f"magasin:{mid}")

        # Ajouter les arêtes avec poids = nombre de cooccurrences produits
        from collections import Counter
        edge_counter = Counter()
        for mags in produit_to_magasins.values():
            mags = list(mags)
            for i in range(len(mags)):
                for j in range(i+1, len(mags)):
                    a, b = sorted((mags[i], mags[j]))
                    edge_counter[(a, b)] += 1

        for (a, b), w in edge_counter.items():
            if w >= min_interactions:
                G.add_edge(f"magasin:{a}", f"magasin:{b}", weight=float(w))

        # 3) Mesures
        weighted_degree = dict(G.degree(weight='weight'))
        try:
            pr = nx.pagerank(G, weight='weight') if G.number_of_nodes() > 0 else {}
        except Exception:
            pr = {}

        communities = {}
        if community_louvain and G.number_of_nodes() > 0 and G.number_of_edges() > 0:
            try:
                part = community_louvain.best_partition(G, weight='weight')
                communities = part
            except Exception:
                communities = {}

        # 4) Persistance
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: aucune écriture DB"))
            return

        with transaction.atomic():
            snapshot, created = GraphSnapshot.objects.get_or_create(
                type=gtype,
                params_hash=params_hash,
                window_start=window_start,
                window_end=window_end,
                defaults={'node_count': G.number_of_nodes(), 'edge_count': G.number_of_edges()}
            )
            if not created:
                # Nettoyer métriques précédentes pour réécriture
                snapshot.nodes.all().delete()
                snapshot.edges.all().delete()
                snapshot.node_count = G.number_of_nodes()
                snapshot.edge_count = G.number_of_edges()
                snapshot.save(update_fields=['node_count', 'edge_count'])

            # Node metrics
            labels = {m.id: m.nom for m in Magasin.objects.filter(id__in=[int(n.split(':')[1]) for n in G.nodes()])}
            for node in G.nodes():
                mid = int(node.split(':')[1])
                avg_ratio = (cheap_sum[mid] / cheap_cnt[mid]) if cheap_cnt[mid] else None
                cheapness_score = (1.0 / avg_ratio) if avg_ratio and avg_ratio > 0 else None
                popularity = pop_counts.get(mid, 0)
                product_coverage = len(product_set_per_mag.get(mid, set()))
                NodeMetric.objects.create(
                    snapshot=snapshot,
                    node_key=node,
                    label=labels.get(mid, str(mid)),
                    degree=float(G.degree(node)),
                    weightedDegree=float(weighted_degree.get(node, 0.0)),
                    pagerank=float(pr.get(node, 0.0)),
                    community=int(communities.get(node, -1)),
                    extra={
                        'cheapness_avg_ratio': round(avg_ratio, 4) if avg_ratio else None,
                        'cheapness_score': round(cheapness_score, 4) if cheapness_score else None,
                        'popularity_count': int(popularity),
                        'product_coverage': int(product_coverage),
                    }
                )

            # Edge metrics
            for u, v, data in G.edges(data=True):
                w = float(data.get('weight', 1.0))
                if u <= v:
                    EdgeMetric.objects.create(snapshot=snapshot, source_key=u, target_key=v, weight=w, similarity=0.0, extra={})
                else:
                    EdgeMetric.objects.create(snapshot=snapshot, source_key=v, target_key=u, weight=w, similarity=0.0, extra={})

        self.stdout.write(self.style.SUCCESS(f"Snapshot {snapshot.id} enregistré: {snapshot.node_count} noeuds, {snapshot.edge_count} arêtes"))
