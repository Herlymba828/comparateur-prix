#!/usr/bin/env python
import os
import sys
import argparse
import logging
from pathlib import Path

import numpy as np
from sklearn.model_selection import train_test_split

# Initialisation Django si besoin d'accès DB (non requis ici mais prêt)
def setup_django():
    # Rendre le script exécutable hors Django sans planter
    try:
        import django  # noqa: F401
    except ImportError:
        return False
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        import django as _django
        _django.setup()
        return True
    except Exception:
        return False


def get_logger():
    logger = logging.getLogger("ml_training")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def _gen_reco_data(num_items: int = 50, num_features: int = 8, seed: int = 42):
    rng = np.random.default_rng(seed)
    items_matrix = rng.normal(size=(num_items, num_features)).astype(float)
    produits_ids = list(range(1, num_items + 1))
    return items_matrix, produits_ids


def _gen_prix_regression(num_samples: int = 200, seed: int = 42):
    rng = np.random.default_rng(seed)
    X = rng.uniform(low=0.0, high=100.0, size=(num_samples, 1)).astype(float)
    noise = rng.normal(loc=0.0, scale=5.0, size=(num_samples,)).astype(float)
    y = 0.8 * X.ravel() + 50.0 + noise
    return X, y


def entrainer_modeles(*, save_dir: str | None, n_items: int, n_features: int, n_samples: int, seed: int) -> int:
    """Entraîne les modèles de recommandation et de prédiction de prix, puis les sauvegarde."""
    logger = get_logger()
    setup_django()

    out_dir = Path(save_dir or Path(__file__).resolve().parent / 'artifacts')
    out_dir.mkdir(parents=True, exist_ok=True)

    # Importer localement pour éviter coûts si script est importé comme module
    from .modele_recommandation import ModeleRecommandationProduits
    from .modele_prediction_prix import ModelePredictionPrix

    logger.info("Entraînement du modèle de recommandation…")
    items_matrix, produits_ids = _gen_reco_data(num_items=n_items, num_features=n_features, seed=seed)
    modele_reco = ModeleRecommandationProduits(n_neighbors=5)
    ok_reco = modele_reco.entrainer(items_matrix, produits_ids)
    if ok_reco:
        reco_path = out_dir / 'modele_recommandation.joblib'
        modele_reco.save(str(reco_path))
        logger.info(f"Modèle reco sauvegardé: {reco_path}")
    else:
        logger.error("Échec entraînement modèle de recommandation")

    logger.info("Entraînement du modèle de prédiction de prix…")
    X, y = _gen_prix_regression(num_samples=n_samples, seed=seed)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=seed)
    modele_prix = ModelePredictionPrix()
    ok_prix = modele_prix.entrainer(X_train, y_train)
    if ok_prix:
        eval_res = modele_prix.evaluer(X_test, y_test)
        prix_path = out_dir / 'modele_prediction_prix.joblib'
        modele_prix.save(str(prix_path))
        logger.info(f"Modèle prix sauvegardé: {prix_path}")
        if eval_res:
            logger.info(f"Evaluation Prix - MAE: {eval_res.mae:.3f} | R2: {eval_res.r2:.3f}")
    else:
        logger.error("Échec entraînement modèle prix")

    logger.info("Entraînement terminé.")
    return 0 if (ok_reco and ok_prix) else 1


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Entrainement des modèles ML")
    parser.add_argument('--save-dir', default=None, help='Répertoire de sortie des artefacts')
    parser.add_argument('--n-items', type=int, default=50, help="Nombre d'items pour le modèle reco")
    parser.add_argument('--n-features', type=int, default=8, help="Nombre de features par item")
    parser.add_argument('--n-samples', type=int, default=200, help="Nombre d'échantillons pour la régression")
    parser.add_argument('--seed', type=int, default=42, help='Graine aléatoire')
    return parser.parse_args(argv)


if __name__ == '__main__':
    args = parse_args()
    sys.exit(entrainer_modeles(save_dir=args.save_dir, n_items=args.n_items, n_features=args.n_features, n_samples=args.n_samples, seed=args.seed))