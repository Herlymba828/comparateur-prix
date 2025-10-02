from django.db import models, connection
from django.db.models import Avg, Min, Max, StdDev, Count
from django.utils import timezone
from django.core.cache import cache
import datetime
import statistics
import logging
import time

logger = logging.getLogger(__name__)

class OptimiseurRequetes:
    """Classe pour optimiser les requêtes d'analyse"""
    
    def __init__(self):
        self.connection = connection
    
    def executer_comparaison_enseignes(self, categorie_id, date_debut, date_fin):
        """Comparaison optimisée entre enseignes"""
        start_time = time.time()
        
        if not date_debut or not date_fin:
            date_fin = timezone.now().date()
            date_debut = date_fin - datetime.timedelta(days=30)
        
        # Implémentation ORM basée sur le modèle Prix
        # Hypothèses: utiliser Prix.prix_actuel et Prix.date_modification comme fenêtre temporelle
        from apps.produits.models import Prix
        from django.db.models import Avg, Min, Max, Count, F

        qs = (
            Prix.objects
            .filter(
                produit__categorie_id=categorie_id,
                est_disponible=True,
                date_modification__date__gte=date_debut,
                date_modification__date__lte=date_fin,
            )
            .select_related('magasin__ville__region', 'produit__categorie')
            .values(
                enseigne=F('magasin__nom'),
                ville=F('magasin__ville__nom'),
                region=F('magasin__ville__region__nom'),
            )
            .annotate(
                nombre_produits=Count('produit', distinct=True),
                prix_moyen=Avg('prix_actuel'),
                prix_minimum=Min('prix_actuel'),
                prix_maximum=Max('prix_actuel'),
                nombre_prix_analyses=Count('id'),
            )
            .order_by('prix_moyen')
        )

        resultats = list(qs)
        for r in resultats:
            r['ecart_type'] = 0.0  # TODO: ajouter calcul si nécessaire

        return {
            'date_analyse': timezone.now().isoformat(),
            'parametres': {'categorie_id': categorie_id, 'date_debut': date_debut, 'date_fin': date_fin},
            'resultats': resultats,
            'metriques': {
                'nombre_enseignes': len(resultats),
                'duree_calcul': round(time.time() - start_time, 3)
            }
        }
    
    def executer_analyse_evolution(self, produit_id, magasin_id, periode):
        """Analyse de l'évolution des prix dans le temps"""
        start_time = time.time()
        
        # Calcul des dates basé sur la période
        date_fin = timezone.now().date()
        if periode == '7j':
            date_debut = date_fin - datetime.timedelta(days=7)
        elif periode == '30j':
            date_debut = date_fin - datetime.timedelta(days=30)
        elif periode == '90j':
            date_debut = date_fin - datetime.timedelta(days=90)
        else:  # 1an
            date_debut = date_fin - datetime.timedelta(days=365)
        
        from apps.produits.models import Prix
        
        queryset = Prix.objects.filter(
            produit_id=produit_id,
            date_releve__gte=date_debut,
            date_releve__lte=date_fin
        )
        
        if magasin_id:
            queryset = queryset.filter(magasin_id=magasin_id)
        
        # Agrégation par jour
        prix_par_jour = queryset.extra(
            {'date': "DATE(date_releve)"}
        ).values('date').annotate(
            prix_moyen=Avg('prix'),
            prix_min=Min('prix'),
            prix_max=Max('prix'),
            nombre_releves=Count('id')
        ).order_by('date')
        
        # Calcul des tendances
        donnees_evolution = list(prix_par_jour)
        variation = 0
        if len(donnees_evolution) >= 2:
            premier_prix = donnees_evolution[0]['prix_moyen']
            dernier_prix = donnees_evolution[-1]['prix_moyen']
            if premier_prix > 0:
                variation = ((dernier_prix - premier_prix) / premier_prix) * 100
        
        return {
            'produit_id': produit_id,
            'magasin_id': magasin_id,
            'periode': periode,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'evolution_prix': donnees_evolution,
            'variation_totale': round(variation, 2),
            'tendance': 'hausse' if variation > 0 else 'baisse' if variation < 0 else 'stable',
            'duree_calcul': round(time.time() - start_time, 3)
        }

class CalculateurMetriques:
    """Classe pour calculer les métriques d'analyse"""
    
    @staticmethod
    def calculer_statistiques_prix(queryset_prix):
        """Calculer les statistiques de base sur un queryset de prix"""
        if not queryset_prix.exists():
            return {}
        
        valeurs_prix = list(queryset_prix.values_list('prix', flat=True))
        
        return {
            'moyenne': statistics.mean(valeurs_prix) if valeurs_prix else 0,
            'mediane': statistics.median(valeurs_prix) if valeurs_prix else 0,
            'ecart_type': statistics.stdev(valeurs_prix) if len(valeurs_prix) > 1 else 0,
            'minimum': min(valeurs_prix) if valeurs_prix else 0,
            'maximum': max(valeurs_prix) if valeurs_prix else 0,
            'nombre_echantillons': len(valeurs_prix)
        }
    
    @staticmethod
    def detecter_anomalies_prix(prix, moyenne, ecart_type, seuil=3):
        """Détecter les anomalies de prix basées sur l'écart-type"""
        if ecart_type == 0:
            return False
        return abs(prix - moyenne) > seuil * ecart_type