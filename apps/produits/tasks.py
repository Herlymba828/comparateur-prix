from celery import shared_task
from django.core.management import call_command
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import os
import sys
from pathlib import Path
import json
import logging

from .models import AlertePrix
from .models import Prix
from .models import HomologationProduit, PrixHomologue


@shared_task
def update_prices_task(supermarches: str | None = None, hypermarches: str | None = None, max_workers: int | None = None):
    """Run the update_prices management command as a Celery task.
    Args can be provided as comma-separated URL strings. If omitted, .env configuration is used.
    """
    cmd = ["update_prices"]
    if supermarches:
        cmd.extend(["--supermarches", supermarches])
    if hypermarches:
        cmd.extend(["--hypermarches", hypermarches])
    if max_workers is not None:
        cmd.extend(["--max-workers", str(max_workers)])
    call_command(*cmd)


@shared_task(name="tache_mettre_a_jour_prix")
def tache_mettre_a_jour_prix(supermarches: str | None = None, hypermarches: str | None = None, max_workers: int | None = None):
    """Alias français de update_prices_task."""
    return update_prices_task(supermarches=supermarches, hypermarches=hypermarches, max_workers=max_workers)


@shared_task
def verifier_alertes_prix_task(utilisateur_id: int | None = None, frequences: list[str] | None = None) -> int:
    """Vérifie les alertes de prix actives et envoie des emails si les seuils sont atteints.
    Si utilisateur_id est fourni, ne traite que ses alertes.
    Retourne le nombre d'alertes notifiées.
    """
    alertes = AlertePrix.objects.filter(est_active=True)
    if utilisateur_id:
        alertes = alertes.filter(utilisateur_id=utilisateur_id)
    if frequences:
        alertes = alertes.filter(frequence_verification__in=frequences)

    notifiees = 0
    for alerte in alertes.select_related('produit', 'utilisateur').prefetch_related('magasins'):
        # Prix minimum actuel (filtre magasins si fourni)
        prix_qs = Prix.objects.filter(produit=alerte.produit, est_disponible=True)
        if alerte.magasins.exists():
            prix_qs = prix_qs.filter(magasin__in=alerte.magasins.all())
        prix_min = prix_qs.order_by('prix_actuel').values_list('prix_actuel', flat=True).first()

        if prix_min is None:
            continue

        seuil_atteint = False
        raisons = []
        # Condition 1: prix souhaité
        if prix_min <= alerte.prix_souhaite:
            seuil_atteint = True
            raisons.append(f"Prix minimum {prix_min}€ <= prix souhaité {alerte.prix_souhaite}€")

        # Condition 2: pourcentage de réduction (vs prix d'origine s'il existe)
        if alerte.pourcentage_reduction is not None:
            # Chercher un prix avec prix_origine pour calculer la réduction
            p = prix_qs.exclude(prix_origine__isnull=True).order_by('prix_actuel').first()
            if p and p.prix_origine and p.prix_origine > 0:
                reduction = (p.prix_origine - p.prix_actuel) / p.prix_origine * Decimal(100)
                if reduction >= alerte.pourcentage_reduction:
                    seuil_atteint = True
                    raisons.append(f"Réduction {reduction:.2f}% >= seuil {alerte.pourcentage_reduction}%")

        if seuil_atteint:
            # Envoyer email
            try:
                sujet = f"Alerte prix atteinte: {alerte.produit.nom}"
                message = (
                    f"Bonjour {alerte.utilisateur.get_username()},\n\n"
                    f"Le produit '{alerte.produit.nom}' a atteint votre seuil.\n"
                    f"Raisons: {'; '.join(raisons)}.\n"
                    f"Consultez l'application pour plus de détails.\n\n"
                    f"Cordialement,\nComparateur Prix"
                )
                send_mail(
                    sujet,
                    message,
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
                    [alerte.utilisateur.email],
                    fail_silently=True,
                )
                # Mettre à jour les métadonnées
                alerte.date_derniere_alerte = timezone.now()
                alerte.nombre_alertes_envoyees = (alerte.nombre_alertes_envoyees or 0) + 1
                alerte.save(update_fields=['date_derniere_alerte', 'nombre_alertes_envoyees'])
                notifiees += 1
            except Exception:
                # ne pas interrompre la boucle
                pass
    return notifiees


# --- DGCCRF/EDIG homologations workflow ---
@shared_task
def import_homologations_task(limit: int | None = None, since_date: str | None = None, verbose: bool = False, dry_run: bool = False) -> int:
    """Exécute la commande de management 'import_homologations'."""
    cmd = ["import_homologations"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if since_date:
        cmd.extend(["--since-date", since_date])
    if verbose:
        cmd.append("--verbose")
    if dry_run:
        cmd.append("--dry-run")
    call_command(*cmd)
    return 0


@shared_task(name="dgccrf_scrape_report_task", bind=True, max_retries=3)
def dgccrf_scrape_report_task(self, limit: int | None = None,
                              unified: bool = True,
                              save: bool = True,
                              only_changed: bool = True,
                              csv_out: str | None = None,
                              sql_out: str | None = None,
                              report_out: str | None = None,
                              sources: list[str] | None = None) -> dict:
    """Tâche Celery pour le scraping DGCCRF avec sauvegarde automatique en base de données.
    
    Cette tâche automatise complètement le processus de scraping et de sauvegarde :
    - Scrape les données depuis les sources DGCCRF
    - Sauvegarde automatiquement en base de données (Produit, Prix, HomologationProduit, PrixHomologue)
    - Génère des rapports détaillés
    - Gère les erreurs avec retry automatique
    
    Args:
        limit: Limite le nombre d'éléments à scraper (None = pas de limite)
        unified: Export au format unifié
        save: Sauvegarder en base de données (True par défaut)
        only_changed: Ne scraper que les éléments modifiés (True par défaut pour performance)
        csv_out: Chemin de sortie CSV (optionnel)
        sql_out: Chemin de sortie SQL (optionnel)
        report_out: Chemin du rapport JSON (optionnel)
        sources: Liste des sources à scraper (par défaut: toutes)
    
    Returns:
        dict: Statistiques de l'extraction avec:
            - success: bool
            - total_items: int
            - saved_products: int
            - saved_prices: int
            - source_counts: dict
            - duration_sec: float
            - timestamp: str
    """
    logger = logging.getLogger(__name__)
    logger.info(
        f"Début du scraping DGCCRF automatisé "
        f"(limit={limit}, save={save}, only_changed={only_changed}, sources={sources})"
    )
    
    try:
        # Importer le scraper directement
        import sys
        base_dir = Path(getattr(settings, 'BASE_DIR', Path(__file__).resolve().parents[2]))
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))
        
        # Import du scraper depuis scripts/
        import importlib.util
        scraper_path = base_dir / 'scripts' / 'scraper_dgccrf.py'
        
        if not scraper_path.exists():
            error_msg = f"Fichier scraper introuvable: {scraper_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        spec = importlib.util.spec_from_file_location("scraper_dgccrf", scraper_path)
        scraper_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scraper_module)
        run_scrape = scraper_module.run_scrape
        
        # Préparer les chemins de sortie
        data_dir = base_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        
        # Sources par défaut : toutes les sources disponibles
        default_sources = ['auto', 'prix_homologue', 'liste_produit', 'produit_petrolier']
        sources_to_use = sources if sources else default_sources
        
        # Générer les noms de fichiers avec timestamp pour éviter les écrasements
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_path = csv_out or (data_dir / f'dgccrf_{timestamp}.csv')
        sql_path = sql_out or (data_dir / f'dgccrf_{timestamp}.sql')
        report_path = report_out or (data_dir / f'dgccrf_{timestamp}_report.json')
        
        logger.info(f"Exécution du scraping avec sauvegarde automatique en base de données...")
        
        # Exécuter le scraping avec sauvegarde automatique
        result = run_scrape(
            out=None,  # Pas de JSON de sortie par défaut
            limit=limit,
            sources=sources_to_use,
            save=save,  # Sauvegarde automatique en base de données
            unified=unified,
            csv_out=str(csv_path) if csv_out or not only_changed else None,
            sql_out=str(sql_path) if sql_out or not only_changed else None,
            report_out=str(report_path),
            only_changed=only_changed,
        )
        
        # Lire le rapport pour retourner les statistiques
        stats = {
            'success': True,
            'result_code': result,
            'report_path': str(report_path),
            'sources': sources_to_use,
        }
        
        try:
            if Path(report_path).exists():
                report_data = json.loads(Path(report_path).read_text(encoding='utf-8'))
                stats.update({
                    'total_items': report_data.get('total_items', 0),
                    'source_counts': report_data.get('source_counts', {}),
                    'saved_products': report_data.get('saved_products', 0),
                    'saved_prices': report_data.get('saved_prices', 0),
                    'duration_sec': report_data.get('duration_sec', 0),
                    'timestamp': report_data.get('timestamp', ''),
                })
                
                logger.info(
                    f"Scraping DGCCRF terminé avec succès: "
                    f"{stats.get('total_items', 0)} items extraits, "
                    f"{stats.get('saved_products', 0)} produits sauvegardés, "
                    f"{stats.get('saved_prices', 0)} prix sauvegardés"
                )
            else:
                logger.warning(f"Rapport non généré: {report_path}")
                stats['success'] = False
                stats['error'] = 'Rapport non généré'
        except Exception as e:
            logger.warning(f"Impossible de lire le rapport: {e}", exc_info=True)
            stats['warning'] = f"Impossible de lire le rapport: {e}"
        
        return stats
        
    except Exception as exc:
        logger.error(f"Erreur lors du scraping DGCCRF: {exc}", exc_info=True)
        # Retry avec backoff exponentiel
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task(name="backup_database_task")
def backup_database_task(format_type: str = 'sql', compress: bool = True, keep: int = 7) -> dict:
    """Tâche Celery pour créer un backup de la base de données.
    
    Args:
        format_type: Format du backup ('sql', 'json', ou 'both')
        compress: Compresser le backup SQL
        keep: Nombre de backups à conserver
    
    Returns:
        dict: Statistiques du backup
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Début du backup de la base de données (format: {format_type})")
    
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Exécuter la commande de backup
        output = StringIO()
        call_command(
            'backup_database',
            format=format_type,
            output='backups',
            compress=compress,
            keep=keep,
            stdout=output
        )
        
        result = {
            'success': True,
            'format': format_type,
            'timestamp': timezone.now().isoformat(),
            'message': 'Backup créé avec succès'
        }
        
        logger.info(f"Backup de la base de données terminé: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Erreur lors du backup de la base de données: {exc}", exc_info=True)
        return {
            'success': False,
            'error': str(exc),
            'timestamp': timezone.now().isoformat()
        }


@shared_task(name="monitor_dgccrf_report_task")
def monitor_dgccrf_report_task(report_path: str | None = None) -> int:
    """Vérifie le rapport DGCCRF et alerte si anomalies (ex: total_items == 0).
    Envoie un email si settings.EMAIL_HOST est configuré, sinon log un warning.
    """
    logger = logging.getLogger(__name__)
    try:
        base_dir = Path(getattr(settings, 'BASE_DIR', Path(__file__).resolve().parents[3]))
        target = Path(report_path or (base_dir / 'data' / 'dgccrf_report.json'))
        if not target.exists():
            msg = f"Rapport DGCCRF introuvable: {target}"
            logger.warning(msg)
            try:
                send_mail(
                    subject="[Alerte] Rapport DGCCRF introuvable",
                    message=msg,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[a[1] for a in getattr(settings, 'ADMINS', [])],
                    fail_silently=True,
                )
            except Exception:
                pass
            return 1
        data = json.loads(target.read_text(encoding='utf-8'))
        total = int(data.get('total_items') or 0)
        if total == 0:
            msg = f"Rapport DGCCRF: aucun item collecté ({target})"
            logger.warning(msg)
            try:
                send_mail(
                    subject="[Alerte] DGCCRF: aucun item collecté",
                    message=msg,
                    from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                    recipient_list=[a[1] for a in getattr(settings, 'ADMINS', [])],
                    fail_silently=True,
                )
            except Exception:
                pass
            return 2
        logger.info(f"Rapport DGCCRF OK: total_items={total}")
        return 0
    except Exception as exc:
        logger = logging.getLogger(__name__)
        logger.error(f"Échec monitoring rapport DGCCRF: {exc}")
        return 3


# --- Scrape & Ingest pipeline ---
@shared_task(name="scrape_and_ingest")
def scrape_and_ingest_task(limit: int | None = None, dry_run: bool = False, source: str | None = None) -> int:
    """Exécute la commande de management 'scrape_and_ingest'.
    Paramètres par défaut hérités des variables d'environnement si non fournis.
    """
    if limit is None:
        try:
            env_limit = os.getenv('SCRAPER_LIMIT')
            limit = int(env_limit) if env_limit else None
        except Exception:
            limit = None
    if source is None:
        source = os.getenv('SCRAPER_SOURCE', 'local')

    cmd = ["scrape_and_ingest"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if dry_run:
        cmd.append("--dry-run")
    if source:
        cmd.extend(["--source", source])
    call_command(*cmd)
    return 0


@shared_task
def comparer_prix_homologues_task() -> int:
    """Compare les prix actuels vs. les prix homologués et retourne le nombre d'écarts détectés.
    Stratégie simple: pour chaque produit homologué, si on trouve un produit/magasin avec un prix > X% au-dessus du prix homologué (par unité), on compte l'écart.
    Cette tâche peut être enrichie pour générer des recommandations ou notifications.
    """
    from django.db.models import Min
    ecarts = 0
    # On prend le dernier prix homologué par produit (par date_publication)
    derniers = (PrixHomologue.objects
                .select_related('produit')
                .order_by('produit_id', '-date_publication', '-date_creation'))
    vus = set()
    for ph in derniers:
        if ph.produit_id in vus:
            continue
        vus.add(ph.produit_id)

        # Logique: si unité dispo, comparer prix min actuel par produit (tous magasins) rapporté à l'unité quand possible
        # Hypothèse: le modèle Produit contient quantite_unite (déjà utilisée dans Prix.prix_par_unite)
        produit_nom = ph.produit.nom
        qs = Prix.objects.filter(produit__nom=produit_nom, est_disponible=True)
        prix_actuel_min = qs.aggregate(m=Min('prix_actuel'))['m']
        if prix_actuel_min is None:
            continue

        # Comparaison basique: si prix actuel min > prix homologué de plus de 20%, compter un écart
        try:
            from decimal import Decimal
            seuil = Decimal('1.20')
            if ph.prix_unitaire and prix_actuel_min and (Decimal(prix_actuel_min) > Decimal(ph.prix_unitaire) * seuil):
                ecarts += 1
        except Exception:
            continue

    return ecarts


@shared_task(name="import_dgccrf_task")
def import_dgccrf_task(limit: int | None = None, dry_run: bool = False) -> int:
    """Exécute la commande de management 'import_dgccrf'."""
    cmd = ["import_dgccrf"]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if dry_run:
        cmd.append("--dry-run")
    call_command(*cmd)
    return 0
