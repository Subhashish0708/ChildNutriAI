"""
image_model.py — NOT YET IMPLEMENTED.

Step 5 of the build plan. Comes after numerical_model.py / train_model.py /
predict.py are working on the anthropometric data alone.

Planned pipeline (see preprocessing.prepare_image_input for the resize/
normalize step already in place):

    Child image
        -> Resize
        -> Normalization
        -> Data augmentation (training only)
        -> EfficientNet-B0 (transfer learning, not trained from scratch)
        -> Visual feature vector

Planned interface, mirroring numerical_model.NumericalModel so
fusion_model.py can treat both branches the same way:

    class ImageModel:
        def fit(self, X_images, y): ...
        def extract_features(self, X_images) -> np.ndarray: ...
        def predict(self, X_images) -> np.ndarray: ...
        def save(self, path): ...
        @classmethod
        def load(cls, path): ...
"""
