from django.core.management.base import BaseCommand
from django.db.models import Q
from apps.magasins.models import Magasin
from apps.magasins.services import geocode_magasin


class Command(BaseCommand):
    help = "Géocode en lot les magasins sans coordonnées (ou forcer la mise à jour)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200, help="Nombre max d'éléments à traiter")
        parser.add_argument("--offset", type=int, default=0, help="Décalage de départ")
        parser.add_argument("--only-missing", action="store_true", help="Ne traiter que ceux sans lat/lon")
        parser.add_argument("--force", action="store_true", help="Forcer le régéocodage même si lat/lon présents")

    def handle(self, *args, **options):
        limit = options["limit"]
        offset = options["offset"]
        only_missing = options["only_missing"]
        force = options["force"]

        qs = Magasin.objects.select_related("ville", "ville__region").all()
        if only_missing:
            qs = qs.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True))

        if not force:
            # si pas force, on ne touche pas aux magasins déjà positionnés
            qs = qs.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True))

        total = qs.count()
        self.stdout.write(self.style.NOTICE(f"Candidats à géocoder: {total}"))

        qs = qs.order_by("id")[offset:offset + limit]

        done = 0
        for m in qs:
            updated = geocode_magasin(m)
            if updated:
                done += 1
                self.stdout.write(self.style.SUCCESS(f"OK: {m.nom} -> ({m.latitude},{m.longitude})"))
            else:
                self.stdout.write(f"SKIP: {m.nom}")

        self.stdout.write(self.style.SUCCESS(f"Terminé. {done}/{qs.count()} mis à jour."))
