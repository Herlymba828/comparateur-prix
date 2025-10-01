from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Min, Max
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
from django.db.models import Q, Avg, Min, Max, Count, StdDev
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from .tasks import verifier_alertes_prix_task
"""Nettoyage: aucune importation de modèles non présents (AlertePrix, ComparaisonPrix, SuggestionPrix, Offre)."""


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
        'prix_actuel', 'date_modification', 'pourcentage_promotion',
        'confiance_prix'
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
        produits_en_promotion = self.get_queryset().filter(
            est_promotion=True,
            est_promotion_valide=True
        ).order_by('-pourcentage_promotion')
        
        page = self.paginate_queryset(produits_en_promotion)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(produits_en_promotion, many=True)
        return Response(serializer.data)
    
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
        produit_id = request.query_params.get('produit_id')
        if not produit_id:
            return Response(
                {'error': _("Le paramètre produit_id est requis")},
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
                est_promotion=True, est_promotion_valide=True
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
        promos_qs = Prix.objects.filter(
            est_promotion=True, est_promotion_valide=True
        ).order_by('-pourcentage_promotion')[:10]
        
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

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


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
        'nom', 'date_creation', 'prix_moyen', 'prix_min', 'prix_max'
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
        
        # Annoter avec les prix agrégés
        queryset = queryset.annotate(
            prix_moyen_agg=Avg('prix__prix_actuel'),
            prix_min_agg=Min('prix__prix_actuel'),
            prix_max_agg=Max('prix__prix_actuel'),
            nombre_magasins_agg=Count('prix', distinct=True)
        )
        
        return queryset
    
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
        
        if prix_min:
            queryset = queryset.filter(prix_moyen_agg__gte=prix_min)
        if prix_max:
            queryset = queryset.filter(prix_moyen_agg__lte=prix_max)
        if note_min:
            # Filtrer par note moyenne des avis
            queryset = queryset.annotate(
                note_moyenne=Avg('avis__note')
            ).filter(note_moyenne__gte=note_min)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
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
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def comparer(self, request, pk=None):
        """Compare ce produit avec d'autres produits"""
        produit_principal = self.get_object()
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