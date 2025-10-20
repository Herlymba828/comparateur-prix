from django.http import JsonResponse
from django.db.models import Min, Q, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from apps.produits.models import Produit
from apps.produits.models import Prix
from apps.magasins.models import Magasin
from .models import SearchEvent
from .serializers import (
    HealthSerializer,
    ProductSearchResultSerializer,
    AutocompleteResultSerializer,
)
from .services.ebay_client import EbayClient
from .services.normalize import normalize_ebay_item
import hashlib


def health(_request):
    return JsonResponse({"status": "ok"})


@api_view(["GET"])
def search_produits(request):
    """Recherche de produits avec prix minimum agrégé (option filtres)."""
    q = (request.GET.get("q") or "").strip()
    categorie = request.GET.get("categorie")
    marque = (request.GET.get("marque") or "").strip()
    page = int(request.GET.get("page", 1))
    page_size = int(request.GET.get("page_size", 20))

    produits = Produit.objects.select_related("categorie", "marque").all()
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

    # Annoter le prix minimum via relation inverse Prix -> Produit
    produits = produits.annotate(min_prix=Min("prix__prix_actuel"))

    total = produits.count()
    start = (page - 1) * page_size
    end = start + page_size

    items = []
    for p in produits.order_by("nom")[start:end]:
        items.append(
            {
                "id": p.id,
                "nom": p.nom,
                "marque": (p.marque.nom if getattr(p, "marque", None) else ""),
                "categorie_id": p.categorie_id,
                "categorie_nom": p.categorie.nom if p.categorie else "",
                "min_prix": p.min_prix,
                "devise": "XAF" if p.min_prix is not None else None,
            }
        )

    data = {"count": total, "results": ProductSearchResultSerializer(items, many=True).data}

    # Journaliser la recherche (un événement par requête)
    try:
        if q:
            user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
            ip = (request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR') or '').split(',')[0].strip()
            ip_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()[:64] if ip else ''
            # Tenter d'associer un produit si le terme est un nom exact
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
    q = (request.GET.get("q") or "").strip()
    if not q:
        return Response({"results": []}, status=HTTP_200_OK)
    qs = (
        Produit.objects.filter(nom__icontains=q)
        .order_by("nom")
        .values("id", "nom")[:10]
    )
    results = [{"id": row["id"], "label": row["nom"]} for row in qs]
    return Response({"results": AutocompleteResultSerializer(results, many=True).data}, status=HTTP_200_OK)


@api_view(["GET"])
def homologations_stats(_request):
    """Retourne quelques statistiques synthétiques pour l'homologation/monitoring."""
    produits_count = Produit.objects.count()
    magasins_count = Magasin.objects.count()
    prix_count = Prix.objects.count()
    # Date la plus récente de modification de prix si dispo (champ existant)
    latest_prix = (
        Prix.objects.order_by('-date_modification')
        .values_list('date_modification', flat=True)
        .first()
    )
    payload = {
        'produits': produits_count,
        'magasins': magasins_count,
        'prix': prix_count,
        'dernier_prix_mis_a_jour': latest_prix,
        'ok': True,
    }
    return Response(payload, status=HTTP_200_OK)


@api_view(["GET"])
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
