"""Tiny Iris classifier for demo predictions (sklearn)."""

from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier

_iris = load_iris()
_model = RandomForestClassifier(n_estimators=50, random_state=42)
_model.fit(_iris.data, _iris.target)

SPECIES = _iris.target_names.tolist()


def predict_species(features: list[float]) -> tuple[int, str]:
    if len(features) != _iris.data.shape[1]:
        raise ValueError(
            f"Expected { _iris.data.shape[1] } features, got {len(features)}"
        )
    idx = int(_model.predict([features])[0])
    return idx, SPECIES[idx]
