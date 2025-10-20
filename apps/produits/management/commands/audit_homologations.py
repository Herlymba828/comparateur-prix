from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.produits.models import HomologationProduit
import csv
import sys


class Command(BaseCommand):
    help = "Audit des HomologationProduit avec sous_categorie vide (rapport et export CSV optionnel)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200, help="Nombre max de lignes à afficher")
        parser.add_argument("--offset", type=int, default=0, help="Décalage de départ")
        parser.add_argument("--csv", dest="csv_out", help="Chemin d'export CSV des lignes vides")
        parser.add_argument("--stats", action="store_true", help="Afficher uniquement les statistiques de répartition par categorie")

    def handle(self, *args, **options):
        limit = options["limit"]
        offset = options["offset"]
        csv_out = options.get("csv_out")
        only_stats = options.get("stats")

        qs_empty = HomologationProduit.objects.filter(sous_categorie__exact="").order_by("id")
        total_empty = qs_empty.count()

        # Stats par categorie
        stats = (
            qs_empty.values("categorie")
            .annotate(c=Count("id"))
            .order_by("-c", "categorie")
        )

        if only_stats:
            self.stdout.write(self.style.NOTICE(f"Total sans sous_categorie: {total_empty}"))
            for row in stats:
                cat = row["categorie"] or "(Non classé)"
                self.stdout.write(f"{cat}: {row['c']}")
            return

        self.stdout.write(self.style.NOTICE(f"Total sans sous_categorie: {total_empty}"))
        self.stdout.write(self.style.NOTICE("Top catégories (manquantes):"))
        for row in list(stats)[:20]:
            cat = row["categorie"] or "(Non classé)"
            self.stdout.write(f"- {cat}: {row['c']}")

        # Liste paginée
        page = list(qs_empty[offset: offset + limit].values(
            "id", "nom", "marque", "format", "categorie", "sous_categorie", "reference_titre", "reference_numero"
        ))

        if not page:
            self.stdout.write("Aucune ligne à afficher pour cette page.")
        else:
            self.stdout.write(self.style.SUCCESS(f"Aperçu ({len(page)} lignes):"))
            for e in page:
                self.stdout.write(
                    f"#{e['id']} | {e['nom']} | marque={e['marque'] or '-'} | format={e['format'] or '-'} | cat={e['categorie'] or '-'} | sous_cat=(vide)"
                )

        # Export CSV optionnel
        if csv_out:
            fieldnames = [
                "id", "nom", "marque", "format", "categorie", "sous_categorie",
                "reference_titre", "reference_numero"
            ]
            try:
                with open(csv_out, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in qs_empty.values(*fieldnames):
                        writer.writerow(row)
                self.stdout.write(self.style.SUCCESS(f"CSV exporté: {csv_out}"))
            except Exception as exc:
                self.stderr.write(f"Erreur export CSV: {exc}")
                sys.exit(1)
