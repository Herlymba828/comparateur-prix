import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django.apps import apps
from django.utils import timezone

logger = logging.getLogger(__name__)

from .models import HistoriqueRecommandation, FeedbackRecommandation, ModeleML
from .serializers import (
    HistoriqueRecommandationSerializer,
    FeedbackRecommandationSerializer,
    ModeleMLSerializer,
    RecommandationRequestSerializer,
    PredictionPrixRequestSerializer,
    ProduitRecommandationSerializer
)
from .modeles_ml import GestionnaireRecommandations

class HistoriqueRecommandationViewSet(viewsets.ModelViewSet):
    serializer_class = HistoriqueRecommandationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return HistoriqueRecommandation.objects.filter(utilisateur=self.request.user)

    @action(detail=True, methods=['post'])
    def marquer_vue(self, request, pk=None):
        """Marque une recommandation comme visualisée"""
        recommandation = self.get_object()
        recommandation.date_visualisation = timezone.now()
        recommandation.save()
        return Response({'status': 'marquée comme vue'})

    @action(detail=True, methods=['post'])
    def marquer_clique(self, request, pk=None):
        """Marque une recommandation comme cliquée"""
        recommandation = self.get_object()
        recommandation.a_ete_clique = True
        recommandation.save()
        return Response({'status': 'marquée comme cliquée'})

class FeedbackRecommandationViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackRecommandationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FeedbackRecommandation.objects.filter(historique__utilisateur=self.request.user)

    def perform_create(self, serializer):
        # Vérifier que l'utilisateur peut donner un feedback sur cette recommandation
        historique_id = self.request.data.get('historique')
        historique = HistoriqueRecommandation.objects.filter(
            id=historique_id, 
            utilisateur=self.request.user
        ).first()
        
        if not historique:
            raise serializers.ValidationError("Recommandation non trouvée")
        
        serializer.save(historique=historique)

class RecommandationViewSet(viewsets.ViewSet):
    """ViewSet pour les opérations de recommandation"""
    permission_classes = [IsAuthenticated]
    gestionnaire = GestionnaireRecommandations()
    
    def get_permissions(self):
        """Gérer les permissions par action"""
        if self.action == 'populaires':
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def pour_moi(self, request):
        """Recommandations personnalisées pour l'utilisateur connecté"""
        start_time = timezone.now()
        user_id = request.user.id
        username = getattr(request.user, 'username', 'unknown')
        
        logger.info(
            f"[RECOMMANDATIONS] Début requête 'pour_moi' - User ID: {user_id}, Username: {username}, "
            f"IP: {request.META.get('REMOTE_ADDR', 'unknown')}, "
            f"Query params: {dict(request.query_params)}"
        )
        
        serializer = RecommandationRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        n_recommandations = serializer.validated_data.get('n_recommandations', 10)
        logger.debug(f"[RECOMMANDATIONS] Nombre de recommandations demandées: {n_recommandations}")
        
        try:
            recommandations = self.gestionnaire.get_recommandations_utilisateur(
                user_id, 
                n_recommandations
            )
            
            nb_reco_retournees = len(recommandations) if isinstance(recommandations, list) else 0
            logger.info(
                f"[RECOMMANDATIONS] Recommandations générées avec succès - User ID: {user_id}, "
                f"Nombre retourné: {nb_reco_retournees}/{n_recommandations}"
            )
            
            # Sauvegarder dans l'historique
            try:
                self._sauvegarder_historique(request.user, recommandations)
                logger.debug(f"[RECOMMANDATIONS] Historique sauvegardé pour User ID: {user_id}")
            except Exception as hist_error:
                logger.warning(
                    f"[RECOMMANDATIONS] Erreur lors de la sauvegarde de l'historique - User ID: {user_id}, "
                    f"Erreur: {str(hist_error)}"
                )
            
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[RECOMMANDATIONS] Requête 'pour_moi' terminée avec succès - User ID: {user_id}, "
                f"Temps d'exécution: {elapsed:.3f}s"
            )
            
            return Response(recommandations)
            
        except Exception as e:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.error(
                f"[RECOMMANDATIONS] Erreur lors de la génération de recommandations 'pour_moi' - "
                f"User ID: {user_id}, Erreur: {str(e)}, Type: {type(e).__name__}, "
                f"Temps écoulé: {elapsed:.3f}s",
                exc_info=True
            )
            return Response(
                {'erreur': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def pour_produit(self, request):
        """Recommandations basées sur un produit spécifique"""
        start_time = timezone.now()
        user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
        
        logger.info(
            f"[RECOMMANDATIONS] Début requête 'pour_produit' - "
            f"User ID: {user_id}, IP: {request.META.get('REMOTE_ADDR', 'unknown')}, "
            f"Query params: {dict(request.query_params)}"
        )
        
        serializer = RecommandationRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        produit_id = serializer.validated_data.get('produit_id')
        n_recommandations = serializer.validated_data.get('n_recommandations', 10)
        
        if not produit_id:
            logger.warning(
                f"[RECOMMANDATIONS] Requête 'pour_produit' rejetée - produit_id manquant, "
                f"User ID: {user_id}, Query params: {dict(request.query_params)}"
            )
            return Response(
                {'erreur': 'produit_id est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logger.debug(
            f"[RECOMMANDATIONS] Paramètres validés - Produit ID: {produit_id}, "
            f"Nombre de recommandations: {n_recommandations}"
        )
        
        try:
            recommandations = self.gestionnaire.get_recommandations_produit(
                produit_id, 
                n_recommandations
            )
            
            nb_reco_retournees = len(recommandations) if isinstance(recommandations, list) else 0
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.info(
                f"[RECOMMANDATIONS] Recommandations 'pour_produit' générées avec succès - "
                f"Produit ID: {produit_id}, Nombre retourné: {nb_reco_retournees}/{n_recommandations}, "
                f"Temps d'exécution: {elapsed:.3f}s"
            )
            
            return Response(recommandations)
            
        except Exception as e:
            elapsed = (timezone.now() - start_time).total_seconds()
            logger.error(
                f"[RECOMMANDATIONS] Erreur lors de la génération de recommandations 'pour_produit' - "
                f"Produit ID: {produit_id}, Erreur: {str(e)}, Type: {type(e).__name__}, "
                f"Temps écoulé: {elapsed:.3f}s",
                exc_info=True
            )
            return Response(
                {'erreur': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    @method_decorator(cache_page(60 * 15))  # Cache 15 minutes
    def populaires(self, request):
        """Produits les plus populaires (accès public)"""
        serializer = RecommandationRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        n_recommandations = serializer.validated_data.get('n_recommandations', 10)
        
        recommandations = self.gestionnaire.get_recommandations_populaires(n_recommandations)
        return Response(recommandations)

    @action(detail=False, methods=['post'])
    def predicire_prix(self, request):
        """Prédit le prix optimal pour un produit"""
        serializer = PredictionPrixRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            prediction = self.gestionnaire.predicire_prix_optimal(serializer.validated_data)
            return Response(prediction)
            
        except Exception as e:
            return Response(
                {'erreur': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _sauvegarder_historique(self, utilisateur, recommandations):
        """Sauvegarde les recommandations dans l'historique"""
        from .models import HistoriqueRecommandation
        from apps.produits.models import Produit
        
        with transaction.atomic():
            for reco in recommandations[:10]:  # Limiter à 10 enregistrements
                produit_id = reco['produit']['id']
                produit = Produit.objects.get(id=produit_id)
                
                HistoriqueRecommandation.objects.create(
                    utilisateur=utilisateur,
                    produit_recommande=produit,
                    score_confiance=reco.get('score_similarite', 0.5),
                    algorithme_utilise=reco.get('algorithme', 'contenu')
                )

class ModeleMLViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour la consultation des modèles ML"""
    queryset = ModeleML.objects.filter(est_actif=True)
    serializer_class = ModeleMLSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'])
    def reentrainer(self, request, pk=None):
        """Relance l'entraînement du modèle"""
        if not request.user.is_staff:
            return Response(
                {'erreur': 'Permission refusée'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Ici, on pourrait lancer une tâche Celery pour le réentraînement
        return Response({'status': 'Réentraînement programmé'})

# Vues fonction pour les endpoints (utilisées dans urls.py)
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Requiert authentification
def recommandations_pour_moi(request):
    """Recommandations personnalisées pour l'utilisateur connecté - Vue fonction pour urls.py"""
    start_time = timezone.now()
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    
    # La permission IsAuthenticated va gérer l'authentification automatiquement
    # On log juste pour déboguer
    auth_header = request.META.get('HTTP_AUTHORIZATION', 'Non fourni')
    logger.debug(
        f"[RECOMMANDATIONS] Requête 'pour_moi' - User: {request.user}, "
        f"Authentifié: {request.user.is_authenticated if hasattr(request.user, 'is_authenticated') else 'N/A'}, "
        f"Auth Header présent: {bool(auth_header and auth_header != 'Non fourni')}, "
        f"IP: {ip_address}"
    )
    
    user_id = request.user.id
    username = getattr(request.user, 'username', 'unknown')
    
    logger.info(
        f"[RECOMMANDATIONS] Début requête 'pour_moi' (fonction) - User ID: {user_id}, Username: {username}, "
        f"IP: {ip_address}, Query params: {dict(request.query_params)}"
    )
    
    try:
        # Récupérer les produits likés par l'utilisateur
        from apps.produits.models import ProduitLike
        from apps.produits.serializers import ProduitListSerializer
        
        produits_likes = ProduitLike.objects.filter(
            utilisateur=request.user
        ).select_related(
            'produit', 'produit__categorie', 'produit__marque', 'produit__unite_mesure'
        ).prefetch_related(
            'produit__caracteristiques', 'produit__avis'
        )
        
        # Annoter avec les prix agrégés
        from django.db.models import Avg, Min, Max, Count
        produits_likes = produits_likes.annotate(
            prix_moyen_agg=Avg('produit__prix__prix_actuel'),
            prix_min_agg=Min('produit__prix__prix_actuel'),
            prix_max_agg=Max('produit__prix__prix_actuel'),
            nombre_magasins_agg=Count('produit__prix', distinct=True)
        ).order_by('-date_creation')
        
        # Extraire les produits
        produits = [like.produit for like in produits_likes]
        
        # Sérialiser les produits
        serializer = ProduitListSerializer(produits, many=True)
        
        nb_produits_likes = len(produits)
        logger.info(
            f"[RECOMMANDATIONS] Produits likés récupérés avec succès - User ID: {user_id}, "
            f"Nombre de produits likés: {nb_produits_likes}"
        )
        
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.info(
            f"[RECOMMANDATIONS] Requête 'pour_moi' (fonction) terminée avec succès - User ID: {user_id}, "
            f"Nombre de produits likés: {nb_produits_likes}, "
            f"Temps d'exécution: {elapsed:.3f}s"
        )
        
        return Response({
            'produits_likes': serializer.data,
            'total': nb_produits_likes,
            'message': 'Produits likés par l\'utilisateur'
        })
        
    except Exception as e:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"[RECOMMANDATIONS] Erreur lors de la génération de recommandations 'pour_moi' (fonction) - "
            f"User ID: {user_id}, Erreur: {str(e)}, Type: {type(e).__name__}, "
            f"Temps écoulé: {elapsed:.3f}s",
            exc_info=True
        )
        return Response(
            {'erreur': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# Vues fonction pour les endpoints publics (utilisées dans urls.py)
@api_view(['GET'])
@permission_classes([AllowAny])
@cache_page(60 * 15)  # Cache 15 minutes (décorateur direct pour fonction)
def recommandations_populaires(request):
    """Produits les plus populaires (accès public) - Vue fonction pour urls.py"""
    start_time = timezone.now()
    user_id = getattr(request.user, 'id', None) if request.user.is_authenticated else None
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    
    logger.info(
        f"[RECOMMANDATIONS] Début requête 'populaires' (public) - "
        f"User ID: {user_id}, IP: {ip_address}, "
        f"Query params: {dict(request.query_params)}, "
        f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')[:100]}"
    )
    
    try:
        serializer = RecommandationRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        n_recommandations = serializer.validated_data.get('n_recommandations', 10)
        logger.debug(f"[RECOMMANDATIONS] Nombre de recommandations populaires demandées: {n_recommandations}")
        
        gestionnaire = GestionnaireRecommandations()
        recommandations = gestionnaire.get_recommandations_populaires(n_recommandations)
        
        nb_reco_retournees = len(recommandations) if isinstance(recommandations, list) else 0
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.info(
            f"[RECOMMANDATIONS] Recommandations 'populaires' générées avec succès - "
            f"Nombre retourné: {nb_reco_retournees}/{n_recommandations}, "
            f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
        )
        
        return Response(recommandations)
    except Exception as e:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"[RECOMMANDATIONS] Erreur lors de la génération de recommandations 'populaires' - "
            f"IP: {ip_address}, Erreur: {str(e)}, Type: {type(e).__name__}, "
            f"Temps écoulé: {elapsed:.3f}s",
            exc_info=True
        )
        return Response(
            {'erreur': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def recommandations_pour_produit(request):
    """Recommandations basées sur un produit spécifique (accès public) - Vue fonction pour urls.py"""
    start_time = timezone.now()
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    produit_id = request.query_params.get('produit_id')
    
    logger.info(
        f"[RECOMMANDATIONS] Début requête 'pour_produit' (query param) - "
        f"Produit ID: {produit_id}, IP: {ip_address}, "
        f"Query params: {dict(request.query_params)}"
    )
    
    if not produit_id:
        logger.warning(
            f"[RECOMMANDATIONS] Requête 'pour_produit' rejetée - produit_id manquant dans query params, "
            f"IP: {ip_address}, Query params: {dict(request.query_params)}"
        )
        return Response(
            {'erreur': 'produit_id est requis'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        n_recommandations = int(request.query_params.get('n_recommandations', 10))
        logger.debug(
            f"[RECOMMANDATIONS] Paramètres validés - Produit ID: {produit_id}, "
            f"Nombre de recommandations: {n_recommandations}"
        )
        
        gestionnaire = GestionnaireRecommandations()
        recommandations = gestionnaire.get_recommandations_produit(
            int(produit_id), 
            n_recommandations
        )
        
        nb_reco_retournees = len(recommandations) if isinstance(recommandations, list) else 0
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.info(
            f"[RECOMMANDATIONS] Recommandations 'pour_produit' (query) générées avec succès - "
            f"Produit ID: {produit_id}, Nombre retourné: {nb_reco_retournees}/{n_recommandations}, "
            f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
        )
        
        return Response(recommandations)
    except ValueError as ve:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.warning(
            f"[RECOMMANDATIONS] Erreur de validation 'pour_produit' - "
            f"Produit ID: {produit_id}, Erreur: {str(ve)}, "
            f"Temps écoulé: {elapsed:.3f}s, IP: {ip_address}"
        )
        return Response(
            {'erreur': f'Paramètre invalide: {str(ve)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"[RECOMMANDATIONS] Erreur lors de la génération de recommandations 'pour_produit' (query) - "
            f"Produit ID: {produit_id}, Erreur: {str(e)}, Type: {type(e).__name__}, "
            f"Temps écoulé: {elapsed:.3f}s, IP: {ip_address}",
            exc_info=True
        )
        return Response(
            {'erreur': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def recommandations_pour_produit_url(request, produit_id):
    """Recommandations basées sur un produit spécifique (accès public) - Version avec produit_id dans l'URL"""
    start_time = timezone.now()
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    
    logger.info(
        f"[RECOMMANDATIONS] Début requête 'pour_produit_url' (URL param) - "
        f"Produit ID: {produit_id}, IP: {ip_address}, "
        f"Query params: {dict(request.query_params)}"
    )
    
    try:
        n_recommandations = int(request.query_params.get('n_recommandations', 10))
        logger.debug(
            f"[RECOMMANDATIONS] Paramètres validés - Produit ID: {produit_id}, "
            f"Nombre de recommandations: {n_recommandations}"
        )
        
        gestionnaire = GestionnaireRecommandations()
        recommandations = gestionnaire.get_recommandations_produit(
            produit_id, 
            n_recommandations
        )
        
        nb_reco_retournees = len(recommandations) if isinstance(recommandations, list) else 0
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.info(
            f"[RECOMMANDATIONS] Recommandations 'pour_produit_url' générées avec succès - "
            f"Produit ID: {produit_id}, Nombre retourné: {nb_reco_retournees}/{n_recommandations}, "
            f"Temps d'exécution: {elapsed:.3f}s, IP: {ip_address}"
        )
        
        return Response(recommandations)
    except ValueError as ve:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.warning(
            f"[RECOMMANDATIONS] Erreur de validation 'pour_produit_url' - "
            f"Produit ID: {produit_id}, Erreur: {str(ve)}, "
            f"Temps écoulé: {elapsed:.3f}s, IP: {ip_address}"
        )
        return Response(
            {'erreur': f'Paramètre invalide: {str(ve)}'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        elapsed = (timezone.now() - start_time).total_seconds()
        logger.error(
            f"[RECOMMANDATIONS] Erreur lors de la génération de recommandations 'pour_produit_url' - "
            f"Produit ID: {produit_id}, Erreur: {str(e)}, Type: {type(e).__name__}, "
            f"Temps écoulé: {elapsed:.3f}s, IP: {ip_address}",
            exc_info=True
        )
        return Response(
            {'erreur': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def statut_modeles(request):
    """Endpoint public pour vérifier le statut des modèles"""
    ip_address = request.META.get('REMOTE_ADDR', 'unknown')
    logger.info(
        f"[RECOMMANDATIONS] Requête 'statut_modeles' - IP: {ip_address}, "
        f"User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')[:100]}"
    )
    
    try:
        gestionnaire = GestionnaireRecommandations()
        statut = {
            'modele_contenu_entraine': gestionnaire.modele_contenu.est_entraine,
            'modele_prix_entraine': gestionnaire.modele_prix.est_entraine,
            'gestionnaire_initialise': gestionnaire.est_initialise,
            'nombre_modeles_actifs': ModeleML.objects.filter(est_actif=True).count()
        }
        
        logger.debug(
            f"[RECOMMANDATIONS] Statut des modèles récupéré - "
            f"Contenu entraîné: {statut['modele_contenu_entraine']}, "
            f"Prix entraîné: {statut['modele_prix_entraine']}, "
            f"Initialisé: {statut['gestionnaire_initialise']}, "
            f"Modèles actifs: {statut['nombre_modeles_actifs']}"
        )
        
        return Response(statut)
    except Exception as e:
        logger.error(
            f"[RECOMMANDATIONS] Erreur lors de la récupération du statut des modèles - "
            f"IP: {ip_address}, Erreur: {str(e)}, Type: {type(e).__name__}",
            exc_info=True
        )
        return Response({'erreur': str(e)}, status=500)