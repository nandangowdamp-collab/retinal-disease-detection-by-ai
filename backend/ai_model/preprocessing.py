import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageOps

CLASS_NAMES = [
    "Normal",
    "Glaucoma",
    "Hypertensive Retinopathy",
    "Diabetic Retinopathy",
]

_INTERPOLATION_MODES = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
    "bicubic": Image.Resampling.BICUBIC,
    "lanczos": Image.Resampling.LANCZOS,
}

_NORMALIZATION_MODES = {"rescale_0_1", "minus_one_to_one", "none"}


class PreprocessingConfigError(ValueError):
    """Raised when preprocessing.json is missing or invalid."""


def load_preprocessing_config(config_path: str | Path) -> dict:
    path = Path(config_path)
    if not path.is_file():
        raise PreprocessingConfigError(f"Preprocessing config not found at {path}")

    with path.open("r", encoding="utf-8") as fh:
        config = json.load(fh)

    image_size = config.get("image_size")
    if (
        not isinstance(image_size, list)
        or len(image_size) != 2
        or not all(isinstance(d, int) and d >= 32 for d in image_size)
    ):
        raise PreprocessingConfigError("image_size must be a 2-element list of integers >= 32.")

    if config.get("color_mode", "RGB").upper() != "RGB":
        raise PreprocessingConfigError("color_mode must be 'RGB'.")

    interp = str(config.get("resize_interpolation", "bilinear")).lower()
    if interp not in _INTERPOLATION_MODES:
        raise PreprocessingConfigError(
            f"Unsupported resize_interpolation '{interp}'. Allowed: {sorted(_INTERPOLATION_MODES)}"
        )

    norm = str(config.get("normalization", "rescale_0_1")).lower()
    if norm not in _NORMALIZATION_MODES:
        raise PreprocessingConfigError(
            f"Unsupported normalization '{norm}'. Allowed: {sorted(_NORMALIZATION_MODES)}"
        )

    class_names = config.get("class_names")
    if not isinstance(class_names, list) or len(class_names) != 4 or set(class_names) != set(CLASS_NAMES):
        raise PreprocessingConfigError(
            f"class_names must contain the 4 target classes: {CLASS_NAMES}"
        )

    return {
        "model_version": str(config.get("model_version", "retinal-cnn-v1.0")),
        "image_size": image_size,
        "color_mode": "RGB",
        "resize_interpolation": interp,
        "normalization": norm,
        "class_names": class_names,
    }


def preprocess_image(image_path: str | Path, config: dict) -> np.ndarray:
    path = Path(image_path)
    if not path.is_file():
        raise ValueError(f"Retinal image file not found: {path}")

    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        if img.width < 32 or img.height < 32:
            raise ValueError("Image dimensions are too small (minimum 32x32 pixels).")

        rgb_img = img.convert("RGB")
        target_h, target_w = config["image_size"]
        resample = _INTERPOLATION_MODES[config["resize_interpolation"]]
        resized = rgb_img.resize((target_w, target_h), resample=resample)

        arr = np.asarray(resized, dtype=np.float32)

    norm = config["normalization"]
    if norm == "rescale_0_1":
        arr = arr / 255.0
    elif norm == "minus_one_to_one":
        arr = (arr / 127.5) - 1.0

    batch = np.expand_dims(arr, axis=0)
    return batch
