import numpy as np
from ml_models.modele_recommandation import ModeleRecommandationProduits


def main():
    # Exemple: 6 items, 4 features (illustratif)
    items = np.array([
        [1.0, 0.2, 0.1, 0.4],
        [0.9, 0.1, 0.2, 0.5],
        [0.1, 0.8, 0.7, 0.2],
        [0.2, 0.9, 0.6, 0.1],
        [0.5, 0.3, 0.2, 0.6],
        [0.15, 0.7, 0.65, 0.25],
    ])
    produits_ids = [101, 102, 103, 104, 105, 106]

    m = ModeleRecommandationProduits(n_neighbors=3)
    m.entrainer(items, produits_ids)
    recs = m.recommander_par_item(101, top_k=3)
    print("Recommandations pour 101:")
    for r in recs:
        print(r)


if __name__ == "__main__":
    main()
