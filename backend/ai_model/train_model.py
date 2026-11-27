"""
Training and evaluation pipeline for the 4-class Retinal Fundus Classifier.

Requires optional AI dependencies (`pip install -r requirements-ai.txt`).
Supports patient-level splitting (preventing patient-level data leakage),
data augmentation, transfer learning (EfficientNetB0, MobileNetV2, ResNet50)
or a custom CNN, and exports `retinal_model.keras` + `preprocessing.json`.
"""

import argparse
import csv
import json
from pathlib import Path
import time

CLASS_NAMES = [
    "Normal",
    "Glaucoma",
    "Hypertensive Retinopathy",
    "Diabetic Retinopathy",
]


def load_metadata_csv(csv_path: Path, data_dir: Path):
    rows = []
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            label = row["label"].strip()
            if label not in CLASS_NAMES:
                raise ValueError(f"Unknown label '{label}'. Expected one of {CLASS_NAMES}")
            img_path = data_dir / row["image_path"].strip()
            patient_id = row.get("patient_id") or img_path.stem.split("_")[0]
            rows.append((str(img_path), CLASS_NAMES.index(label), patient_id))
    return rows


def build_model(arch: str, image_size: tuple[int, int]):
    import tensorflow as tf
    from tensorflow.keras import layers, models

    inputs = layers.Input(shape=(image_size[0], image_size[1], 3))
    aug = models.Sequential(
        [
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.08),
            layers.RandomZoom(0.1),
            layers.RandomContrast(0.1),
        ],
        name="augmentation",
    )
    x = aug(inputs)

    if arch == "custom_cnn":
        for filters in (32, 64, 128, 256):
            x = layers.Conv2D(filters, 3, padding="same", activation="relu")(x)
            x = layers.BatchNormalization()(x)
            x = layers.MaxPooling2D()(x)
            x = layers.Dropout(0.2)(x)
        x = layers.GlobalAveragePooling2D()(x)
    else:
        backbones = {
            "mobilenetv2": tf.keras.applications.MobileNetV2,
            "efficientnetb0": tf.keras.applications.EfficientNetB0,
            "resnet50": tf.keras.applications.ResNet50,
        }
        backbone_cls = backbones[arch]
        base = backbone_cls(include_top=False, weights="imagenet", input_shape=(image_size[0], image_size[1], 3))
        base.trainable = False
        x = base(x, training=False)
        x = layers.GlobalAveragePooling2D()(x)

    x = layers.Dropout(0.35)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.25)(x)
    outputs = layers.Dense(len(CLASS_NAMES), activation="softmax")(x)
    return models.Model(inputs, outputs)


def main():
    parser = argparse.ArgumentParser(description="Train 4-class Retinal Disease Classifier")
    parser.add_argument("--data-dir", required=True, help="Root folder of retinal images")
    parser.add_argument("--metadata-csv", required=True, help="CSV with image_path,label,patient_id")
    parser.add_argument("--arch", default="mobilenetv2", choices=["custom_cnn", "mobilenetv2", "efficientnetb0", "resnet50"])
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--output-dir", default="ai_model")
    args = parser.parse_args()

    import numpy as np
    from PIL import Image
    from sklearn.metrics import classification_report, confusion_matrix
    from sklearn.model_selection import GroupShuffleSplit
    import tensorflow as tf

    rows = load_metadata_csv(Path(args.metadata_csv), Path(args.data_dir))
    paths = np.array([r[0] for r in rows])
    labels = np.array([r[1] for r in rows])
    groups = np.array([r[2] for r in rows])

    gss_test = GroupShuffleSplit(n_splits=1, test_size=0.15, random_state=42)
    train_val_idx, test_idx = next(gss_test.split(paths, labels, groups))

    gss_val = GroupShuffleSplit(n_splits=1, test_size=0.176, random_state=42)
    train_rel_idx, val_rel_idx = next(
        gss_val.split(paths[train_val_idx], labels[train_val_idx], groups[train_val_idx])
    )
    train_idx = train_val_idx[train_rel_idx]
    val_idx = train_val_idx[val_rel_idx]

    target_size = (args.image_size, args.image_size)

    def load_split(indices):
        images = []
        for p in paths[indices]:
            with Image.open(p) as img:
                arr = np.asarray(img.convert("RGB").resize(target_size, Image.Resampling.BILINEAR), dtype=np.float32)
                images.append(arr / 255.0)
        return np.array(images), labels[indices]

    x_train, y_train = load_split(train_idx)
    x_val, y_val = load_split(val_idx)
    x_test, y_test = load_split(test_idx)

    model = build_model(args.arch, target_size)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2),
    ]
    model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=args.epochs,
        batch_size=args.batch_size,
        callbacks=callbacks,
    )

    start = time.perf_counter()
    preds = np.argmax(model.predict(x_test, batch_size=args.batch_size), axis=1)
    elapsed = time.perf_counter() - start
    print(f"Test inference time: {elapsed:.3f}s ({elapsed / max(len(x_test), 1):.4f}s/image)")
    print(classification_report(y_test, preds, target_names=CLASS_NAMES))
    print("Confusion Matrix:\n", confusion_matrix(y_test, preds))

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    model.save(out_dir / "retinal_model.keras")

    config = {
        "model_version": f"retinal-{args.arch}-v1.0",
        "image_size": [args.image_size, args.image_size],
        "color_mode": "RGB",
        "resize_interpolation": "bilinear",
        "normalization": "rescale_0_1",
        "class_names": CLASS_NAMES,
    }
    with (out_dir / "preprocessing.json").open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2)


if __name__ == "__main__":
    main()
