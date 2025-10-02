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
        es = get_es_client()
        recreate = options["recreate"]
        reindex = options["reindex"]
        batch_size = options["batch"]

        if recreate:
            try:
                es.indices.delete(index=INDEX_PRODUCTS, ignore_unavailable=True)
            except Exception:
                pass
        ensure_indices()
        self.stdout.write(self.style.SUCCESS("Elasticsearch indices ensured."))

        if not reindex and not recreate:
            self.stdout.write("No reindex requested. Use --reindex to bulk index all products.")
            return

        qs = (
            Produit.objects.select_related("categorie", "marque")
            .filter(est_actif=True)
            .order_by("id")
        )
        total = qs.count()
        self.stdout.write(f"Indexing {total} products in batches of {batch_size}...")

        def gen_actions():
            for p in qs.iterator(chunk_size=batch_size):
                doc = make_product_doc(p)
                yield {
                    "_op_type": "index",
                    "_index": INDEX_PRODUCTS,
                    "_id": p.id,
                    "_source": doc,
                }

        success, _ = bulk(es, gen_actions(), chunk_size=batch_size, raise_on_error=False)
        self.stdout.write(self.style.SUCCESS(f"Bulk indexed {success} documents."))
