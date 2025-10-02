import os
from elasticsearch import Elasticsearch


def get_es_client() -> Elasticsearch:
    url = os.getenv('ELASTICSEARCH_URL', 'http://127.0.0.1:9200')
    verify_certs = os.getenv('ELASTICSEARCH_VERIFY_CERTS', 'true').lower() in ('1','true','yes','y')
    return Elasticsearch(hosts=[url], verify_certs=verify_certs)


def check_health(client: Elasticsearch) -> dict:
    try:
        return client.cluster.health()
    except Exception as e:
        return {'status': 'red', 'error': str(e)}
