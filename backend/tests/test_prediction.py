import json
from pathlib import Path

from ai_model.predictor import set_predictor_override
from ai_model.preprocessing import load_preprocessing_config, preprocess_image
from tests.conftest import make_png_bytes, register_and_login_patient


class StubPredictor:
    def is_ready(self):
        return True, None

    def predict(self, _image_path):
        return {
            "predicted_class": "Diabetic Retinopathy",
            "confidence_score": 0.91,
            "class_scores": {
                "Normal": 0.03,
                "Glaucoma": 0.02,
                "Hypertensive Retinopathy": 0.04,
                "Diabetic Retinopathy": 0.91,
            },
            "model_version": "test-stub-v1",
        }


def test_unconfigured_model_returns_503_without_saving_prediction(client):
    token, _ = register_and_login_patient(client)
    res = client.post(
        "/api/prediction/classify",
        data={"image": (make_png_bytes(), "fundus.png")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 503
    hist = client.get("/api/prediction/history", headers={"Authorization": f"Bearer {token}"})
    assert hist.status_code == 200
    assert hist.get_json()["predictions"] == []


def test_invalid_file_upload_rejected(client):
    token, _ = register_and_login_patient(client)
    res = client.post(
        "/api/prediction/classify",
        data={"image": (b"not-an-image", "malicious.png")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400


def test_preprocessing_pipeline_shape_and_normalization(tmp_path):
    cfg_path = tmp_path / "preprocessing.json"
    cfg_path.write_text(
        json.dumps(
            {
                "model_version": "v1",
                "image_size": [224, 224],
                "color_mode": "RGB",
                "resize_interpolation": "bilinear",
                "normalization": "rescale_0_1",
                "class_names": [
                    "Normal",
                    "Glaucoma",
                    "Hypertensive Retinopathy",
                    "Diabetic Retinopathy",
                ],
            }
        ),
        encoding="utf-8",
    )
    img_path = tmp_path / "sample.png"
    img_path.write_bytes(make_png_bytes(300, 300).getvalue())
    cfg = load_preprocessing_config(cfg_path)
    tensor = preprocess_image(img_path, cfg)
    assert tensor.shape == (1, 224, 224, 3)
    assert 0.0 <= float(tensor.min()) <= float(tensor.max()) <= 1.0


def test_classify_history_protected_image_and_pdf_report(client):
    set_predictor_override(StubPredictor())
    token1, _ = register_and_login_patient(client, email="p1@example.com")
    token2, _ = register_and_login_patient(client, email="p2@example.com")

    res = client.post(
        "/api/prediction/classify",
        data={"image": (make_png_bytes(), "retina_od.png")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {token1}"},
    )
    assert res.status_code == 201
    pred = res.get_json()["prediction"]
    assert pred["predicted_class"] == "Diabetic Retinopathy"
    pred_id = pred["id"]

    # Owner can view image & PDF report
    img_res = client.get(f"/api/prediction/{pred_id}/image", headers={"Authorization": f"Bearer {token1}"})
    assert img_res.status_code == 200

    pdf_res = client.get(f"/api/prediction/{pred_id}/report", headers={"Authorization": f"Bearer {token1}"})
    assert pdf_res.status_code == 200
    assert pdf_res.mimetype == "application/pdf"
    assert pdf_res.data.startswith(b"%PDF")

    # Different patient cannot access image or report
    unauth_img = client.get(f"/api/prediction/{pred_id}/image", headers={"Authorization": f"Bearer {token2}"})
    assert unauth_img.status_code == 403
