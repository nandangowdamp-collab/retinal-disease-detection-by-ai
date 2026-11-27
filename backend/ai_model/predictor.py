from pathlib import Path
import threading
import numpy as np

from ai_model.preprocessing import (
    PreprocessingConfigError,
    load_preprocessing_config,
    preprocess_image,
)


class ModelUnavailableError(RuntimeError):
    """Raised when the trained Keras model or its runtime/config is unavailable."""


class RetinalDiseasePredictor:
    def __init__(self, model_path: str | Path, config_path: str | Path):
        self.model_path = Path(model_path)
        self.config_path = Path(config_path)
        self._lock = threading.Lock()
        self._model = None
        self._config = None

    def is_ready(self) -> tuple[bool, str | None]:
        if not self.model_path.is_file():
            return False, f"Trained model file not found at {self.model_path}."
        if not self.config_path.is_file():
            return False, f"Preprocessing configuration not found at {self.config_path}."
        try:
            load_preprocessing_config(self.config_path)
        except PreprocessingConfigError as exc:
            return False, str(exc)
        return True, None

    def _ensure_loaded(self):
        with self._lock:
            if self._model is not None and self._config is not None:
                return self._model, self._config

            if not self.model_path.is_file() or not self.config_path.is_file():
                raise ModelUnavailableError(
                    "AI screening model is not configured yet. Place a trained Keras model at "
                    "backend/ai_model/retinal_model.keras and copy preprocessing.example.json "
                    "to preprocessing.json."
                )

            try:
                config = load_preprocessing_config(self.config_path)
            except PreprocessingConfigError as exc:
                raise ModelUnavailableError(f"Invalid preprocessing configuration: {exc}") from exc

            try:
                import tensorflow as tf
            except ImportError as exc:
                raise ModelUnavailableError(
                    "TensorFlow inference runtime is not installed. Install backend/requirements-ai.txt "
                    "in a supported environment to enable AI retinal screening."
                ) from exc

            try:
                model = tf.keras.models.load_model(str(self.model_path))
            except Exception as exc:
                raise ModelUnavailableError(f"Failed to load Keras model: {exc}") from exc

            expected_h, expected_w = config["image_size"]
            input_shape = getattr(model, "input_shape", None)
            if (
                not input_shape
                or len(input_shape) != 4
                or input_shape[1] not in (None, expected_h)
                or input_shape[2] not in (None, expected_w)
                or input_shape[3] != 3
            ):
                raise ModelUnavailableError(
                    f"Model input shape {input_shape} does not match configured RGB shape (None, {expected_h}, {expected_w}, 3)."
                )

            output_shape = getattr(model, "output_shape", None)
            if not output_shape or len(output_shape) != 2 or output_shape[1] != 4:
                raise ModelUnavailableError(
                    f"Model output shape {output_shape} does not match 4-class softmax output (None, 4)."
                )

            self._model = model
            self._config = config
            return self._model, self._config

    def predict(self, image_path: str | Path) -> dict:
        model, config = self._ensure_loaded()
        batch = preprocess_image(image_path, config)
        raw_preds = model.predict(batch, verbose=0)
        probs = np.asarray(raw_preds[0], dtype=np.float64)

        if probs.shape != (4,) or not np.all(np.isfinite(probs)):
            raise ModelUnavailableError("Model returned invalid prediction probabilities.")

        total = float(np.sum(probs))
        if total <= 0:
            raise ModelUnavailableError("Model returned non-positive probability sum.")
        if abs(total - 1.0) > 0.05 or np.any(probs < 0):
            # Apply softmax fallback if logits were returned
            exp = np.exp(probs - np.max(probs))
            probs = exp / np.sum(exp)
        else:
            probs = probs / total

        class_names = config["class_names"]
        best_idx = int(np.argmax(probs))
        class_scores = {
            name: round(float(score), 4) for name, score in zip(class_names, probs)
        }

        return {
            "predicted_class": class_names[best_idx],
            "confidence_score": round(float(probs[best_idx]), 4),
            "class_scores": class_scores,
            "model_version": config["model_version"],
        }


_predictor_override = None
_predictor_cache: dict[tuple[str, str], RetinalDiseasePredictor] = {}


def set_predictor_override(predictor) -> None:
    global _predictor_override
    _predictor_override = predictor


def get_predictor(model_path: str | Path, config_path: str | Path):
    if _predictor_override is not None:
        return _predictor_override
    key = (str(Path(model_path).resolve()), str(Path(config_path).resolve()))
    if key not in _predictor_cache:
        _predictor_cache[key] = RetinalDiseasePredictor(model_path, config_path)
    return _predictor_cache[key]
