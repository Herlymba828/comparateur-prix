from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import (
    Categorie, Marque, UniteMesure, Produit, 
    AvisProduit, CaracteristiqueProduit, HistoriquePrixProduit,
    Prix, HistoriquePrix, AlertePrix, SuggestionPrix, ComparaisonPrix, Offre,
)
# Nettoyage: pas d'import de modèles inexistants


# (définitions de serializers pour Prix sont plus bas dans ce fichier)


class HistoriquePrixSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des prix"""
    magasin_nom = serializers.CharField(source='prix.magasin.nom', read_only=True)
    produit_nom = serializers.CharField(source='prix.produit.nom', read_only=True)
    
    class Meta:
        model = HistoriquePrix
        fields = [
            'id', 'prix', 'magasin_nom', 'produit_nom', 'ancien_prix',
            'nouveau_prix', 'variation', 'pourcentage_variation', 'raison',
            'date_changement', 'modifie_par'
        ]
        read_only_fields = ['date_changement']


class AlertePrixSerializer(serializers.ModelSerializer):
    """Serializer pour les alertes de prix"""
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_image = serializers.ImageField(source='produit.image_principale', read_only=True)
    prix_actuel_minimum = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True
    )
    est_seuil_atteint = serializers.BooleanField(read_only=True)
    magasins_noms = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertePrix
        fields = [
            'id', 'utilisateur', 'produit', 'produit_nom', 'produit_image',
            'prix_souhaite', 'pourcentage_reduction', 'magasins', 'magasins_noms',
            'est_active', 'frequence_verification', 'prix_actuel_minimum',
            'est_seuil_atteint', 'date_creation', 'date_derniere_alerte',
            'nombre_alertes_envoyees'
        ]
        read_only_fields = [
            'utilisateur', 'date_creation', 'date_derniere_alerte',
            'nombre_alertes_envoyees'
        ]
    
    def get_magasins_noms(self, obj):
        return [magasin.nom for magasin in obj.magasins.all()]
    
    def validate(self, data):
        """Validation des données de l'alerte"""
        if 'prix_souhaite' not in data and 'pourcentage_reduction' not in data:
            raise serializers.ValidationError(
                _("Vous devez spécifier soit un prix souhaité, soit un pourcentage de réduction")
            )
        return data
    
    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)


class ComparaisonPrixSerializer(serializers.ModelSerializer):
    """Serializer pour les comparaisons de prix"""
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_categorie = serializers.CharField(source='produit.categorie.nom', read_only=True)
    magasin_prix_min_nom = serializers.CharField(source='magasin_prix_min.nom', read_only=True)
    magasin_prix_max_nom = serializers.CharField(source='magasin_prix_max.nom', read_only=True)
    ecart_prix = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True,
        source='prix_maximum - prix_minimum'
    )
    
    class Meta:
        model = ComparaisonPrix
        fields = [
            'id', 'produit', 'produit_nom', 'produit_categorie', 'date_comparaison',
            'prix_minimum', 'prix_maximum', 'prix_moyen', 'ecart_prix',
            'nombre_magasins', 'ecart_type', 'coefficient_variation',
            'magasin_prix_min', 'magasin_prix_min_nom', 'magasin_prix_max',
            'magasin_prix_max_nom'
        ]
        read_only_fields = ['date_comparaison']


class SuggestionPrixSerializer(serializers.ModelSerializer):
    """Serializer pour les suggestions de prix"""
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    magasin_nom = serializers.CharField(source='magasin.nom', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    prix_actuel_magasin = serializers.SerializerMethodField()
    
    class Meta:
        model = SuggestionPrix
        fields = [
            'id', 'utilisateur', 'utilisateur_nom', 'produit', 'produit_nom',
            'magasin', 'magasin_nom', 'prix_suggere', 'prix_actuel_magasin',
            'date_observation', 'photo_preuve', 'commentaire', 'statut',
            'verifie_par', 'date_verification', 'raison_rejet', 'date_creation'
        ]
        read_only_fields = [
            'utilisateur', 'statut', 'verifie_par', 'date_verification',
            'raison_rejet', 'date_creation'
        ]
    
    def get_prix_actuel_magasin(self, obj):
        """Retourne le prix actuel enregistré pour ce produit dans ce magasin"""
        try:
            prix_actuel_obj = Prix.objects.get(
                produit=obj.produit,
                magasin=obj.magasin
            )
            return prix_actuel_obj.prix_actuel
        except Prix.DoesNotExist:
            return None
    
    def validate(self, data):
        """Validation de la suggestion"""
        # Vérifier que la date d'observation n'est pas dans le futur
        if data.get('date_observation'):
            from django.utils import timezone
            if data['date_observation'] > timezone.now():
                raise serializers.ValidationError(
                    _("La date d'observation ne peut pas être dans le futur")
                )
        
        return data
    
    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)


class PrixParMagasinSerializer(serializers.Serializer):
    """Serializer pour l'agrégation des prix par magasin"""
    magasin_id = serializers.IntegerField()
    magasin_nom = serializers.CharField()
    prix_min = serializers.DecimalField(max_digits=8, decimal_places=2)
    prix_max = serializers.DecimalField(max_digits=8, decimal_places=2)
    prix_moyen = serializers.DecimalField(max_digits=8, decimal_places=2)
    nombre_produits = serializers.IntegerField()
    pourcentage_promotions = serializers.DecimalField(max_digits=5, decimal_places=2)


class EvolutionPrixSerializer(serializers.Serializer):
    """Serializer pour l'évolution des prix dans le temps"""
    date = serializers.DateField()
    prix_moyen = serializers.DecimalField(max_digits=8, decimal_places=2)
    prix_min = serializers.DecimalField(max_digits=8, decimal_places=2)
    prix_max = serializers.DecimalField(max_digits=8, decimal_places=2)
    nombre_magasins = serializers.IntegerField()


class OffreSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle unifié Offre"""
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    magasin_nom = serializers.CharField(source='magasin.nom', read_only=True)

    class Meta:
        model = Offre
        fields = [
            'id', 'produit', 'produit_nom', 'magasin', 'magasin_nom',
            'prix_actuel', 'prix_origine', 'est_promotion',
            'cheapness_score', 'popularity_count', 'recommendation_score',
            'source', 'date_observation'
        ]
        read_only_fields = ['date_observation']

class UniteMesureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UniteMesure
        fields = ['id', 'nom', 'symbole', 'description']


class CategorieSerializer(serializers.ModelSerializer):
    niveau = serializers.SerializerMethodField()
    est_racine = serializers.SerializerMethodField()
    chemin = serializers.SerializerMethodField()
    nombre_produits = serializers.SerializerMethodField()
    sous_categories = serializers.SerializerMethodField()
    
    class Meta:
        model = Categorie
        fields = [
            'id', 'nom', 'slug', 'description', 'parent', 'image', 
            'ordre', 'niveau', 'est_racine', 'chemin', 'nombre_produits',
            'sous_categories', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification']
    
    def get_niveau(self, obj):
        """Retourne le niveau de la catégorie dans la hiérarchie"""
        return obj.get_niveau()
    
    def get_est_racine(self, obj):
        """Indique si la catégorie est une catégorie racine"""
        return obj.est_racine
    
    def get_chemin(self, obj):
        """Retourne le chemin complet de la catégorie"""
        return obj.get_chemin()
    
    def get_nombre_produits(self, obj):
        """Retourne le nombre de produits actifs dans cette catégorie"""
        return obj.produits.filter(est_actif=True).count()
    
    def get_sous_categories(self, obj):
        """Retourne les sous-catégories de manière récursive"""
        sous_cats = obj.sous_categories.all()
        if sous_cats.exists():
            # Limiter la profondeur de récursion pour éviter les problèmes de performance
            # et les récursions infinies en cas de relations circulaires
            return CategorieSerializer(sous_cats, many=True).data
        return []


class MarqueSerializer(serializers.ModelSerializer):
    nombre_produits = serializers.SerializerMethodField()
    
    class Meta:
        model = Marque
        fields = [
            'id', 'nom', 'slug', 'description', 'logo', 'site_web',
            'pays_origine', 'nombre_produits', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification']
    
    def get_nombre_produits(self, obj):
        return obj.produits.filter(est_actif=True).count()


class ProduitListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des produits (optimisé)"""
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    marque_nom = serializers.CharField(source='marque.nom', read_only=True, allow_null=True)
    # Utiliser les annotations du queryset (prix_moyen_agg, prix_min_agg, etc.)
    prix_moyen = serializers.DecimalField(
        source='prix_moyen_agg',
        max_digits=8, decimal_places=2, read_only=True, allow_null=True
    )
    prix_min = serializers.DecimalField(
        source='prix_min_agg',
        max_digits=8, decimal_places=2, read_only=True, allow_null=True
    )
    prix_max = serializers.DecimalField(
        source='prix_max_agg',
        max_digits=8, decimal_places=2, read_only=True, allow_null=True
    )
    nombre_magasins = serializers.IntegerField(source='nombre_magasins_agg', read_only=True)
    
    class Meta:
        model = Produit
        fields = [
            'id', 'code_barre', 'nom', 'slug', 'categorie', 'categorie_nom',
            'marque', 'marque_nom', 'image_principale', 'prix_moyen',
            'prix_min', 'prix_max', 'nombre_magasins', 'est_actif'
        ]


class ProduitDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un produit"""
    categorie = CategorieSerializer(read_only=True)
    marque = MarqueSerializer(read_only=True)
    unite_mesure = UniteMesureSerializer(read_only=True)
    # Utiliser les propriétés du modèle ou les annotations si disponibles
    prix_moyen = serializers.SerializerMethodField()
    prix_min = serializers.SerializerMethodField()
    prix_max = serializers.SerializerMethodField()
    nombre_magasins = serializers.SerializerMethodField()
    note_moyenne = serializers.SerializerMethodField()
    nombre_avis = serializers.SerializerMethodField()
    caracteristiques = serializers.SerializerMethodField()
    
    class Meta:
        model = Produit
        fields = [
            'id', 'code_barre', 'nom', 'slug', 'categorie', 'marque',
            'poids', 'volume', 'unite_mesure', 'quantite_unite',
            'energie_kcal', 'proteines_g', 'glucides_g', 'lipides_g',
            'image_principale', 'images_secondaires', 'est_actif',
            'prix_moyen', 'prix_min', 'prix_max', 'nombre_magasins',
            'note_moyenne', 'nombre_avis', 'caracteristiques',
            'date_creation', 'date_modification'
        ]
        read_only_fields = ['date_creation', 'date_modification']
    
    def get_prix_moyen(self, obj):
        """Récupère le prix moyen depuis l'annotation ou la propriété"""
        if hasattr(obj, 'prix_moyen_agg'):
            return float(obj.prix_moyen_agg) if obj.prix_moyen_agg else None
        return float(obj.prix_moyen) if obj.prix_moyen else None
    
    def get_prix_min(self, obj):
        """Récupère le prix minimum depuis l'annotation ou la propriété"""
        if hasattr(obj, 'prix_min_agg'):
            return float(obj.prix_min_agg) if obj.prix_min_agg else None
        return float(obj.prix_min) if obj.prix_min else None
    
    def get_prix_max(self, obj):
        """Récupère le prix maximum depuis l'annotation ou la propriété"""
        if hasattr(obj, 'prix_max_agg'):
            return float(obj.prix_max_agg) if obj.prix_max_agg else None
        return float(obj.prix_max) if obj.prix_max else None
    
    def get_nombre_magasins(self, obj):
        """Récupère le nombre de magasins depuis l'annotation ou la propriété"""
        if hasattr(obj, 'nombre_magasins_agg'):
            return obj.nombre_magasins_agg or 0
        return obj.nombre_magasins or 0
    
    def get_note_moyenne(self, obj):
        from django.db.models import Avg
        result = obj.avis.aggregate(moyenne=Avg('note'))
        return round(result['moyenne'], 2) if result['moyenne'] else None
    
    def get_nombre_avis(self, obj):
        return obj.avis.count()
    
    def get_caracteristiques(self, obj):
        caracteristiques = obj.caracteristiques.all().order_by('ordre')
        return CaracteristiqueProduitSerializer(caracteristiques, many=True).data


class ProduitCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la création et modification de produits"""
    
    class Meta:
        model = Produit
        fields = [
            'code_barre', 'nom', 'categorie', 'marque', 'poids', 'volume',
            'unite_mesure', 'quantite_unite', 'energie_kcal', 'proteines_g',
            'glucides_g', 'lipides_g', 'image_principale', 'est_actif'
        ]
    
    def validate_code_barre(self, value):
        """Valide le format du code-barres"""
        if not value.isdigit():
            raise serializers.ValidationError(_("Le code-barres doit contenir uniquement des chiffres"))
        if len(value) not in [8, 12, 13, 14]:
            raise serializers.ValidationError(_("Le code-barres doit avoir 8, 12, 13 ou 14 chiffres"))
        return value
    
    def create(self, validated_data):
        validated_data['cree_par'] = self.context['request'].user
        return super().create(validated_data)


class AvisProduitSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    utilisateur_username = serializers.CharField(source='utilisateur.username', read_only=True)
    
    class Meta:
        model = AvisProduit
        fields = [
            'id', 'produit', 'utilisateur', 'utilisateur_nom', 'utilisateur_username',
            'note', 'titre', 'commentaire', 'est_verifie', 'date_creation', 'date_modification'
        ]
        read_only_fields = ['utilisateur', 'date_creation', 'date_modification']
    
    def create(self, validated_data):
        validated_data['utilisateur'] = self.context['request'].user
        return super().create(validated_data)
    
    def validate(self, data):
        """Valide qu'un utilisateur ne peut pas poster deux avis sur le même produit"""
        if self.instance is None:  # Création uniquement
            utilisateur = self.context['request'].user
            produit = data['produit']
            if AvisProduit.objects.filter(produit=produit, utilisateur=utilisateur).exists():
                raise serializers.ValidationError(
                    _("Vous avez déjà posté un avis sur ce produit")
                )
        return data


class CaracteristiqueProduitSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CaracteristiqueProduit
        fields = ['id', 'produit', 'nom', 'valeur', 'ordre']
        read_only_fields = ['produit']


class HistoriquePrixProduitSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = HistoriquePrixProduit
        fields = ['id', 'produit', 'date', 'prix_moyen', 'prix_min', 'prix_max', 'nombre_magasins']


class BatchPrixRequestSerializer(serializers.Serializer):
    """Serializer pour les requêtes batch de prix"""
    produit_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100,
        help_text="Liste des IDs de produits (max 100)"
    )
    magasin_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Liste des IDs de magasins (optionnel)"
    )
    include_stats = serializers.BooleanField(
        default=True,
        help_text="Inclure les statistiques de prix pour chaque produit"
    )
    filters = serializers.DictField(
        required=False,
        allow_empty=True,
        help_text="Filtres additionnels (est_promotion, rayon_km, etc.)"
    )


class BatchPrixResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses batch de prix"""
    produit_id = serializers.IntegerField()
    magasin_id = serializers.IntegerField(allow_null=True)
    prix_id = serializers.IntegerField(allow_null=True)
    prix_actuel = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)
    prix_origine = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)
    est_promotion = serializers.BooleanField()
    pourcentage_promotion = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    devise = serializers.CharField()
    disponible = serializers.BooleanField()
    stats = serializers.DictField(required=False, allow_null=True)
    produit_nom = serializers.CharField(allow_null=True)
    magasin_nom = serializers.CharField(allow_null=True)


class PrixSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    magasin_id = serializers.IntegerField(source='magasin.id', read_only=True)
    prix_par_unite = serializers.SerializerMethodField()
    
    class Meta:
        model = Prix
        fields = [
            'id', 'produit', 'produit_nom', 'magasin', 'magasin_id',
            'prix_actuel', 'prix_origine', 'est_promotion', 'est_disponible',
            'quantite_stock', 'niveau_stock', 'source_prix', 'confiance_prix',
            'cheapness_score', 'popularity_count', 'recommendation_score',
            'date_creation', 'date_modification', 'prix_par_unite',
        ]
        read_only_fields = ['date_creation', 'date_modification', 'est_promotion']
    
    def get_prix_par_unite(self, obj):
        return obj.prix_par_unite


class HistoriquePrixSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoriquePrix
        fields = [
            'id', 'prix', 'ancien_prix', 'nouveau_prix', 'variation',
            'pourcentage_variation', 'raison', 'date_changement',
        ]


class ProduitRechercheSerializer(serializers.Serializer):
    """Serializer pour les résultats de recherche"""
    id = serializers.IntegerField()
    nom = serializers.CharField()
    code_barre = serializers.CharField()
    categorie_nom = serializers.CharField()
    marque_nom = serializers.CharField(allow_null=True)
    image_principale = serializers.ImageField(allow_null=True)
    prix_min = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)
    prix_max = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)
    nombre_magasins = serializers.IntegerField()
    score = serializers.FloatField(help_text="Score de pertinence dans la recherche")