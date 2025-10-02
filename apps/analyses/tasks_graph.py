from celery import shared_task
import logging
from django.core.management import call_command

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generer_snapshots_graphes(self, graph_type: str = 'magasin-magasin', window_days: int = 90, min_interactions: int = 2, dry_run: bool = False):
    """Construit un snapshot de graphe (ex: magasin–magasin) en appelant la commande management.
    Planifié quotidiennement par Celery Beat.
    """
    try:
        logger.info(f"[Graph] Génération snapshot type={graph_type} window_days={window_days} min_interactions={min_interactions}")
        call_command(
            'analyser_graphes',
            type=graph_type,
            **{
                'window_days': window_days,
                'min_interactions': min_interactions,
                'dry_run': dry_run,
            }
        )
        logger.info("[Graph] Génération terminée")
    except Exception as e:
        logger.error(f"[Graph] Erreur génération snapshot: {e}")
        raise self.retry(exc=e)
