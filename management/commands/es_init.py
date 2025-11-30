from django.core.management.base import BaseCommand
from django.db import transaction
from elasticsearch.helpers import bulk

from apps.produits.search import get_es_client, ensure_indices, INDEX_PRODUCTS, make_product_doc
from apps.produits.models import Produit


class Command(BaseCommand):
    help = "Initialize Elasticsearch indices and bulk index products."

    def add_arguments(self, parser):
        parser.add_argument("--recreate", action="store_true", help="Delete and recreate product indices")
        parser.add_argument("--reindex", action="store_true", help="Force bulk reindex of all products")
        parser.add_argument("--batch", type=int, default=1000, help="Bulk batch size (default: 1000)")

    def handle(self, *args, **options):
        try:
            es = get_es_client()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Impossible de se connecter à Elasticsearch: {type(e).__name__} - {str(e)}"))
            self.stdout.write(self.style.WARNING("Vérifiez que Elasticsearch est démarré et accessible."))
            return
        
        recreate = options["recreate"]
        reindex = options["reindex"]
        batch_size = options["batch"]

        if recreate:
            try:
                es.indices.delete(index=INDEX_PRODUCTS, ignore_unavailable=True)
                self.stdout.write(self.style.SUCCESS("✓ Index produits supprimé"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Impossible de supprimer l'index: {type(e).__name__} - {str(e)}"))
        
        try:
            ensure_indices()
            self.stdout.write(self.style.SUCCESS("✓ Elasticsearch indices créés/vérifiés"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Impossible de créer les index: {type(e).__name__} - {str(e)}"))
            return

        if not reindex and not recreate:
            self.stdout.write("No reindex requested. Use --reindex to bulk index all products.")
            return

        qs = (
            Produit.objects.select_related("categorie", "marque")
            .filter(est_actif=True)
            .order_by("id")
        )
        total = qs.count()
        self.stdout.write(f"Indexation de {total} produits par lots de {batch_size}...")

        def gen_actions():
            for p in qs.iterator(chunk_size=batch_size):
                doc = make_product_doc(p)
                yield {
                    "_op_type": "index",
                    "_index": INDEX_PRODUCTS,
                    "_id": p.id,
                    "_source": doc,
                }

        try:
            success, errors = bulk(es, gen_actions(), chunk_size=batch_size, raise_on_error=False, request_timeout=10)
            self.stdout.write(self.style.SUCCESS(f"✓ {success} documents indexés avec succès"))
            if errors:
                self.stdout.write(self.style.WARNING(f"⚠️  {len(errors)} erreurs lors de l'indexation"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur lors de l'indexation en masse: {type(e).__name__} - {str(e)}"))
