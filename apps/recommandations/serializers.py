from rest_framework import serializers
from .models import HistoriqueRecommandation, FeedbackRecommandation, ModeleML
from apps.produits.serializers import ProduitListSerializer

class FeedbackRecommandationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackRecommandation
        fields = ['id', 'note_utilisateur', 'aime', 'commentaire', 'date_feedback']
        read_only_fields = ['date_feedback']

class HistoriqueRecommandationSerializer(serializers.ModelSerializer):
    produit_details = ProduitListSerializer(source='produit_recommande', read_only=True)
    feedback = FeedbackRecommandationSerializer(read_only=True)
    
    class Meta:
        model = HistoriqueRecommandation
        fields = [
            'id', 'utilisateur', 'produit_recommande', 'produit_details',
            'score_confiance', 'algorithme_utilise', 'date_creation',
            'date_visualisation', 'a_ete_clique', 'feedback'
        ]
        read_only_fields = ['date_creation']

class ModeleMLSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeleML
        fields = [
            'id', 'nom', 'version', 'type_modele', 'chemin_fichier',
            'precision', 'date_entrainement', 'est_actif', 'parametres'
        ]
        read_only_fields = ['date_entrainement']

class RecommandationRequestSerializer(serializers.Serializer):
    produit_id = serializers.IntegerField(required=False)
    n_recommandations = serializers.IntegerField(default=10, min_value=1, max_value=50)
    algorithme = serializers.ChoiceField(
        choices=['contenu', 'collaboratif', 'hybride', 'populaire'],
        default='contenu'
    )

class PredictionPrixRequestSerializer(serializers.Serializer):
    categorie = serializers.CharField(required=True)
    marque = serializers.CharField(required=True)
    magasin = serializers.CharField(required=True)
    ville = serializers.CharField(required=True)

class ProduitRecommandationSerializer(serializers.Serializer):
    produit = ProduitListSerializer()
    score_similarite = serializers.FloatField()
    algorithme = serializers.CharField()
    prix_prediction = serializers.FloatField(required=False)