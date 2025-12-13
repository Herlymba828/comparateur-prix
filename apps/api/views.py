from django.http import JsonResponse
from django.db.models import Min, Max, Q, Count
from django.utils.dateparse import parse_datetime, parse_date
from django.core.cache import cache
from datetime import datetime, time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_500_INTERNAL_SERVER_ERROR
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from apps.produits.models import Produit
from apps.produits.models import Prix
from apps.magasins.models import Magasin
from apps.produits.views import StatistiquesPrixViewSet
from .models import SearchEvent
import logging
import json

logger = logging.getLogger(__name__)
from .serializers import (
    HealthSerializer,
    ProductSearchResultSerializer,
    AutocompleteResultSerializer,
)
from .services.ebay_client import EbayClient
from .services.normalize import normalize_ebay_item
import hashlib


def health(request):
    """
    Health check endpoint amélioré avec monitoring.
    Retourne le statut de santé du système.
    """
    from .monitoring import HealthChecker, PerformanceMonitor
    
    # Mode simple (par défaut)
    detailed = request.GET.get('detailed', 'false').lower() == 'true'
    
    if not detailed:
        # Health check simple et rapide
        return JsonResponse({
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        })
    
    # Health check détaillé
    health_status = HealthChecker.get_full_health_status()
    
    # Ajouter les métriques si demandées
    if request.GET.get('metrics', 'false').lower() == 'true':
        health_status['metrics'] = PerformanceMonitor.get_metrics()
    
    # Déterminer le code de statut HTTP
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


def test_simple(request):
    """
    Endpoint de test ultra-simple pour diagnostic.
    """
    from apps.produits.models import Produit, Categorie
    
    try:
        produits_count = Produit.objects.count()
        categories_count = Categorie.objects.count()
        
        return JsonResponse({
            "status": "ok",
            "message": "Test simple réussi",
            "database": {
                "produits": produits_count,
                "categories": categories_count
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }, status=500)


class TestConnectionView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        return Response({
            'status': 'success',
            'message': 'Connexion API réussie!',
            'data': {
                'user': str(request.user) if request.user.is_authenticated else 'Non authentifié',
                'timestamp': datetime.now().isoformat()
            }
        })


@api_view(["GET"])
def search_produits(request):
    """Recherche de produits avec prix minimum agrégé (option filtres) - OPTIMISÉ."""
    q = (request.GET.get("q") or "").strip()
    categorie = request.GET.get("categorie")
    marque = (request.GET.get("marque") or "").strip()
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    # Générer la clé de cache basée sur les paramètres
    params = {
        'q': q,
        'categorie': categorie,
        'marque': marque,
        'page': page,
        'page_size': page_size,
    }
    cache_key = f"search_produits:{hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()}"
    
    # Vérifier le cache
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Cache hit pour search_produits: {cache_key[:50]}")
        return Response(cached, status=HTTP_200_OK)

    # ✅ OPTIMISATION : select_related + annotation en une requête
    produits = Produit.objects.select_related("categorie", "marque", "unite_mesure")
    
    if q:
        produits = produits.filter(
            Q(nom__icontains=q)
            | Q(marque__nom__icontains=q)
            | Q(categorie__nom__icontains=q)
        )
    if categorie:
        produits = produits.filter(categorie_id=categorie)
    if marque:
        produits = produits.filter(marque__nom__icontains=marque)

    # ✅ OPTIMISATION : Annotation avec filtre sur est_disponible
    produits = produits.annotate(
        min_prix=Min("prix__prix_actuel", filter=Q(prix__est_disponible=True)),
        max_prix=Max("prix__prix_actuel", filter=Q(prix__est_disponible=True)),
        prix_count=Count("prix", filter=Q(prix__est_disponible=True)),
    ).filter(est_actif=True)  # Filtrer les produits actifs

    # ✅ OPTIMISATION : Compter AVANT de paginer (plus efficace)
    total = produits.count()
    start = (page - 1) * page_size
    
    # ✅ OPTIMISATION : Utiliser values() pour réduire la taille des données
    items_data = list(
        produits.order_by("nom")[start:start + page_size]
        .values(
            "id", "nom",
            "categorie_id", "categorie__nom",
            "marque__nom",
            "min_prix", "max_prix", "prix_count"
        )
    )
    
    # Formater les résultats
    items = [
        {
            "id": item["id"],
            "nom": item["nom"],
            "marque": item["marque__nom"] or "",
            "categorie_id": item["categorie_id"],
            "categorie_nom": item["categorie__nom"] or "",
            "min_prix": item["min_prix"],
            "max_prix": item["max_prix"],
            "prix_count": item["prix_count"],
            "devise": "XAF" if item["min_prix"] is not None else None,
        }
        for item in items_data
    ]

    data = {"count": total, "results": ProductSearchResultSerializer(items, many=True).data}

    # Mettre en cache avec TTL adaptatif
    ttl = 900 if (categorie or marque) else 300
    cache.set(cache_key, data, ttl)
    logger.debug(f"Cache miss pour search_produits, mis en cache avec TTL {ttl}s")

    # ✅ OPTIMISATION : Log asynchrone (ne bloque pas la réponse)
    try:
        if q:
            # Importer la tâche asynchrone si disponible, sinon log synchrone
            try:
                from .tasks import log_search_event_async
                user_id = request.user.id if request.user.is_authenticated else None
                ip = (request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or '').split(',')[0].strip()
                ip_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()[:64] if ip else ''
                
                # Trouver le produit si nom exact
                produit_id = None
                try:
                    produit_id = Produit.objects.filter(nom__iexact=q).values_list('id', flat=True).first()
                except Exception:
                    pass
                
                # Envoyer la tâche asynchrone
                log_search_event_async.delay(q, produit_id, user_id, ip_hash)
            except ImportError:
                # Fallback vers log synchrone si Celery n'est pas disponible
                user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
                ip = (request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or '').split(',')[0].strip()
                ip_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()[:64] if ip else ''
                produit_obj = None
                try:
                    pid = Produit.objects.filter(nom__iexact=q).values_list('id', flat=True).first()
                    if pid:
                        produit_obj = Produit.objects.only('id').get(id=pid)
                except Exception:
                    produit_obj = None
                SearchEvent.objects.create(q=q, produit=produit_obj, utilisateur=user, ip_hash=ip_hash)
    except Exception:
        # Ne jamais bloquer la réponse sur un problème de log
        pass
    
    return Response(data, status=HTTP_200_OK)


@api_view(["GET"])
def autocomplete_produits(request):
    """Autocomplete de produits - OPTIMISÉ."""
    q = (request.GET.get("q") or "").strip()
    if not q or len(q) < 2:  # ✅ OPTIMISATION : Minimum 2 caractères
        return Response({"results": []}, status=HTTP_200_OK)
    
    # Cache key simple basé sur la requête (normalisée en minuscules)
    cache_key = f"autocomplete:{q.lower()}"
    
    # Vérifier le cache
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Cache hit pour autocomplete: {q}")
        return Response(cached, status=HTTP_200_OK)
    
    # ✅ OPTIMISATION : utiliser only() pour limiter les champs chargés
    # ✅ Limite stricte à 10 résultats (suffisant pour autocomplete)
    qs = (
        Produit.objects
        .filter(est_actif=True, nom__icontains=q)
        .only("id", "nom")  # Charger uniquement les champs nécessaires
        .order_by("nom")
        .values("id", "nom")[:10]  # Limite stricte
    )
    
    results = [{"id": row["id"], "label": row["nom"]} for row in qs]
    data = {"results": AutocompleteResultSerializer(results, many=True).data}
    
    # Mettre en cache avec TTL court (2 minutes) car très fréquent
    cache.set(cache_key, data, 120)
    logger.debug(f"Cache miss pour autocomplete, mis en cache: {q}")
    
    return Response(data, status=HTTP_200_OK)


@api_view(["GET"])
def homologations_stats(request):
    """Statistiques synthétiques filtrables pour l'homologation/monitoring.

    Query params optionnels:
      - produit_id | productId: filtrer sur un produit
      - date_from | start: borne inférieure (datetime/date ISO)
      - date_to   | end:   borne supérieure (datetime/date ISO)
      - localisation: filtre texte sur Magasin.localisation (icontains)
      - ville: filtre texte sur Magasin.ville.nom (icontains)
      - ville_id: filtre exact sur Magasin.ville.id
    """
    produit_id = request.GET.get("produit_id") or request.GET.get("productId")
    date_from = request.GET.get("date_from") or request.GET.get("start")
    date_to = request.GET.get("date_to") or request.GET.get("end")
    localisation = request.GET.get("localisation")
    ville = request.GET.get("ville")
    ville_id = request.GET.get("ville_id")

    # Générer la clé de cache basée sur les filtres
    filters = {
        'produit_id': produit_id,
        'date_from': date_from,
        'date_to': date_to,
        'localisation': localisation,
        'ville': ville,
        'ville_id': ville_id,
    }
    cache_key = f"homologations_stats:{hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()}"
    
    # Vérifier le cache
    cached = cache.get(cache_key)
    if cached:
        logger.debug(f"Cache hit pour homologations_stats: {cache_key[:50]}")
        return Response(cached, status=HTTP_200_OK)

    prix_qs = Prix.objects.all()

    # Filtre produit
    if produit_id:
        try:
            pid = int(produit_id)
            prix_qs = prix_qs.filter(produit_id=pid)
        except (TypeError, ValueError):
            pass

    # Filtres période (sur date_modification si dispo)
    def _to_dt(val, end=False):
        if not val:
            return None
        dt = parse_datetime(val)
        if dt is not None:
            return dt
        d = parse_date(val)
        if d is not None:
            return datetime.combine(d, time.max if end else time.min)
        return None

    dt_from = _to_dt(date_from, end=False)
    dt_to = _to_dt(date_to, end=True)
    if dt_from:
        prix_qs = prix_qs.filter(date_modification__gte=dt_from)
    if dt_to:
        prix_qs = prix_qs.filter(date_modification__lte=dt_to)

    # Filtres localisation
    if localisation:
        prix_qs = prix_qs.filter(magasin__localisation__icontains=localisation)
    if ville:
        prix_qs = prix_qs.filter(magasin__ville__nom__icontains=ville)
    if ville_id:
        try:
            vid = int(ville_id)
            prix_qs = prix_qs.filter(magasin__ville_id=vid)
        except (TypeError, ValueError):
            pass

    # Comptages filtrés
    produits_count = prix_qs.values("produit_id").distinct().count()
    magasins_count = prix_qs.values("magasin_id").distinct().count()
    prix_count = prix_qs.count()
    latest_prix = (
        prix_qs.order_by('-date_modification')
        .values_list('date_modification', flat=True)
        .first()
    )

    payload = {
        'produits': produits_count,
        'magasins': magasins_count,
        'prix': prix_count,
        'dernier_prix_mis_a_jour': latest_prix,
        'filtres': {
            'produit_id': produit_id,
            'date_from': date_from,
            'date_to': date_to,
            'localisation': localisation,
            'ville': ville,
            'ville_id': ville_id,
        },
        'ok': True,
    }
    
    # Mettre en cache avec TTL de 30 minutes (calculs coûteux)
    cache.set(cache_key, payload, 1800)
    logger.debug(f"Cache miss pour homologations_stats, mis en cache avec TTL 1800s")
    
    return Response(payload, status=HTTP_200_OK)


@api_view(['GET'])
def stats_prix(request):
    """Endpoint pour les statistiques sur les prix (alias de /api/produits/statistiques-prix/)"""
    try:
        # Utiliser le ViewSet existant
        viewset = StatistiquesPrixViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        
        # Appeler la méthode list du ViewSet
        response = viewset.list(request)
        return response
    except Exception as e:
        logger.error(f"Erreur dans stats_prix: {e}", exc_info=True)
        return Response(
            {'erreur': 'Erreur lors de la récupération des statistiques de prix'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def compare_offers(request):
    """
    Comparateur public: interroge eBay (et futur Amazon) et renvoie des offres normalisées.
    Params:
      - q: requête (obligatoire)
      - limit: nombre max d'items (<= 50)
      - market: EBAY_FR (par défaut), EBAY_US, EBAY_GB, etc.
      - sources: liste séparée par virgule (ex: "ebay,amazon") — pour l'instant, eBay seul.
    """
    q = (request.GET.get("q") or "").strip()
    if not q:
        return Response({"results": [], "count": 0}, status=HTTP_200_OK)

    limit = int(request.GET.get("limit", 10))
    market = (request.GET.get("market") or "EBAY_FR").strip() or "EBAY_FR"
    sources = (request.GET.get("sources") or "ebay").lower().split(",")
    sort = (request.GET.get("sort") or "price").lower()  # price | rating | combined
    try:
        alpha = float(request.GET.get("alpha", 0.7))  # poids du prix dans le score combiné
    except ValueError:
        alpha = 0.7
    produit_id = request.GET.get("produit_id")  # optionnel: utiliser notes internes du produit

    results = []

    if "ebay" in sources:
        try:
            client = EbayClient()
            data = client.search(q=q, limit=limit, marketplace=market)
            items = client.extract_items(data)
            for it in items:
                results.append(normalize_ebay_item(it))
        except Exception as e:
            # On échoue en douceur, et on inclut un message informatif minimal
            results.append({
                "marketplace": "ebay",
                "error": str(e),
            })

    # TODO: intégrer Amazon PA-API ici (phase 2)

    # Calcul de la note moyenne interne si un produit_id est fourni
    avg_rating = None
    ratings_count = 0
    if produit_id:
        try:
            pid = int(produit_id)
            from apps.produits.models import AvisProduit, Produit as _Prod
            if _Prod.objects.filter(id=pid).exists():
                from django.db.models import Avg, Count
                agg = AvisProduit.objects.filter(produit_id=pid).aggregate(
                    avg=Avg('note'), cnt=Count('id')
                )
                avg_rating = agg.get('avg') or None
                ratings_count = int(agg.get('cnt') or 0)
        except Exception:
            pass

    # Prix total (prix + livraison)
    def total_price(x):
        p = x.get("price")
        s = x.get("shipping_cost") or 0
        try:
            return (float(p) + float(s)) if p is not None else None
        except Exception:
            return None

    # Préparer champs d'aide
    totals = [tp for tp in (total_price(r) for r in results) if tp is not None]
    if totals:
        min_p, max_p = min(totals), max(totals)
    else:
        min_p, max_p = None, None

    # Score normalisé prix: plus petit prix => score proche de 1
    def price_score(x):
        tp = total_price(x)
        if tp is None or min_p is None or max_p is None:
            return 0.0
        if max_p == min_p:
            return 1.0
        return max(0.0, min(1.0, (max_p - tp) / (max_p - min_p)))

    # Score note: moyenne/5 si dispo, sinon 0
    def rating_score():
        if avg_rating is None:
            return 0.0
        try:
            return max(0.0, min(1.0, float(avg_rating) / 5.0))
        except Exception:
            return 0.0

    r_score = rating_score()

    # Calcul du score combiné par offre
    for r in results:
        r["_total_price"] = total_price(r)
        r["_price_score"] = price_score(r)
        r["_rating_score"] = r_score
        r["combined_score"] = alpha * r["_price_score"] + (1 - alpha) * r["_rating_score"]

    # Tri selon paramètre
    if sort == "rating":
        results_sorted = sorted(
            results,
            key=lambda x: (-(x.get("_rating_score") or 0), (x.get("_total_price") or float("inf")))
        )
    elif sort == "combined":
        results_sorted = sorted(
            results,
            key=lambda x: (-(x.get("combined_score") or 0), (x.get("_total_price") or float("inf")))
        )
    else:  # price (default)
        results_sorted = sorted(
            results,
            key=lambda x: (x.get("_total_price") is None, x.get("_total_price") or float("inf"))
        )

    # Nettoyage des champs techniques
    for r in results_sorted:
        r.pop("_price_score", None)
        r.pop("_rating_score", None)
        # conserver _total_price utile côté client pour affichage/tri

    return Response({
        "query": q,
        "count": len(results_sorted),
        "sort": sort,
        "alpha": alpha,
        "produit_id": produit_id,
        "avg_rating": avg_rating,
        "ratings_count": ratings_count,
        "results": results_sorted,
    }, status=HTTP_200_OK)
