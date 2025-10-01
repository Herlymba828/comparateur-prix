from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, KFold

ArrayLike = Union[Sequence[float], np.ndarray]


@dataclass
class EvaluationResult:
    mae: float
    r2: float


class ModelePredictionPrix:
    """Modèle de régression linéaire avec normalisation.

    - Utilise un pipeline (StandardScaler + LinearRegression)
    - Fournit des méthodes d'entraînement, prédiction, évaluation et persistence (save/load)
    """

    def __init__(self) -> None:
        self.pipeline: Pipeline = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("reg", LinearRegression()),
            ]
        )
        self.est_entraine: bool = False

    @staticmethod
    def _to_2d(X: ArrayLike) -> np.ndarray:
        X_arr = np.asarray(X, dtype=float)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(-1, 1)
        return X_arr

    @staticmethod
    def _to_1d(y: ArrayLike) -> np.ndarray:
        y_arr = np.asarray(y, dtype=float).ravel()
        return y_arr

    def entrainer(self, X: ArrayLike, y: ArrayLike) -> bool:
        """Entraîne le modèle.

        X: array-like (n_samples, n_features) ou (n_samples,)
        y: array-like (n_samples,)
        """
        X_arr = self._to_2d(X)
        y_arr = self._to_1d(y)
        if len(X_arr) == 0 or len(y_arr) == 0:
            return False
        self.pipeline.fit(X_arr, y_arr)
        self.est_entraine = True
        return True

    def predire(self, X: ArrayLike) -> Optional[np.ndarray]:
        """Prédit les valeurs de prix.

        Retourne un np.ndarray (n_samples,) ou None si non entraîné.
        """
        if not self.est_entraine:
            return None
        X_arr = self._to_2d(X)
        preds = self.pipeline.predict(X_arr)
        return preds

    def evaluer(self, X: ArrayLike, y: ArrayLike) -> Optional[EvaluationResult]:
        if not self.est_entraine:
            return None
        X_arr = self._to_2d(X)
        y_arr = self._to_1d(y)
        y_pred = self.pipeline.predict(X_arr)
        return EvaluationResult(
            mae=float(mean_absolute_error(y_arr, y_pred)),
            r2=float(r2_score(y_arr, y_pred)),
        )

    def cross_valider(self, X: ArrayLike, y: ArrayLike, cv_splits: int = 5, random_state: int = 42) -> Dict[str, float]:
        """Effectue une validation croisée KFold et retourne les métriques moyennes.

        Ne nécessite pas que le pipeline soit déjà entraîné.
        """
        X_arr = self._to_2d(X)
        y_arr = self._to_1d(y)
        kf = KFold(n_splits=max(2, cv_splits), shuffle=True, random_state=random_state)
        maes: List[float] = []
        r2s: List[float] = []
        for train_idx, test_idx in kf.split(X_arr):
            self.pipeline.fit(X_arr[train_idx], y_arr[train_idx])
            preds = self.pipeline.predict(X_arr[test_idx])
            maes.append(float(mean_absolute_error(y_arr[test_idx], preds)))
            r2s.append(float(r2_score(y_arr[test_idx], preds)))
        # Remettre le flag entraîné à False car ce fit n'est pas le fit final
        self.est_entraine = False
        return {"mae_mean": float(np.mean(maes)), "mae_std": float(np.std(maes)), "r2_mean": float(np.mean(r2s)), "r2_std": float(np.std(r2s))}

    def grid_search(self, X: ArrayLike, y: ArrayLike, param_grid: Optional[Dict[str, List[Union[int, float, str]]]] = None, cv_splits: int = 5, n_jobs: int = 1) -> Dict[str, Union[float, Dict[str, Union[int, float, str]]]]:
        """Recherche d'hyperparamètres via GridSearchCV.

        param_grid s'applique aux étapes du pipeline (e.g., {'reg__fit_intercept': [True, False]})
        Retourne les meilleurs paramètres et le score (R² par défaut).
        """
        X_arr = self._to_2d(X)
        y_arr = self._to_1d(y)
        if param_grid is None:
            param_grid = {"reg__fit_intercept": [True, False], "reg__copy_X": [True]}
        gs = GridSearchCV(self.pipeline, param_grid=param_grid, cv=max(2, cv_splits), n_jobs=n_jobs, scoring="r2")
        gs.fit(X_arr, y_arr)
        # Met à jour le pipeline avec le meilleur estimateur
        self.pipeline = gs.best_estimator_  # type: ignore[assignment]
        self.est_entraine = True
        return {"best_score": float(gs.best_score_), "best_params": dict(gs.best_params_)}

    def save(self, path: str) -> None:
        joblib.dump({"pipeline": self.pipeline, "est_entraine": self.est_entraine}, path, compress=3)

    @classmethod
    def load(cls, path: str) -> "ModelePredictionPrix":
        data = joblib.load(path)
        obj = cls()
        obj.pipeline = data["pipeline"]
        obj.est_entraine = data.get("est_entraine", True)
        return obj