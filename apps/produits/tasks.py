from celery import shared_task
from django.core.management import call_command
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import os

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
