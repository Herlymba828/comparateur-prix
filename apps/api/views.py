from django.http import JsonResponse
from django.db.models import Min, Q, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from apps.produits.models import Produit
from apps.produits.models import Prix
from apps.magasins.models import Magasin
from .serializers import (
    HealthSerializer,
    ProductSearchResultSerializer,
    AutocompleteResultSerializer,
)


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
