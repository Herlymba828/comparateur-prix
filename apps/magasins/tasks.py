from celery import shared_task
from django.db.models import Q
from .models import Magasin
from .services import geocode_magasin

@shared_task
def geocode_missing_magasins(limit: int = 200) -> dict:
    """
    Géocode en lot les magasins sans coordonnées (latitude/longitude).
    Retourne un résumé {processed, updated}.
    """
    qs = Magasin.objects.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True))[:max(1, int(limit))]
    processed = 0
    updated = 0
    for m in qs:
        processed += 1
        try:
            if geocode_magasin(m):
                updated += 1
        except Exception:
            # Ignorer les échecs individuels
            pass
    return {"processed": processed, "updated": updated}
