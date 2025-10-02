import os
from elasticsearch import Elasticsearch

ES_HOST = os.getenv("ELASTICSEARCH_HOST", "localhost")
ES_PORT = int(os.getenv("ELASTICSEARCH_PORT", "9200"))
ES_SCHEME = os.getenv("ELASTICSEARCH_SCHEME", "http")
ES_USER = os.getenv("ELASTICSEARCH_USERNAME")
ES_PASS = os.getenv("ELASTICSEARCH_PASSWORD")
ES_VERIFY = str(os.getenv("ELASTICSEARCH_VERIFY_CERTS", "false")).lower() in ("1", "true", "yes")

INDEX_PRODUCTS = os.getenv("ELASTICSEARCH_INDEX_PRODUCTS", "produits")
INDEX_SUGGEST = os.getenv("ELASTICSEARCH_INDEX_SUGGEST", "produits_suggest")


def get_es_client() -> Elasticsearch:
    kwargs = {
        "hosts": [{
            "host": ES_HOST,
            "port": ES_PORT,
            "scheme": ES_SCHEME,
        }],
        "verify_certs": ES_VERIFY,
    }
    if ES_USER and ES_PASS:
        kwargs["basic_auth"] = (ES_USER, ES_PASS)
    return Elasticsearch(**kwargs)


PRODUCT_MAPPING = {
    "settings": {
        "analysis": {
            "filter": {
                "fr_elision": {"type": "elision", "articles_case": True, "articles": [
                    "l", "m", "t", "qu", "n", "s", "j", "d", "c", "jusqu", "quoiqu", "lorsqu", "puisqu"
                ]},
                "fr_stemmer": {"type": "stemmer", "language": "light_french"},
                "fr_stop": {"type": "stop", "stopwords": "_french_"}
            },
            "analyzer": {
                "french_custom": {
                    "tokenizer": "standard",
                    "filter": ["lowercase", "asciifolding", "fr_elision", "fr_stop", "fr_stemmer"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "code_barre": {"type": "keyword"},
            "nom": {"type": "text", "analyzer": "french_custom"},
            "slug": {"type": "keyword"},
            "categorie": {"type": "keyword"},
            "categorie_nom": {"type": "text", "analyzer": "french_custom"},
            "marque": {"type": "keyword"},
            "marque_nom": {"type": "text", "analyzer": "french_custom"},
            "est_actif": {"type": "boolean"},
            "date_creation": {"type": "date"},
            "suggest": {"type": "completion"}
        }
    }
}


def make_product_doc(produit):
    return {
        "id": str(produit.id),
        "code_barre": produit.code_barre,
        "nom": produit.nom,
        "slug": produit.slug,
        "categorie": str(produit.categorie_id),
        "categorie_nom": getattr(produit.categorie, "nom", None),
        "marque": str(produit.marque_id) if produit.marque_id else None,
        "marque_nom": getattr(produit.marque, "nom", None) if produit.marque_id else None,
        "est_actif": produit.est_actif,
        "date_creation": produit.date_creation,
        "suggest": {
            "input": [x for x in [produit.nom, getattr(produit.marque, "nom", None), getattr(produit.categorie, "nom", None)] if x],
            "weight": 5
        }
    }


def ensure_indices():
    es = get_es_client()
    if not es.indices.exists(index=INDEX_PRODUCTS):
        es.indices.create(index=INDEX_PRODUCTS, mappings=PRODUCT_MAPPING["mappings"], settings=PRODUCT_MAPPING["settings"]) 
    if not es.indices.exists(index=INDEX_SUGGEST):
        es.indices.create(index=INDEX_SUGGEST, mappings={
            "properties": {
                "id": {"type": "keyword"},
                "suggest": {"type": "completion"}
            }
        })


def index_product(produit):
    es = get_es_client()
    doc = make_product_doc(produit)
    es.index(index=INDEX_PRODUCTS, id=produit.id, document=doc, refresh="wait_for")
    # also index suggest-only doc
    es.index(index=INDEX_SUGGEST, id=produit.id, document={"id": str(produit.id), "suggest": doc["suggest"]}, refresh="wait_for")


def delete_product(product_id):
    es = get_es_client()
    try:
        es.delete(index=INDEX_PRODUCTS, id=product_id, refresh="wait_for")
    except Exception:
        pass
    try:
        es.delete(index=INDEX_SUGGEST, id=product_id, refresh="wait_for")
    except Exception:
        pass


def search_products(q: str, size: int = 20, offset: int = 0):
    es = get_es_client()
    body = {
        "from": offset,
        "size": size,
        "query": {
            "bool": {
                "must": [
                    {"multi_match": {"query": q, "fields": ["nom^3", "categorie_nom^1.5", "marque_nom^2"]}}
                ],
                "filter": [{"term": {"est_actif": True}}]
            }
        },
        "highlight": {"fields": {"nom": {}}}
    }
    return es.search(index=INDEX_PRODUCTS, body=body)


def suggest_products(prefix: str, size: int = 5):
    es = get_es_client()
    body = {
        "suggest": {
            "product-suggest": {
                "prefix": prefix,
                "completion": {"field": "suggest", "size": size}
            }
        }
    }
    return es.search(index=INDEX_SUGGEST, body=body)
