from typing import List, Dict, Any

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from apps.produits.models import Prix


@api_view(["GET"])
def prix_proches_public(request):
    """
    Liste les prix d'un produit à proximité d'une position (public).
    Params requis: produit_id, lat, lng
    Optionnels: rayon_km (def 10), max_results (def 50), sort=distance|price|combined, mode (pour durée)
    """
    produit_id = request.GET.get("produit_id")
    if not produit_id:
        return Response({"error": "produit_id requis"}, status=HTTP_400_BAD_REQUEST)
    try:
        produit_id = int(produit_id)
        lat = float(request.GET.get("lat"))
        lng = float(request.GET.get("lng"))
    except (TypeError, ValueError):
        return Response({"error": "Paramètres lat et lng requis (float)"}, status=HTTP_400_BAD_REQUEST)

    try:
        rayon_km = float(request.GET.get("rayon_km", 10))
    except ValueError:
        rayon_km = 10.0
    try:
        max_results = int(request.GET.get("max_results", 50))
    except ValueError:
        max_results = 50
    sort = (request.GET.get("sort") or "distance").lower()
    mode = request.GET.get("mode") or "driving"

    # Haversine helpers
    from math import radians, sin, cos, sqrt, atan2

    def haversine_km(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    # Bounding box approx pour limiter
    lat_delta = rayon_km / 111.0
    lng_delta = rayon_km / max(0.0001, (111.320 * cos(radians(lat))))

    qs = (
        Prix.objects.select_related("magasin", "produit")
        .filter(
            produit_id=produit_id,
            est_disponible=True,
            magasin__latitude__isnull=False,
            magasin__longitude__isnull=False,
            magasin__latitude__gte=lat - lat_delta,
            magasin__latitude__lte=lat + lat_delta,
            magasin__longitude__gte=lng - lng_delta,
            magasin__longitude__lte=lng + lng_delta,
        )
    )

    candidats: List[Dict[str, Any]] = []
    for p in qs:
        try:
            d = haversine_km(float(p.magasin.latitude), float(p.magasin.longitude), lat, lng)
        except Exception:
            continue
        if d <= rayon_km:
            item = {
                "prix_id": p.id,
                "produit": {
                    "id": p.produit_id,
                    "nom": p.produit.nom,
                },
                "magasin": {
                    "id": p.magasin_id,
                    "nom": p.magasin.nom,
                    "latitude": float(p.magasin.latitude),
                    "longitude": float(p.magasin.longitude),
                    "adresse": p.magasin.adresse,
                },
                "prix_actuel": float(p.prix_actuel),
                "prix_origine": float(p.prix_origine) if p.prix_origine is not None else None,
                "est_promotion": bool(p.est_promotion),
                "date_modification": p.date_modification,
                "distance_km": d,
            }
            candidats.append(item)

    # Distance Matrix (durée) si clé configurée
    from django.conf import settings as _s
    if getattr(_s, "GOOGLE_MAPS_API_KEY", None) and candidats:
        try:
            import googlemaps
            gmaps = googlemaps.Client(key=_s.GOOGLE_MAPS_API_KEY)
            origins = [(lat, lng)]
            destinations = [(c["magasin"]["latitude"], c["magasin"]["longitude"]) for c in candidats]
            dm = gmaps.distance_matrix(origins=origins, destinations=destinations, mode=mode)
            rows = dm.get("rows", [])
            if rows and rows[0].get("elements"):
                for c, el in zip(candidats, rows[0]["elements"]):
                    if el.get("status") == "OK":
                        c["duration_min"] = el["duration"]["value"] / 60.0
        except Exception:
            pass

    # Tri
    if sort == "price":
        candidats.sort(key=lambda x: (x.get("prix_actuel") is None, x.get("prix_actuel") or 0, x.get("distance_km") or 1e9))
    elif sort == "combined":
        prices = [c["prix_actuel"] for c in candidats if c.get("prix_actuel") is not None]
        pmin, pmax = (min(prices), max(prices)) if prices else (None, None)

        def price_score(v):
            if v is None or pmin is None or pmax is None:
                return 0.0
            if pmax == pmin:
                return 1.0
            return max(0.0, min(1.0, (pmax - v) / (pmax - pmin)))

        def dist_score(d):
            return 1.0 / (1.0 + (d or 0))

        for c in candidats:
            c["combined_score"] = 0.6 * dist_score(c.get("distance_km")) + 0.4 * price_score(c.get("prix_actuel"))
        candidats.sort(key=lambda x: (-x.get("combined_score", 0), x.get("distance_km") or 1e9))
    else:
        candidats.sort(key=lambda x: (x.get("distance_km") is None, x.get("distance_km") or 1e9, x.get("prix_actuel") or 0))

    candidats = candidats[: max(1, min(max_results, 200))]

    return Response(
        {
            "count": len(candidats),
            "params": {
                "produit_id": produit_id,
                "lat": lat,
                "lng": lng,
                "rayon_km": rayon_km,
                "sort": sort,
                "max_results": max_results,
                "mode": mode,
            },
            "results": candidats,
        },
        status=HTTP_200_OK,
    )
