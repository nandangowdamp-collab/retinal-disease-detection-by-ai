from flask import Blueprint, Response, current_app, g, jsonify, request, send_file
from database.db import get_db
from models.patient_model import PatientModel
from models.prediction_model import PredictionModel
from models.user_model import UserModel
from services.image_service import resolve_upload_path
from services.prediction_service import (
    PredictionServiceError,
    classify_retinal_image,
    query_predictions,
    stage_retinal_upload,
)
from utils.decorators import require_roles
from utils.report_generator import generate_prediction_pdf

prediction_bp = Blueprint("prediction", __name__, url_prefix="/api/prediction")


def _can_access_prediction(pred_doc: dict, user_doc: dict) -> bool:
    role = user_doc.get("role")
    uid = str(user_doc["_id"])
    if role == "admin":
        return True
    if role == "patient":
        return pred_doc.get("patient_id") == uid
    if role == "doctor":
        db = get_db()
        doc_profile = db.doctors.find_one({"user_id": uid, "verification_status": "verified"})
        if not doc_profile:
            return False
        consult = db.consultations.find_one({"doctor_id": uid, "patient_id": pred_doc.get("patient_id")})
        return consult is not None
    return False


@prediction_bp.post("/upload")
@require_roles("patient")
def upload_retinal_image():
    file_storage = request.files.get("image") or request.files.get("file")
    try:
        res = stage_retinal_upload(g.current_user_id, file_storage, current_app.config)
        return jsonify(res), 201
    except PredictionServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@prediction_bp.post("/classify")
@require_roles("patient")
def classify_image():
    file_storage = request.files.get("image") or request.files.get("file")
    upload_id = request.form.get("upload_id")
    if not upload_id and request.is_json:
        upload_id = (request.get_json(silent=True) or {}).get("upload_id")
    try:
        prediction = classify_retinal_image(
            g.current_user_id, file_storage, upload_id, current_app.config
        )
        return jsonify({"prediction": prediction}), 201
    except PredictionServiceError as exc:
        return jsonify({"error": exc.message}), exc.status_code


@prediction_bp.get("/history")
@require_roles("patient")
def prediction_history():
    search = request.args.get("search", "")
    disease = request.args.get("disease", "")
    start_date = request.args.get("start_date", "")
    end_date = request.args.get("end_date", "")
    records = query_predictions(
        patient_id=g.current_user_id,
        search=search,
        disease=disease,
        start_date=start_date,
        end_date=end_date,
    )
    return jsonify({"predictions": records}), 200


@prediction_bp.get("/<prediction_id>")
@require_roles("patient", "doctor", "admin")
def get_prediction_detail(prediction_id: str):
    pred = PredictionModel.find_by_id(prediction_id)
    if not pred:
        return jsonify({"error": "Prediction not found."}), 404
    if not _can_access_prediction(pred, g.current_user):
        return jsonify({"error": "You are not authorized to view this prediction."}), 403

    pub = PredictionModel.to_public(pred)
    patient_user = UserModel.find_by_id(pred.get("patient_id"))
    pub["patient_name"] = patient_user.get("full_name") if patient_user else "Patient"
    pub["patient_email"] = patient_user.get("email") if patient_user else ""
    return jsonify({"prediction": pub}), 200


@prediction_bp.get("/<prediction_id>/image")
@require_roles("patient", "doctor", "admin")
def get_prediction_image(prediction_id: str):
    pred = PredictionModel.find_by_id(prediction_id)
    if not pred:
        return jsonify({"error": "Prediction not found."}), 404
    if not _can_access_prediction(pred, g.current_user):
        return jsonify({"error": "You are not authorized to access this retinal image."}), 403

    path = resolve_upload_path(current_app.config["UPLOAD_FOLDER"], pred["image_path"])
    if not path.is_file():
        return jsonify({"error": "Retinal image file not found on server."}), 404
    return send_file(str(path))


@prediction_bp.get("/<prediction_id>/report")
@require_roles("patient", "doctor", "admin")
def download_prediction_report(prediction_id: str):
    pred = PredictionModel.find_by_id(prediction_id)
    if not pred:
        return jsonify({"error": "Prediction not found."}), 404
    if not _can_access_prediction(pred, g.current_user):
        return jsonify({"error": "You are not authorized to download this report."}), 403

    pub = PredictionModel.to_public(pred)
    patient_user = UserModel.find_by_id(pred.get("patient_id")) or {}
    patient_profile = PatientModel.find_by_user_id(pred.get("patient_id")) or {}
    patient_info = {
        "full_name": patient_user.get("full_name", "Patient"),
        "email": patient_user.get("email", "N/A"),
        "phone": patient_user.get("phone", "N/A"),
        "age": patient_profile.get("age", "N/A"),
        "gender": patient_profile.get("gender", "N/A"),
    }
    img_path = resolve_upload_path(current_app.config["UPLOAD_FOLDER"], pred["image_path"])
    pdf_bytes = generate_prediction_pdf(pub, patient_info, img_path)
    filename = f"{pub.get('prediction_id', 'retinal-report')}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
