"""
Service d'enrichissement des prix avec cache Redis.

Ce service permet de récupérer et mettre en cache les prix enrichis
avec leurs statistiques pour améliorer les performances.
"""
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
from django.core.cache import cache
from django.db.models import Min, Max, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from apps.produits.models import Prix, Produit

logger = logging.getLogger(__name__)

# Configuration du cache
CACHE_TIMEOUT_STATS = 3600  # 1 heure
CACHE_TIMEOUT_PRICE = 1800  # 30 minutes
CACHE_PREFIX_STATS = 'prix_stats'
CACHE_PREFIX_PRICE = 'prix_enriched'
CACHE_PREFIX_PRODUIT = 'produit_prix'


class PriceEnrichmentService:
    """Service pour l'enrichissement et la mise en cache des prix."""
    
    @staticmethod
    def get_cache_key_stats(produit_id: int) -> str:
        """Génère une clé de cache pour les statistiques d'un produit."""
        return f"{CACHE_PREFIX_STATS}:{produit_id}"
    
    @staticmethod
    def get_cache_key_price(produit_id: int, magasin_id: Optional[int] = None) -> str:
        """Génère une clé de cache pour un prix enrichi."""
        if magasin_id:
            return f"{CACHE_PREFIX_PRICE}:{produit_id}:{magasin_id}"
        return f"{CACHE_PREFIX_PRICE}:{produit_id}"
    
    @staticmethod
    def get_cache_key_produit(produit_id: int) -> str:
        """Génère une clé de cache pour tous les prix d'un produit."""
        return f"{CACHE_PREFIX_PRODUIT}:{produit_id}"
    
    @classmethod
    def get_price_stats(cls, produit_id: int, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Récupère les statistiques de prix pour un produit (min, max, moyenne, nombre).
        
        Args:
            produit_id: ID du produit
            force_refresh: Si True, ignore le cache et recalcule
            
        Returns:
            Dictionnaire avec min, max, avg, count, last_update
        """
        cache_key = cls.get_cache_key_stats(produit_id)
        
        # Vérifier le cache
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit pour stats produit {produit_id}")
                return cached
        
        # Calculer les statistiques
        try:
            stats = Prix.objects.filter(
                produit_id=produit_id,
                est_disponible=True
            ).aggregate(
                prix_min=Min('prix_actuel'),
                prix_max=Max('prix_actuel'),
                prix_moyen=Avg('prix_actuel'),
                nombre_magasins=Count('id', distinct=True),
                promotions=Count('id', filter=Q(est_promotion=True))
            )
            
            result = {
                'produit_id': produit_id,
                'prix_min': float(stats['prix_min']) if stats['prix_min'] else None,
                'prix_max': float(stats['prix_max']) if stats['prix_max'] else None,
                'prix_moyen': float(stats['prix_moyen']) if stats['prix_moyen'] else None,
                'nombre_magasins': stats['nombre_magasins'] or 0,
                'nombre_promotions': stats['promotions'] or 0,
                'last_update': timezone.now().isoformat(),
            }
            
            # Mettre en cache
            cache.set(cache_key, result, CACHE_TIMEOUT_STATS)
            logger.debug(f"Stats calculées et mises en cache pour produit {produit_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des stats pour produit {produit_id}: {e}")
            return {
                'produit_id': produit_id,
                'prix_min': None,
                'prix_max': None,
                'prix_moyen': None,
                'nombre_magasins': 0,
                'nombre_promotions': 0,
                'last_update': None,
                'error': str(e)
            }
    
    @classmethod
    def get_enriched_price(
        cls,
        produit_id: int,
        magasin_id: Optional[int] = None,
        include_stats: bool = True,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Récupère un prix enrichi avec ses métadonnées.
        
        Args:
            produit_id: ID du produit
            magasin_id: ID du magasin (optionnel)
            include_stats: Inclure les statistiques du produit
            force_refresh: Si True, ignore le cache
            
        Returns:
            Dictionnaire avec les données du prix enrichi
        """
        cache_key = cls.get_cache_key_price(produit_id, magasin_id)
        
        # Vérifier le cache
        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit pour prix {produit_id}:{magasin_id}")
                return cached
        
        try:
            # Récupérer le prix
            query = Prix.objects.select_related(
                'produit', 'produit__categorie', 'produit__marque', 'magasin'
            ).filter(
                produit_id=produit_id,
                est_disponible=True
            )
            
            if magasin_id:
                query = query.filter(magasin_id=magasin_id)
            
            prix_obj = query.first()
            
            if not prix_obj:
                return {
                    'produit_id': produit_id,
                    'magasin_id': magasin_id,
                    'prix': None,
                    'disponible': False,
                }
            
            # Construire la réponse enrichie
            result = {
                'prix_id': prix_obj.id,
                'produit_id': produit_id,
                'produit_nom': prix_obj.produit.nom,
                'magasin_id': prix_obj.magasin_id,
                'magasin_nom': prix_obj.magasin.nom,
                'prix_actuel': float(prix_obj.prix_actuel),
                'prix_origine': float(prix_obj.prix_origine) if prix_obj.prix_origine else None,
                'est_promotion': prix_obj.est_promotion,
                'pourcentage_promotion': float(prix_obj.pourcentage_promotion) if prix_obj.est_promotion else 0,
                'devise': prix_obj.devise,
                'date_modification': prix_obj.date_modification.isoformat() if prix_obj.date_modification else None,
                'disponible': True,
            }
            
            # Ajouter les statistiques si demandé
            if include_stats:
                stats = cls.get_price_stats(produit_id, force_refresh=False)
                result['stats'] = stats
                # Calculer la position relative du prix
                if stats['prix_min'] and stats['prix_max']:
                    prix_val = result['prix_actuel']
                    if stats['prix_min'] < stats['prix_max']:
                        result['position_relative'] = (prix_val - stats['prix_min']) / (stats['prix_max'] - stats['prix_min'])
                    else:
                        result['position_relative'] = 0.5
                else:
                    result['position_relative'] = None
            
            # Mettre en cache
            cache.set(cache_key, result, CACHE_TIMEOUT_PRICE)
            logger.debug(f"Prix enrichi calculé et mis en cache: {produit_id}:{magasin_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement du prix {produit_id}:{magasin_id}: {e}")
            return {
                'produit_id': produit_id,
                'magasin_id': magasin_id,
                'prix': None,
                'disponible': False,
                'error': str(e)
            }
    
    @classmethod
    def get_batch_prices(
        cls,
        produit_ids: List[int],
        magasin_ids: Optional[List[int]] = None,
        include_stats: bool = True
    ) -> Dict[int, Dict[str, Any]]:
        """
        Récupère plusieurs prix enrichis en une seule opération.
        
        Args:
            produit_ids: Liste des IDs de produits
            magasin_ids: Liste des IDs de magasins (optionnel)
            include_stats: Inclure les statistiques
            
        Returns:
            Dictionnaire {produit_id: données_enrichies}
        """
        result = {}
        
        for produit_id in produit_ids:
            if magasin_ids:
                # Un prix par magasin pour ce produit
                for magasin_id in magasin_ids:
                    key = f"{produit_id}:{magasin_id}"
                    result[key] = cls.get_enriched_price(
                        produit_id,
                        magasin_id,
                        include_stats=include_stats
                    )
            else:
                # Prix sans magasin spécifique (meilleur prix)
                result[produit_id] = cls.get_enriched_price(
                    produit_id,
                    magasin_id=None,
                    include_stats=include_stats
                )
        
        return result
    
    @classmethod
    def invalidate_cache(
        cls,
        produit_id: Optional[int] = None,
        magasin_id: Optional[int] = None
    ) -> int:
        """
        Invalide le cache pour un produit et/ou magasin.
        
        Args:
            produit_id: ID du produit (si None, invalide tout)
            magasin_id: ID du magasin (optionnel)
            
        Returns:
            Nombre de clés invalidées
        """
        count = 0
        
        if produit_id:
            # Invalider les stats
            cache_key_stats = cls.get_cache_key_stats(produit_id)
            if cache.delete(cache_key_stats):
                count += 1
            
            # Invalider les prix enrichis
            if magasin_id:
                cache_key_price = cls.get_cache_key_price(produit_id, magasin_id)
                if cache.delete(cache_key_price):
                    count += 1
            else:
                # Invalider tous les prix de ce produit
                # Note: nécessite de connaître tous les magasins, ou utiliser un pattern
                cache_key_produit = cls.get_cache_key_produit(produit_id)
                if cache.delete(cache_key_produit):
                    count += 1
        else:
            # Invalider tout le cache (à utiliser avec précaution)
            logger.warning("Invalidation complète du cache des prix")
            # Pour une invalidation complète, il faudrait itérer sur toutes les clés
            # ou utiliser un namespace Redis. Pour l'instant, on log juste un warning.
        
        logger.info(f"Cache invalidé: {count} clé(s) pour produit={produit_id}, magasin={magasin_id}")
        return count

