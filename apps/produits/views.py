from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Min, Max, F
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .search import search_products, suggest_products
from PIL import Image
import io as _io
import requests
from .models import (
    Categorie, Marque, UniteMesure, Produit,
    AvisProduit, CaracteristiqueProduit, HistoriquePrixProduit,
    Prix, HistoriquePrix,
    AlertePrix, SuggestionPrix, ComparaisonPrix, Offre,
    HomologationProduit, PrixHomologue,
)
from .serializers import (
    CategorieSerializer, MarqueSerializer, UniteMesureSerializer,
    ProduitListSerializer, ProduitDetailSerializer, ProduitCreateUpdateSerializer,
    AvisProduitSerializer, CaracteristiqueProduitSerializer,
    HistoriquePrixProduitSerializer, ProduitRechercheSerializer,
    PrixSerializer, HistoriquePrixSerializer,
    AlertePrixSerializer, SuggestionPrixSerializer, ComparaisonPrixSerializer,
    OffreSerializer, EvolutionPrixSerializer,
)
from .filters import (
    ProduitFilter, CategorieFilter, MarqueFilter, PrixFilter,
    AlertePrixFilter, SuggestionPrixFilter,
)
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Min, Max, Count, StdDev, F
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from decimal import Decimal
import logging
from .tasks import verifier_alertes_prix_task
"""Nettoyage: aucune importation de modèles non présents (AlertePrix, ComparaisonPrix, SuggestionPrix, Offre)."""

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class PrixViewSet(viewsets.ModelViewSet):
    queryset = Prix.objects.select_related(
        'produit', 'produit__categorie', 'produit__marque',
        'magasin'
    ).filter(est_disponible=True)
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PrixFilter
    search_fields = [
        'produit__nom', 'produit__code_barre', 'magasin__nom'
    ]
    ordering_fields = [
        'prix_actuel', 'date_modification', 'confiance_prix'
        # Note: pourcentage_promotion est une propriété, pas un champ DB, donc non triable via order_by
    ]
    ordering = ['prix_actuel']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        # Un seul serializer pour list/detail
        return PrixSerializer
    
    def get_queryset(self):
        requete = super().get_queryset()
        
        # Filtrage par géolocalisation si disponible
        position_utilisateur = self.request.query_params.get('position')
        rayon_km = self.request.query_params.get('rayon_km', 10)
        
        if position_utilisateur:
            # Implémentation simplifiée - à compléter avec PostGIS
            try:
                latitude, longitude = map(float, position_utilisateur.split(','))
                # Filtrage géographique à implémenter
                _ = (latitude, longitude)  # évite l'avertissement variable non utilisée
            except (ValueError, AttributeError):
                pass
        
        return requete
    
    @action(detail=False, methods=['get'])
    def meilleurs_prix(self, request):
        """Retourne les meilleurs prix pour chaque produit"""
        # Agrégation des prix minimum par produit
        from django.db.models import Subquery, OuterRef
        
        # Sous-requête pour obtenir le prix minimum par produit
        sous_requete_prix_min = Prix.objects.filter(
            produit=OuterRef('produit_id'),
            est_disponible=True
        ).order_by('prix_actuel').values('prix_actuel')[:1]
        
        meilleurs_prix_qs = Prix.objects.filter(
            est_disponible=True
        ).annotate(
            prix_min=Subquery(sous_requete_prix_min)
        ).filter(prix_actuel=Subquery(sous_requete_prix_min))
        
        # Appliquer les filtres standard
        meilleurs_prix_qs = self.filter_queryset(meilleurs_prix_qs)
        
        page = self.paginate_queryset(meilleurs_prix_qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(meilleurs_prix_qs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def promotions(self, request):
        """Retourne les produits en promotion"""
        from django.utils import timezone
        start_time = timezone.now()
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
        
        logger.info(
            f"[PRIX] Début requête 'promotions' - User ID: {user_id}, IP: {ip_address}, "
            f"Query params: {dict(request.query_params)}"
        )
        
        try:
            # est_promotion_valide est une propriété, pas un champ DB, donc on filtre seulement sur est_promotion
            queryset = self.get_queryset().filter(est_promotion=True)
            total_count = queryset.count()
            logger.debug(f"[PRIX] Nombre total de prix en promotion trouvés: {total_count}")
            
            produits_en_promotion = list(queryset)
            
            # Trier par pourcentage_promotion (propriété) en Python
            produits_en_promotion.sort(key=lambda x: x.pourcentage_promotion, reverse=True)
            logger.debug(f"[PRIX] Produits triés par pourcentage de promotion décroissant")
            
            page = self.paginate_queryset(produits_en_promotion)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                nb_retournes = len(page)
                elapsed = (timezone.now() - start_time).total_seconds()
                logger.info(
                    f"[PRIX] Requête 'promotions' terminée avec succès (paginée) - "
                    f"Total: {total_count}, Retourné: {nb_retournes}, "
                    f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
                )
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(produits_en_promotion, many=True)
            nb_retournes = len(produits_en_promotion)
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[PRIX] Requête 'promotions' terminée avec succès (non paginée) - "
                f"Total: {total_count}, Retourné: {nb_retournes}, "
                f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
            )
            return Response(serializer.data)
        except Exception as e:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.error(
                f"[PRIX] Erreur lors de la récupération des promotions - "
                f"User ID: {user_id}, IP: {ip_address}, Erreur: {str(e)}, "
                f"Type: {type(e).__name__}, Temps écoulé: {elapsed:.3f}s",
                exc_info=True
            )
            return Response(
                {'erreur': 'Erreur lors de la récupération des promotions'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def historique(self, request, pk=None):
        """Retourne l'historique des prix pour un produit-magasin"""
        prix = self.get_object()
        historique_prix = prix.historique.all().order_by('-date_changement')
        
        page = self.paginate_queryset(historique_prix)
        if page is not None:
            serializer = HistoriquePrixSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = HistoriquePrixSerializer(historique_prix, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def comparaison_produit(self, request):
        """Compare les prix d'un produit spécifique entre magasins"""
        # Accepter soit 'produit_id' soit 'produit' pour compatibilité
        produit_id = request.query_params.get('produit_id') or request.query_params.get('produit')
        if not produit_id:
            return Response(
                {'error': _("Le paramètre produit_id ou produit est requis")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            produit_id = int(produit_id)
        except (ValueError, TypeError):
            return Response(
                {'error': _("Le paramètre produit_id doit être un nombre entier valide")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.produits.models import Produit
        produit = get_object_or_404(Produit, id=produit_id)
        
        prix_du_produit = self.get_queryset().filter(produit=produit)
        
        # Statistiques
        statistiques = prix_du_produit.aggregate(
            prix_min=Min('prix_actuel'),
            prix_max=Max('prix_actuel'),
            prix_moyen=Avg('prix_actuel'),
            nombre_magasins=Count('id'),
            promotions=Count('id', filter=Q(est_promotion=True))
        )
        
        # Prix par magasin
        prix_par_magasin = prix_du_produit.values(
            'magasin_id', 'magasin__nom'
        ).annotate(
            prix_actuel=Min('prix_actuel'),
            est_promotion=Count('id', filter=Q(est_promotion=True))
        ).order_by('prix_actuel')
        
        resultat = {
            'produit': {
                'id': produit.id,
                'nom': produit.nom,
                'image': request.build_absolute_uri(produit.image_principale.url) if produit.image_principale else None
            },
            'statistiques': statistiques,
            'prix_par_magasin': list(prix_par_magasin)
        }
        
        return Response(resultat)
    
    @action(detail=False, methods=['post'])
    def batch(self, request):
        """
        Récupère plusieurs prix en une seule requête (batch).
        
        Body JSON:
        {
            "produit_ids": [1, 2, 3],
            "magasin_ids": [10, 20],  // optionnel
            "include_stats": true,    // optionnel, défaut: true
            "filters": {              // optionnel
                "est_promotion": true,
                "rayon_km": 10
            }
        }
        
        Returns:
        {
            "count": 5,
            "results": [
                {
                    "produit_id": 1,
                    "magasin_id": 10,
                    "prix_actuel": 1500.00,
                    ...
                },
                ...
            ]
        }
        """
        from apps.produits.serializers import BatchPrixRequestSerializer
        from apps.produits.services.price_enrichment import PriceEnrichmentService
        
        # Valider la requête
        request_serializer = BatchPrixRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                request_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        validated_data = request_serializer.validated_data
        produit_ids = validated_data['produit_ids']
        magasin_ids = validated_data.get('magasin_ids')
        include_stats = validated_data.get('include_stats', True)
        filters = validated_data.get('filters', {})
        
        # Limiter à 100 produits
        if len(produit_ids) > 100:
            return Response(
                {'error': _("Maximum 100 produits par requête batch")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Utiliser le service d'enrichissement avec cache
            if magasin_ids:
                # Récupérer les prix pour chaque combinaison produit/magasin
                results = []
                for produit_id in produit_ids:
                    for magasin_id in magasin_ids:
                        enriched = PriceEnrichmentService.get_enriched_price(
                            produit_id=produit_id,
                            magasin_id=magasin_id,
                            include_stats=include_stats
                        )
                        # Appliquer les filtres si nécessaire
                        if filters:
                            if filters.get('est_promotion') and not enriched.get('est_promotion'):
                                continue
                        results.append(enriched)
            else:
                # Récupérer les meilleurs prix pour chaque produit
                results = []
                for produit_id in produit_ids:
                    # Récupérer le meilleur prix (minimum)
                    prix_obj = self.get_queryset().filter(
                        produit_id=produit_id
                    ).order_by('prix_actuel').first()
                    
                    if prix_obj:
                        enriched = PriceEnrichmentService.get_enriched_price(
                            produit_id=produit_id,
                            magasin_id=prix_obj.magasin_id,
                            include_stats=include_stats
                        )
                        # Appliquer les filtres
                        if filters:
                            if filters.get('est_promotion') and not enriched.get('est_promotion'):
                                continue
                        results.append(enriched)
                    else:
                        # Produit sans prix disponible
                        results.append({
                            'produit_id': produit_id,
                            'magasin_id': None,
                            'prix_actuel': None,
                            'disponible': False,
                        })
            
            return Response({
                'count': len(results),
                'results': results
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.exception("Erreur lors de la récupération batch des prix")
            return Response(
                {'error': _("Erreur lors de la récupération des prix"), 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def evolution_prix(self, request):
        """Retourne l'évolution des prix pour un produit"""
        produit_id = request.query_params.get('produit_id')
        jours = int(request.query_params.get('jours', 30))
        
        if not produit_id:
            return Response(
                {'error': _("Le paramètre produit_id est requis")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from apps.produits.models import Produit
        produit = get_object_or_404(Produit, id=produit_id)
        
        # Calculer la date de début
        date_debut = timezone.now() - timedelta(days=jours)
        
        # Récupérer l'historique des prix
        historique_jours = HistoriquePrix.objects.filter(
            prix__produit=produit,
            date_changement__gte=date_debut
        ).values('date_changement__date').annotate(
            prix_moyen=Avg('nouveau_prix'),
            prix_min=Min('nouveau_prix'),
            prix_max=Max('nouveau_prix'),
            nombre_magasins=Count('prix__magasin', distinct=True)
        ).order_by('date_changement__date')
        
        serializer = EvolutionPrixSerializer(historique_jours, many=True)
        return Response(serializer.data)


class AlertePrixViewSet(viewsets.ModelViewSet):
    queryset = AlertePrix.objects.select_related(
        'produit', 'utilisateur'
    ).prefetch_related('magasins')
    
    serializer_class = AlertePrixSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = AlertePrixFilter
    ordering_fields = ['date_creation', 'prix_souhaite']
    ordering = ['-date_creation']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return self.queryset.filter(utilisateur=self.request.user)
    
    @action(detail=True, methods=['post'])
    def desactiver(self, request, pk=None):
        """Désactive une alerte"""
        alerte = self.get_object()
        alerte.est_active = False
        alerte.save()
        
        serializer = self.get_serializer(alerte)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reactiver(self, request, pk=None):
        """Réactive une alerte"""
        alerte = self.get_object()
        alerte.est_active = True
        alerte.save()
        
        serializer = self.get_serializer(alerte)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def alertes_actives(self, request):
        """Retourne les alertes actives de l'utilisateur"""
        alertes_actives_qs = self.get_queryset().filter(est_active=True)
        
        # Vérifier les seuils atteints
        for alerte in alertes_actives_qs:
            if alerte.est_seuil_atteint:
                # Déclencher une notification (à implémenter)
                pass
        
        serializer = self.get_serializer(alertes_actives_qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def lancer_verification(self, request):
        """Déclenche la vérification des alertes de l'utilisateur en tâche Celery."""
        res = verifier_alertes_prix_task.delay(utilisateur_id=request.user.id)
        return Response({'task_id': res.id, 'message': 'Vérification des alertes planifiée.'}, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['post'])
    def lancer_verification_globale(self, request):
        """Déclenche la vérification de toutes les alertes (réservé staff)."""
        if not request.user.is_staff:
            return Response({'error': _('Action réservée aux administrateurs')}, status=status.HTTP_403_FORBIDDEN)
        res = verifier_alertes_prix_task.delay()
        return Response({'task_id': res.id, 'message': 'Vérification globale des alertes planifiée.'}, status=status.HTTP_202_ACCEPTED)


class SuggestionPrixViewSet(viewsets.ModelViewSet):
    queryset = SuggestionPrix.objects.select_related(
        'utilisateur', 'produit', 'magasin'
    )
    
    serializer_class = SuggestionPrixSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = SuggestionPrixFilter
    ordering_fields = ['date_creation', 'date_observation']
    ordering = ['-date_creation']
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Les utilisateurs normaux ne voient que leurs suggestions
        if self.request.user.is_authenticated and not self.request.user.is_staff:
            queryset = queryset.filter(utilisateur=self.request.user)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def approuver(self, request, pk=None):
        """Approuve une suggestion (admin seulement)"""
        if not request.user.is_staff:
            return Response(
                {'error': _("Action réservée aux administrateurs")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        suggestion = self.get_object()
        suggestion.statut = 'approuve'
        suggestion.verifie_par = request.user
        suggestion.date_verification = timezone.now()
        suggestion.save()
        
        # Mettre à jour le prix correspondant
        try:
            prix = Prix.objects.get(
                produit=suggestion.produit,
                magasin=suggestion.magasin
            )
            prix.prix_actuel = suggestion.prix_suggere
            prix.source_prix = 'utilisateur'
            prix.confiance_prix = 0.9  # Confiance élevée pour les prix vérifiés
            prix.save()
        except Prix.DoesNotExist:
            # Créer un nouveau prix
            Prix.objects.create(
                produit=suggestion.produit,
                magasin=suggestion.magasin,
                prix_actuel=suggestion.prix_suggere,
                source_prix='utilisateur',
                confiance_prix=0.9
            )
        
        serializer = self.get_serializer(suggestion)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def rejeter(self, request, pk=None):
        """Rejette une suggestion (admin seulement)"""
        if not request.user.is_staff:
            return Response(
                {'error': _("Action réservée aux administrateurs")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        suggestion = self.get_object()
        suggestion.statut = 'rejete'
        suggestion.verifie_par = request.user
        suggestion.date_verification = timezone.now()
        suggestion.raison_rejet = request.data.get('raison', '')
        suggestion.save()
        
        serializer = self.get_serializer(suggestion)
        return Response(serializer.data)


class StatistiquesPrixViewSet(viewsets.ViewSet):
    """ViewSet pour les statistiques sur les prix"""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def list(self, request):
        """Statistiques générales sur les prix"""
        statistiques = {
            'total_prix': Prix.objects.filter(est_disponible=True).count(),
            'prix_moyen_global': Prix.objects.filter(
                est_disponible=True
            ).aggregate(avg=Avg('prix_actuel'))['avg'],
            'promotions_actives': Prix.objects.filter(
                est_promotion=True
            ).count(),
            'produits_sans_prix': Prix.objects.filter(
                est_disponible=False
            ).count(),
            'evolution_7_jours': self.get_evolution_prix(7),
            'top_promotions': self.get_top_promotions(),
        }
        
        return Response(statistiques)
    
    def get_evolution_prix(self, jours):
        """Calcule l'évolution des prix sur N jours"""
        date_debut = timezone.now() - timedelta(days=jours)
        
        historique_fenetre = HistoriquePrix.objects.filter(
            date_changement__gte=date_debut
        ).aggregate(
            variation_moyenne=Avg('pourcentage_variation'),
            hausses=Count('id', filter=Q(variation__gt=0)),
            baisses=Count('id', filter=Q(variation__lt=0))
        )
        
        return historique_fenetre
    
    def get_top_promotions(self):
        """Retourne les meilleures promotions"""
        promos_qs = list(Prix.objects.filter(
            est_promotion=True
        ))
        
        # Trier par pourcentage_promotion (propriété) en Python
        promos_qs.sort(key=lambda x: x.pourcentage_promotion, reverse=True)
        promos_qs = promos_qs[:10]
        
        return [{
            'produit': prix.produit.nom,
            'magasin': prix.magasin.nom,
            'pourcentage_promotion': float(prix.pourcentage_promotion),
            'prix_actuel': float(prix.prix_actuel),
            'prix_origine': float(prix.prix_origine) if prix.prix_origine else None
        } for prix in promos_qs]


class ComparaisonPrixViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ComparaisonPrix.objects.select_related(
        'produit', 'magasin_prix_min', 'magasin_prix_max'
    ).all()
    
    serializer_class = ComparaisonPrixSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    ordering = ['-date_comparaison']
    
    @action(detail=False, methods=['get'])
    def generer_comparaison(self, request):
        """Génère une nouvelle comparaison de prix pour tous les produits"""
        if not request.user.is_staff:
            return Response(
                {'error': _("Action réservée aux administrateurs")},
                status=status.HTTP_403_FORBIDDEN
            )
        
        from apps.produits.models import Produit
        from django.db import transaction
        
        produits_actifs = Produit.objects.filter(est_actif=True)
        comparaisons_creees = 0
        
        with transaction.atomic():
            for produit in produits_actifs:
                prix_du_produit = Prix.objects.filter(
                    produit=produit, est_disponible=True
                )
                
                if prix_du_produit.count() < 2:  # Au moins 2 magasins pour comparer
                    continue
                
                statistiques = prix_du_produit.aggregate(
                    prix_min=Min('prix_actuel'),
                    prix_max=Max('prix_actuel'),
                    prix_moyen=Avg('prix_actuel'),
                    nombre_magasins=Count('id'),
                    ecart_type=StdDev('prix_actuel')
                )
                
                if not all(statistiques.values()):
                    continue
                
                # Trouver les magasins avec prix min/max
                magasin_au_prix_minimum = prix_du_produit.filter(
                    prix_actuel=statistiques['prix_min']
                ).first().magasin
                
                magasin_au_prix_maximum = prix_du_produit.filter(
                    prix_actuel=statistiques['prix_max']
                ).first().magasin
                
                # Calculer le coefficient de variation
                coefficient_de_variation = (statistiques['ecart_type'] / statistiques['prix_moyen']) * 100 if statistiques['prix_moyen'] else 0
                
                # Créer la comparaison
                ComparaisonPrix.objects.create(
                    produit=produit,
                    prix_minimum=statistiques['prix_min'],
                    prix_maximum=statistiques['prix_max'],
                    prix_moyen=statistiques['prix_moyen'],
                    nombre_magasins=statistiques['nombre_magasins'],
                    ecart_type=statistiques['ecart_type'],
                    coefficient_variation=coefficient_de_variation,
                    magasin_prix_min=magasin_au_prix_minimum,
                    magasin_prix_max=magasin_au_prix_maximum
                )
                
                comparaisons_creees += 1
        
        return Response({
            'message': f'{comparaisons_creees} comparaisons générées avec succès'
        })


class HomologationsStatsViewSet(viewsets.ViewSet):
    """Statistiques de contrôle pour l'import des prix homologués DGCCRF."""
    permission_classes = [IsAuthenticatedOrReadOnly]

    def list(self, request):
        from django.db.models import Count
        par_dates = (PrixHomologue.objects
                     .values('date_publication')
                     .annotate(count=Count('id'))
                     .order_by('-date_publication')[:10])

        par_localisation = (PrixHomologue.objects
                             .values('localisation')
                             .annotate(count=Count('id'))
                             .order_by('-count'))

        total = PrixHomologue.objects.count()

        return Response({
            'total': total,
            'par_dates': list(par_dates),
            'par_localisation': list(par_localisation),
        })


class OffreViewSet(viewsets.ReadOnlyModelViewSet):
    """Offres unifiées (produit x magasin) pour des requêtes simples côté front/API."""
    queryset = Offre.objects.select_related('produit', 'magasin').all()
    serializer_class = OffreSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['produit', 'magasin', 'est_promotion']
    search_fields = ['produit__nom', 'magasin__nom']
    ordering_fields = ['prix_actuel', 'date_observation', 'popularity_count', 'recommendation_score']
    ordering = ['prix_actuel']

    def get_queryset(self):
        qs = super().get_queryset()
        min_prix = self.request.query_params.get('min_prix')
        max_prix = self.request.query_params.get('max_prix')
        if min_prix:
            try:
                qs = qs.filter(prix_actuel__gte=float(min_prix))
            except ValueError:
                pass
        if max_prix:
            try:
                qs = qs.filter(prix_actuel__lte=float(max_prix))
            except ValueError:
                pass
        return qs


class CategorieViewSet(viewsets.ModelViewSet):
    queryset = Categorie.objects.prefetch_related('sous_categories').all()
    serializer_class = CategorieSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CategorieFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom', 'ordre', 'date_creation']
    ordering = ['ordre', 'nom']
    pagination_class = StandardResultsSetPagination
    
    @action(detail=True, methods=['get'])
    def produits(self, request, pk=None):
        """Retourne les produits d'une catégorie (incluant les sous-catégories)"""
        categorie = self.get_object()
        
        # Récupérer toutes les sous-catégories
        def get_sous_categories_ids(cat):
            ids = [cat.id]
            for sous_cat in cat.sous_categories.all():
                ids.extend(get_sous_categories_ids(sous_cat))
            return ids
        
        categories_ids = get_sous_categories_ids(categorie)
        produits = Produit.objects.filter(
            categorie_id__in=categories_ids, 
            est_actif=True
        ).select_related('categorie', 'marque')
        
        # Pagination
        page = self.paginate_queryset(produits)
        if page is not None:
            serializer = ProduitListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProduitListSerializer(produits, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def racines(self, request):
        """Retourne uniquement les catégories racines"""
        categories_racines = Categorie.objects.filter(parent__isnull=True)
        serializer = self.get_serializer(categories_racines, many=True)
        return Response(serializer.data)


class MarqueViewSet(viewsets.ModelViewSet):
    queryset = Marque.objects.annotate(
        nombre_produits=Count('produits', filter=Q(produits__est_actif=True))
    ).all()
    serializer_class = MarqueSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = MarqueFilter
    search_fields = ['nom', 'description', 'pays_origine']
    ordering_fields = ['nom', 'nombre_produits', 'date_creation']
    ordering = ['nom']
    pagination_class = StandardResultsSetPagination


class UniteMesureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UniteMesure.objects.all()
    serializer_class = UniteMesureSerializer
    pagination_class = None  # Pas de pagination pour les unités de mesure


class ProduitViewSet(viewsets.ModelViewSet):
    queryset = Produit.objects.select_related(
        'categorie', 'marque', 'unite_mesure'
    ).prefetch_related(
        'caracteristiques', 'avis'
    ).filter(est_actif=True)
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProduitFilter
    search_fields = ['nom', 'code_barre', 'marque__nom']
    ordering_fields = [
        'nom', 'date_creation', 'prix_moyen_agg', 'prix_min_agg', 'prix_max_agg'
        # Utiliser les annotations prix_moyen_agg, prix_min_agg, prix_max_agg au lieu de prix_moyen
    ]
    ordering = ['nom']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProduitListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProduitCreateUpdateSerializer
        return ProduitDetailSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Annoter avec les prix agrégés pour toutes les actions (list et retrieve)
        queryset = queryset.annotate(
            prix_moyen_agg=Avg('prix__prix_actuel'),
            prix_min_agg=Min('prix__prix_actuel'),
            prix_max_agg=Max('prix__prix_actuel'),
            nombre_magasins_agg=Count('prix', distinct=True)
        )
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Liste des produits avec logs détaillés"""
        from django.utils import timezone
        start_time = timezone.now()
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
        
        # Extraire les paramètres de filtrage importants
        prix_min = request.query_params.get('prix_min')
        prix_max = request.query_params.get('prix_max')
        ordering = request.query_params.get('ordering')
        search = request.query_params.get('search')
        page = request.query_params.get('page', 1)
        page_size = request.query_params.get('page_size')
        
        logger.info(
            f"[PRODUITS] Début requête 'list' - User ID: {user_id}, IP: {ip_address}, "
            f"Prix min: {prix_min}, Prix max: {prix_max}, Ordering: {ordering}, "
            f"Search: {search}, Page: {page}, Page size: {page_size}"
        )
        
        try:
            # Appeler la méthode parent pour le traitement normal
            response = super().list(request, *args, **kwargs)
            
            # Compter les résultats retournés
            if hasattr(response, 'data') and isinstance(response.data, dict):
                count = response.data.get('count', len(response.data.get('results', [])))
                results_count = len(response.data.get('results', []))
            else:
                count = results_count = 'unknown'
            
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[PRODUITS] Requête 'list' terminée avec succès - User ID: {user_id}, "
                f"Total: {count}, Résultats page: {results_count}, "
                f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
            )
            
            return response
        except Exception as e:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.error(
                f"[PRODUITS] Erreur lors de la récupération de la liste des produits - "
                f"User ID: {user_id}, IP: {ip_address}, Prix min: {prix_min}, Prix max: {prix_max}, "
                f"Ordering: {ordering}, Erreur: {str(e)}, Type: {type(e).__name__}, "
                f"Temps écoulé: {elapsed:.3f}s",
                exc_info=True
            )
            raise
    
    def get_object(self):
        """Surcharge pour s'assurer que l'objet a les annotations"""
        obj = super().get_object()
        # S'assurer que les annotations sont présentes même pour retrieve
        if not hasattr(obj, 'prix_moyen_agg'):
            from django.db.models import Avg, Min, Max, Count
            queryset = self.get_queryset().filter(pk=obj.pk)
            obj = queryset.first() or obj
        return obj
    
    @action(detail=True, methods=['get'])
    def avis(self, request, pk=None):
        """Retourne les avis d'un produit"""
        produit = self.get_object()
        avis = produit.avis.select_related('utilisateur').all()
        
        page = self.paginate_queryset(avis)
        if page is not None:
            serializer = AvisProduitSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = AvisProduitSerializer(avis, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def historique_prix(self, request, pk=None):
        """Retourne l'historique des prix du produit"""
        produit = self.get_object()
        historique = produit.historique_prix.all().order_by('-date')[:30]  # 30 derniers jours
        
        serializer = HistoriquePrixProduitSerializer(historique, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tous(self, request):
        """Retourne TOUS les produits de la base de données (actifs et inactifs)"""
        from django.utils import timezone
        start_time = timezone.now()
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
        
        logger.info(
            f"[PRODUITS] Début requête 'tous' (tous les produits) - User ID: {user_id}, IP: {ip_address}, "
            f"Query params: {dict(request.query_params)}"
        )
        
        try:
            # Récupérer tous les produits (actifs et inactifs)
            queryset = Produit.objects.select_related(
                'categorie', 'marque', 'unite_mesure'
            ).prefetch_related(
                'caracteristiques', 'avis'
            ).all()  # Pas de filtre est_actif
            
            # Annoter avec les prix agrégés
            queryset = queryset.annotate(
                prix_moyen_agg=Avg('prix__prix_actuel'),
                prix_min_agg=Min('prix__prix_actuel'),
                prix_max_agg=Max('prix__prix_actuel'),
                nombre_magasins_agg=Count('prix', distinct=True)
            )
            
            total_count = queryset.count()
            logger.debug(f"[PRODUITS] Nombre total de produits (actifs + inactifs): {total_count}")
            
            # Appliquer la pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ProduitListSerializer(page, many=True)
                nb_retournes = len(page)
                elapsed = (timezone.now() - start_time).total_seconds()
                logger.info(
                    f"[PRODUITS] Requête 'tous' terminée avec succès (paginée) - "
                    f"Total: {total_count}, Retourné: {nb_retournes}, "
                    f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
                )
                return self.get_paginated_response(serializer.data)
            
            serializer = ProduitListSerializer(queryset, many=True)
            nb_retournes = len(queryset)
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[PRODUITS] Requête 'tous' terminée avec succès (non paginée) - "
                f"Total: {total_count}, Retourné: {nb_retournes}, "
                f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
            )
            return Response(serializer.data)
        except Exception as e:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.error(
                f"[PRODUITS] Erreur lors de la récupération de tous les produits - "
                f"User ID: {user_id}, IP: {ip_address}, Erreur: {str(e)}, "
                f"Type: {type(e).__name__}, Temps écoulé: {elapsed:.3f}s",
                exc_info=True
            )
            return Response(
                {'erreur': 'Erreur lors de la récupération des produits'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def defiscalises(self, request):
        """Retourne tous les produits défiscalisés"""
        from django.utils import timezone
        from django.db.models import Q
        start_time = timezone.now()
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
        
        logger.info(
            f"[PRODUITS] Début requête 'defiscalises' - User ID: {user_id}, IP: {ip_address}, "
            f"Query params: {dict(request.query_params)}"
        )
        
        try:
            queryset = self.get_queryset()
            
            # Appliquer le filtre défiscalisé
            categories_defiscalisees = ['Alimentaire', 'Médicament', 'Équipement médical']
            queryset = queryset.filter(
                Q(categorie__nom__in=categories_defiscalisees) |
                Q(categorie__sous_categories__nom__in=categories_defiscalisees)
            ).distinct()
            
            total_count = queryset.count()
            logger.debug(f"[PRODUITS] Nombre de produits défiscalisés trouvés: {total_count}")
            
            # Appliquer la pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ProduitListSerializer(page, many=True)
                nb_retournes = len(page)
                elapsed = (timezone.now() - start_time).total_seconds()
                logger.info(
                    f"[PRODUITS] Requête 'defiscalises' terminée avec succès (paginée) - "
                    f"Total: {total_count}, Retourné: {nb_retournes}, "
                    f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
                )
                return self.get_paginated_response(serializer.data)
            
            serializer = ProduitListSerializer(queryset, many=True)
            nb_retournes = len(queryset)
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[PRODUITS] Requête 'defiscalises' terminée avec succès (non paginée) - "
                f"Total: {total_count}, Retourné: {nb_retournes}, "
                f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
            )
            return Response(serializer.data)
        except Exception as e:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.error(
                f"[PRODUITS] Erreur lors de la récupération des produits défiscalisés - "
                f"User ID: {user_id}, IP: {ip_address}, Erreur: {str(e)}, "
                f"Type: {type(e).__name__}, Temps écoulé: {elapsed:.3f}s",
                exc_info=True
            )
            return Response(
                {'erreur': 'Erreur lors de la récupération des produits défiscalisés'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def homologues(self, request):
        """Retourne tous les produits homologués (correspondance avec HomologationProduit)"""
        from django.utils import timezone
        from django.db.models import Q, Exists, OuterRef
        start_time = timezone.now()
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
        
        logger.info(
            f"[PRODUITS] Début requête 'homologues' - User ID: {user_id}, IP: {ip_address}, "
            f"Query params: {dict(request.query_params)}"
        )
        
        try:
            queryset = self.get_queryset()
            
            # Vérifier si un produit correspond à un HomologationProduit par nom
            homologations = HomologationProduit.objects.filter(
                Q(nom__iexact=OuterRef('nom')) |
                Q(nom__icontains=OuterRef('nom'))
            )
            queryset = queryset.annotate(
                est_homologue_agg=Exists(homologations)
            ).filter(est_homologue_agg=True)
            
            total_count = queryset.count()
            logger.debug(f"[PRODUITS] Nombre de produits homologués trouvés: {total_count}")
            
            # Appliquer la pagination
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = ProduitListSerializer(page, many=True)
                nb_retournes = len(page)
                elapsed = (timezone.now() - start_time).total_seconds()
                logger.info(
                    f"[PRODUITS] Requête 'homologues' terminée avec succès (paginée) - "
                    f"Total: {total_count}, Retourné: {nb_retournes}, "
                    f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
                )
                return self.get_paginated_response(serializer.data)
            
            serializer = ProduitListSerializer(queryset, many=True)
            nb_retournes = len(queryset)
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[PRODUITS] Requête 'homologues' terminée avec succès (non paginée) - "
                f"Total: {total_count}, Retourné: {nb_retournes}, "
                f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
            )
            return Response(serializer.data)
        except Exception as e:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.error(
                f"[PRODUITS] Erreur lors de la récupération des produits homologués - "
                f"User ID: {user_id}, IP: {ip_address}, Erreur: {str(e)}, "
                f"Type: {type(e).__name__}, Temps écoulé: {elapsed:.3f}s",
                exc_info=True
            )
            return Response(
                {'erreur': 'Erreur lors de la récupération des produits homologués'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def ajouter_avis(self, request, pk=None):
        """Ajoute un avis au produit"""
        produit = self.get_object()
        serializer = AvisProduitSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save(produit=produit)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def recherche_avancee(self, request):
        """Recherche avancée de produits avec filtres multiples"""
        queryset = self.filter_queryset(self.get_queryset())
        
        # Filtres supplémentaires
        prix_min = request.query_params.get('prix_min')
        prix_max = request.query_params.get('prix_max')
        note_min = request.query_params.get('note_min')
        
        try:
            if prix_min:
                prix_min_decimal = Decimal(str(prix_min))
                queryset = queryset.filter(prix_moyen_agg__gte=prix_min_decimal)
            if prix_max:
                prix_max_decimal = Decimal(str(prix_max))
                queryset = queryset.filter(prix_moyen_agg__lte=prix_max_decimal)
        except (ValueError, TypeError) as e:
            logger.warning(f"Erreur de conversion prix_min/prix_max: {e}")
            return Response(
                {'error': _("Les paramètres prix_min et prix_max doivent être des nombres valides")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if note_min:
            try:
                note_min_float = float(note_min)
                # Filtrer par note moyenne des avis
                queryset = queryset.annotate(
                    note_moyenne=Avg('avis__note')
                ).filter(note_moyenne__gte=note_min_float)
            except (ValueError, TypeError):
                return Response(
                    {'error': _("Le paramètre note_min doit être un nombre valide")},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='populaires')
    def populaires(self, request):
        """Retourne les produits les plus populaires (activités/prix disponibles)."""
        queryset = (
            self.get_queryset()
            .annotate(
                nb_prix=Count('prix', distinct=True),
                nb_avis=Count('avis', distinct=True),
            )
            .filter(nb_prix__gt=0)
            .annotate(score_popularite=F('nb_prix') * 2 + F('nb_avis'))
            .order_by('-score_popularite', '-nb_prix', '-date_creation')
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProduitListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        limit = request.query_params.get('limit')
        try:
            limit_value = max(1, min(int(limit), 100)) if limit else 12
        except (TypeError, ValueError):
            limit_value = 12

        serializer = ProduitListSerializer(queryset[:limit_value], many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Suggestions de produits basées sur la recherche"""
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response([])
        
        # Recherche dans les noms et marques
        suggestions = Produit.objects.filter(
            Q(nom__icontains=query) | Q(marque__nom__icontains=query),
            est_actif=True
        )[:10]  # Limiter à 10 suggestions
        
        serializer = ProduitListSerializer(suggestions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def es_search(self, request):
        """Recherche full-text via Elasticsearch."""
        q = request.query_params.get('q', '')
        if not q or len(q) < 2:
            return Response({'results': [], 'total': 0})
        try:
            size = int(request.query_params.get('size', '20'))
            offset = int(request.query_params.get('offset', '0'))
        except ValueError:
            size, offset = 20, 0
        res = search_products(q, size=size, offset=offset)
        hits = res.get('hits', {})
        total = hits.get('total', {}).get('value', 0)
        items = [h.get('_source') for h in hits.get('hits', [])]
        return Response({'results': items, 'total': total})

    @action(detail=False, methods=['get'])
    def es_suggest(self, request):
        """Suggestions via Elasticsearch completion suggester."""
        prefix = request.query_params.get('q', '')
        if not prefix or len(prefix) < 1:
            return Response([])
        res = suggest_products(prefix, size=int(request.query_params.get('size', '5')))
        suggests = res.get('suggest', {}).get('product-suggest', [])
        options = []
        for bucket in suggests:
            for opt in bucket.get('options', []):
                options.append(opt.get('text'))
        return Response(options)

    @action(detail=False, methods=['post'])
    def scan(self, request):
        """Analyse une image téléchargée pour extraire un code-barres, sinon OCR pour détecter un code EAN.
        Si un code est trouvé, tente de récupérer les infos via OpenFoodFacts.
        Body: form-data avec 'image' (fichier).
        """
        f = request.FILES.get('image')
        if not f:
            return Response({'error': 'Aucun fichier image fourni (clé image).'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            img_bytes = f.read()
            image = Image.open(_io.BytesIO(img_bytes))
        except Exception:
            return Response({'error': "Image invalide."}, status=status.HTTP_400_BAD_REQUEST)

        # 1) Essayer de décoder un code-barres
        ean = None
        try:
            # Import paresseux pour éviter l'erreur de DLL manquante au démarrage
            from pyzbar.pyzbar import decode as decode_barcode  # type: ignore
            for symbol in decode_barcode(image):
                val = symbol.data.decode('utf-8')
                if val and val.isdigit() and 8 <= len(val) <= 14:
                    ean = val
                    break
        except Exception:
            # Si pyzbar ou la DLL ZBar est manquante, on passe à l'OCR
            pass

        # 2) Fallback: OCR pour détecter une suite de chiffres type EAN
        if not ean:
            try:
                # Import paresseux de pytesseract
                import pytesseract  # type: ignore
                text = pytesseract.image_to_string(image)
                # détecter un bloc de 8-14 chiffres
                import re
                m = re.search(r"\b(\d{8,14})\b", text)
                if m:
                    ean = m.group(1)
            except Exception:
                pass

        result = {'code_barre': ean}
        # 3) Tenter la récupération via OpenFoodFacts si EAN trouvé
        if ean:
            try:
                off = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{ean}.json", timeout=5).json()
                if off.get('status') == 1:
                    p = off.get('product', {})
                    prefill = {
                        'nom': p.get('product_name') or p.get('generic_name'),
                        'marque_nom': (p.get('brands') or '').split(',')[0].strip() if p.get('brands') else None,
                        'categorie_nom': (p.get('categories') or '').split(',')[0].strip() if p.get('categories') else None,
                        'image_url': p.get('image_front_url') or p.get('image_url'),
                        'nutri_score': p.get('nutriscore_grade'),
                    }
                    result['prefill'] = prefill
            except Exception:
                pass

        return Response(result)
    
    @action(detail=True, methods=['get', 'post'])
    def comparer(self, request, pk=None):
        """Compare ce produit avec d'autres produits
        
        GET: Récupère les produits similaires pour comparaison (public)
        POST: Compare ce produit avec une liste de produits spécifiés (authentifié)
        """
        produit_principal = self.get_object()
        
        if request.method == 'GET':
            # Pour GET, retourner les produits similaires de la même catégorie
            produits_similaires = Produit.objects.filter(
                categorie=produit_principal.categorie,
                est_actif=True
            ).exclude(id=produit_principal.id).select_related('categorie', 'marque', 'unite_mesure')[:10]
            
            comparaison = {
                'produit_principal': ProduitDetailSerializer(produit_principal).data,
                'produits_similaires': ProduitListSerializer(produits_similaires, many=True).data,
                'critères': ['prix', 'caractéristiques', 'notes']
            }
            return Response(comparaison)
        
        # POST: Comparaison avec produits spécifiés (nécessite authentification)
        if not request.user.is_authenticated:
            return Response(
                {'error': _("Authentification requise pour la comparaison personnalisée")},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        produits_ids = request.data.get('produits_ids', [])
        
        if not produits_ids:
            return Response(
                {'error': _("Aucun produit à comparer spécifié")},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les produits à comparer
        produits_a_comparer = Produit.objects.filter(
            id__in=produits_ids, 
            est_actif=True
        ).select_related('categorie', 'marque', 'unite_mesure')
        
        # Préparer les données de comparaison
        comparaison = {
            'produit_principal': ProduitDetailSerializer(produit_principal).data,
            'produits_comparaison': ProduitListSerializer(produits_a_comparer, many=True).data,
            'critères': ['prix', 'caractéristiques', 'notes']
        }
        
        return Response(comparaison)
    
    @action(detail=True, methods=['get'], url_path='comparaison')
    def comparaison(self, request, pk=None):
        """Alias GET pour la comparaison (compatibilité frontend)"""
        return self.comparer(request, pk)
    
    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Liker ou unliker un produit (nécessite authentification)"""
        # La permission IsAuthenticated va gérer l'authentification automatiquement
        # On log juste pour déboguer si nécessaire
        auth_header = request.META.get('HTTP_AUTHORIZATION', 'Non fourni')
        logger.debug(
            f"[PRODUITS] Requête 'like' - User: {request.user}, "
            f"Authentifié: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else 'N/A'}, "
            f"Auth Header présent: {bool(auth_header and auth_header != 'Non fourni')}, "
            f"Produit ID: {pk}, Method: {request.method}"
        )
        
        produit = self.get_object()
        from .models import ProduitLike
        
        try:
            if request.method == 'POST':
                # Liker le produit
                like, created = ProduitLike.objects.get_or_create(
                    utilisateur=request.user,
                    produit=produit
                )
                if created:
                    logger.info(f"[PRODUITS] Produit {produit.id} liké par User ID: {request.user.id}")
                    return Response({
                        'message': _('Produit ajouté aux favoris'),
                        'liked': True,
                        'produit_id': produit.id
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'message': _('Produit déjà dans vos favoris'),
                        'liked': True,
                        'produit_id': produit.id
                    }, status=status.HTTP_200_OK)
            
            elif request.method == 'DELETE':
                # Unliker le produit
                deleted = ProduitLike.objects.filter(
                    utilisateur=request.user,
                    produit=produit
                ).delete()[0]
                
                if deleted:
                    logger.info(f"[PRODUITS] Produit {produit.id} unliké par User ID: {request.user.id}")
                    return Response({
                        'message': _('Produit retiré des favoris'),
                        'liked': False,
                        'produit_id': produit.id
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'message': _('Produit non trouvé dans vos favoris'),
                        'liked': False,
                        'produit_id': produit.id
                    }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(
                f"[PRODUITS] Erreur lors du like/unlike - User ID: {request.user.id}, "
                f"Produit ID: {produit.id}, Erreur: {str(e)}",
                exc_info=True
            )
            return Response({
                'erreur': _('Une erreur est survenue lors de l\'opération'),
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mes_likes(self, request):
        """Retourne tous les produits likés par l'utilisateur connecté"""
        # La permission IsAuthenticated va gérer l'authentification automatiquement
        auth_header = request.META.get('HTTP_AUTHORIZATION', 'Non fourni')
        logger.debug(
            f"[PRODUITS] Requête 'mes_likes' - User: {request.user}, "
            f"Authentifié: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else 'N/A'}, "
            f"Auth Header présent: {bool(auth_header and auth_header != 'Non fourni')}"
        )
        
        from .models import ProduitLike
        from django.utils import timezone
        
        start_time = timezone.now()
        ip_address = request.META.get('REMOTE_ADDR', 'unknown')
        user_id = request.user.id
        
        logger.info(
            f"[PRODUITS] Début requête 'mes_likes' - User ID: {user_id}, IP: {ip_address}"
        )
        
        try:
            likes = ProduitLike.objects.filter(
                utilisateur=request.user
            ).select_related('produit', 'produit__categorie', 'produit__marque', 'produit__unite_mesure')
            
            # Annoter avec les prix agrégés
            likes = likes.annotate(
                prix_moyen_agg=Avg('produit__prix__prix_actuel'),
                prix_min_agg=Min('produit__prix__prix_actuel'),
                prix_max_agg=Max('produit__prix__prix_actuel'),
                nombre_magasins_agg=Count('produit__prix', distinct=True)
            ).order_by('-date_creation')
            
            total_count = likes.count()
            logger.debug(f"[PRODUITS] Nombre de produits likés trouvés: {total_count}")
            
            # Pagination
            page = self.paginate_queryset(likes)
            if page is not None:
                # Extraire les produits de la page
                produits = [like.produit for like in page]
                serializer = ProduitListSerializer(produits, many=True)
                nb_retournes = len(page)
                elapsed = (timezone.now() - start_time).total_seconds()
                logger.info(
                    f"[PRODUITS] Requête 'mes_likes' terminée avec succès (paginée) - "
                    f"Total: {total_count}, Retourné: {nb_retournes}, "
                    f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
                )
                return self.get_paginated_response(serializer.data)
            
            # Sans pagination
            produits = [like.produit for like in likes]
            serializer = ProduitListSerializer(produits, many=True)
            nb_retournes = len(produits)
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[PRODUITS] Requête 'mes_likes' terminée avec succès (non paginée) - "
                f"Total: {total_count}, Retourné: {nb_retournes}, "
                f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
            )
            return Response(serializer.data)
        except Exception as e:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.error(
                f"[PRODUITS] Erreur lors de la récupération des produits likés - "
                f"User ID: {user_id}, IP: {ip_address}, Erreur: {str(e)}, "
                f"Type: {type(e).__name__}, Temps écoulé: {elapsed:.3f}s",
                exc_info=True
            )
            return Response(
                {'erreur': 'Erreur lors de la récupération des produits likés'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AvisProduitViewSet(viewsets.ModelViewSet):
    queryset = AvisProduit.objects.select_related('produit', 'utilisateur').all()
    serializer_class = AvisProduitSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrer par produit si spécifié
        produit_id = self.request.query_params.get('produit')
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
        
        # Filtrer par utilisateur si spécifié
        utilisateur_id = self.request.query_params.get('utilisateur')
        if utilisateur_id:
            queryset = queryset.filter(utilisateur_id=utilisateur_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(utilisateur=self.request.user)


class CaracteristiqueProduitViewSet(viewsets.ModelViewSet):
    queryset = CaracteristiqueProduit.objects.all()
    serializer_class = CaracteristiqueProduitSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = None
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtrer par produit si spécifié
        produit_id = self.request.query_params.get('produit')
        if produit_id:
            queryset = queryset.filter(produit_id=produit_id)
        
        return queryset


class StatistiquesProduitViewSet(viewsets.ViewSet):
    """ViewSet pour les statistiques des produits"""
    
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def list(self, request):
        """Statistiques générales sur les produits"""
        from django.db.models import Count, Avg
        
        stats = {
            'total_produits': Produit.objects.filter(est_actif=True).count(),
            'total_categories': Categorie.objects.count(),
            'total_marques': Marque.objects.count(),
            'produits_sans_prix': Produit.objects.filter(
                est_actif=True, 
                prix__isnull=True
            ).count(),
            'moyenne_prix': Produit.objects.filter(
                est_actif=True
            ).aggregate(moyenne=Avg('prix__prix_actuel'))['moyenne'],
            'top_categories': Categorie.objects.annotate(
                nb_produits=Count('produits', filter=Q(produits__est_actif=True))
            ).order_by('-nb_produits')[:5].values('nom', 'nb_produits'),
            'top_marques': Marque.objects.annotate(
                nb_produits=Count('produits', filter=Q(produits__est_actif=True))
            ).order_by('-nb_produits')[:5].values('nom', 'nb_produits')
        }
        
        return Response(stats)