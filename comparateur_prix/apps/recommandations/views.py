from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from django.apps import apps

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

    @action(detail=False, methods=['get'])
    def pour_moi(self, request):
        """Recommandations personnalisées pour l'utilisateur connecté"""
        serializer = RecommandationRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        n_recommandations = serializer.validated_data.get('n_recommandations', 10)
        
        try:
            recommandations = self.gestionnaire.get_recommandations_utilisateur(
                request.user.id, 
                n_recommandations
            )
            
            # Sauvegarder dans l'historique
            self._sauvegarder_historique(request.user, recommandations)
            
            return Response(recommandations)
            
        except Exception as e:
            return Response(
                {'erreur': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def pour_produit(self, request):
        """Recommandations basées sur un produit spécifique"""
        serializer = RecommandationRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        
        produit_id = serializer.validated_data.get('produit_id')
        n_recommandations = serializer.validated_data.get('n_recommandations', 10)
        
        if not produit_id:
            return Response(
                {'erreur': 'produit_id est requis'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            recommandations = self.gestionnaire.get_recommandations_produit(
                produit_id, 
                n_recommandations
            )
            return Response(recommandations)
            
        except Exception as e:
            return Response(
                {'erreur': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 15))  # Cache 15 minutes
    def populaires(self, request):
        """Produits les plus populaires"""
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

@api_view(['GET'])
@permission_classes([AllowAny])
def statut_modeles(request):
    """Endpoint public pour vérifier le statut des modèles"""
    try:
        gestionnaire = GestionnaireRecommandations()
        statut = {
            'modele_contenu_entraine': gestionnaire.modele_contenu.est_entraine,
            'modele_prix_entraine': gestionnaire.modele_prix.est_entraine,
            'gestionnaire_initialise': gestionnaire.est_initialise,
            'nombre_modeles_actifs': ModeleML.objects.filter(est_actif=True).count()
        }
        return Response(statut)
    except Exception as e:
        return Response({'erreur': str(e)}, status=500)