"""
fusion_model.py — NOT YET IMPLEMENTED.

Step 6 of the build plan, and the part that makes this project a
multi-modal system rather than either an image classifier or a plain
tabular model on its own.

Planned pipeline:

    NumericalModel features  ---\
                                  >--  concatenate  -->  FC layer -> softmax
    ImageModel features       --/                        -> Normal/Moderate/Severe

Planned interface:

    def fuse_features(visual_features: np.ndarray,
                       numerical_features: np.ndarray) -> np.ndarray:
        # simple concatenation, per the architecture doc
        return np.concatenate([visual_features, numerical_features], axis=1)

    class FusionClassifier:
        def fit(self, X_fused, y): ...
        def predict(self, X_fused) -> np.ndarray: ...
        def predict_proba(self, X_fused) -> np.ndarray: ...

`predict.py` will grow a `predict_fused()` alongside the current
`predict_numerical()` once this exists — the numerical-only path stays
available rather than being replaced, since it's useful on its own when
only measurements (no photo) are available.
"""
