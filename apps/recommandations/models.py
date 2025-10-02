from django.db import models
from django.contrib.auth import get_user_model
from apps.produits.models import Produit
from apps.utilisateurs.models import Utilisateur

User = get_user_model()

class HistoriqueRecommandation(models.Model):
    """Historique des recommandations générées pour les utilisateurs"""
    
    utilisateur = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='recommandations'
    )
    produit_recommande = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name='recommandations'
    )
    score_confiance = models.FloatField(
        default=0.0,
        help_text="Score de confiance de la recommandation (0-1)"
    )
    algorithme_utilise = models.CharField(
        max_length=50,
        choices=[
            ('contenu', 'Recommandation par Contenu'),
            ('collaboratif', 'Filtrage Collaboratif'),
            ('hybride', 'Modèle Hybride'),
            ('populaire', 'Produits Populaires')
        ]
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_visualisation = models.DateTimeField(null=True, blank=True)
    a_ete_clique = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'recommandations_historique'
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['utilisateur', 'date_creation']),
            models.Index(fields=['produit_recommande', 'score_confiance']),
        ]
    
    def __str__(self):
        return f"Recommandation {self.id} pour {self.utilisateur}"

class ModeleML(models.Model):
    """Stockage des métadonnées des modèles de machine learning"""
    
    nom = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20, default='1.0.0')
    type_modele = models.CharField(
        max_length=50,
        choices=[
            ('recommandation', 'Système de Recommandation'),
            ('prediction_prix', 'Prédiction de Prix'),
            ('classification', 'Classification')
        ]
    )
    chemin_fichier = models.CharField(max_length=255)
    precision = models.FloatField(null=True, blank=True)
    date_entrainement = models.DateTimeField(auto_now_add=True)
    est_actif = models.BooleanField(default=True)
    parametres = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'recommandations_modeles_ml'
        ordering = ['-date_entrainement']
    
    def __str__(self):
        return f"{self.nom} v{self.version}"

class FeedbackRecommandation(models.Model):
    """Feedback des utilisateurs sur les recommandations"""
    
    historique = models.OneToOneField(
        HistoriqueRecommandation,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    note_utilisateur = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],  # 1-5 étoiles
        null=True,
        blank=True
    )
    aime = models.BooleanField(null=True, blank=True)
    commentaire = models.TextField(blank=True)
    date_feedback = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommandations_feedback'
    
    def __str__(self):
        return f"Feedback {self.id} - Note: {self.note_utilisateur}"