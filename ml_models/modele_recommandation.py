from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence

import joblib
import numpy as np
from sklearn.neighbors import NearestNeighbors


Array2D = np.ndarray


@dataclass
class Recommandation:
    produit_id: int
    score: float


class ModeleRecommandationProduits:
    """Modèle KNN basé sur similarité cosinus entre vecteurs d'articles.

    - Entrée: matrice (n_items, n_features) + liste des `produits_ids` alignée sur les lignes
    - Recommandations par similarité d'article (item-to-item) ou depuis un vecteur utilisateur moyen
    - Persistence avec joblib
    """

    def __init__(self, n_neighbors: int = 10, metric: str = "cosine", n_jobs: int = -1) -> None:
        self.knn = NearestNeighbors(n_neighbors=n_neighbors, metric=metric, n_jobs=n_jobs)
        self.items_matrix: Optional[Array2D] = None
        self.produits_ids: List[int] = []
        self.est_entraine: bool = False

    def entrainer(self, items_matrix: Array2D, produits_ids: Sequence[int]) -> bool:
        if items_matrix is None or len(items_matrix) == 0:
            return False
        if len(items_matrix) != len(produits_ids):
            raise ValueError("items_matrix et produits_ids doivent être alignés")
        self.items_matrix = np.asarray(items_matrix, dtype=float)
        self.produits_ids = list(map(int, produits_ids))
        self.knn.fit(self.items_matrix)
        self.est_entraine = True
        return True

    def recommander_par_item(self, produit_id: int, top_k: int = 5) -> List[Recommandation]:
        if not self.est_entraine or self.items_matrix is None:
            return []
        try:
            idx = self.produits_ids.index(int(produit_id))
        except ValueError:
            return []
        distances, indices = self.knn.kneighbors(self.items_matrix[idx : idx + 1], n_neighbors=min(top_k + 1, len(self.produits_ids)))
        recs: List[Recommandation] = []
        for d, i in zip(distances[0], indices[0]):
            pid = self.produits_ids[i]
            if pid == produit_id:
                continue  # ignorer l'élément source
            recs.append(Recommandation(produit_id=pid, score=float(1.0 - d)))  # similarité ~ 1 - distance cos
            if len(recs) >= top_k:
                break
        return recs

    def recommander_par_vecteur(self, vecteur: Sequence[float], top_k: int = 5) -> List[Recommandation]:
        if not self.est_entraine or self.items_matrix is None:
            return []
        v = np.asarray(vecteur, dtype=float).reshape(1, -1)
        distances, indices = self.knn.kneighbors(v, n_neighbors=min(top_k, len(self.produits_ids)))
        return [Recommandation(produit_id=self.produits_ids[i], score=float(1.0 - d)) for d, i in zip(distances[0], indices[0])]

    def save(self, path: str) -> None:
        joblib.dump(
            {
                "knn": self.knn,
                "items_matrix": self.items_matrix,
                "produits_ids": self.produits_ids,
                "est_entraine": self.est_entraine,
            },
            path,
            compress=3,
        )

    @classmethod
    def load(cls, path: str) -> "ModeleRecommandationProduits":
        data = joblib.load(path)
        obj = cls()
        obj.knn = data["knn"]
        obj.items_matrix = data["items_matrix"]
        obj.produits_ids = list(map(int, data.get("produits_ids", [])))
        obj.est_entraine = data.get("est_entraine", True)
        return obj