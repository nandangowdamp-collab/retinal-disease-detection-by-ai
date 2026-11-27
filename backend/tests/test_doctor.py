from ai_model.predictor import set_predictor_override
from tests.conftest import (
    create_and_login_admin,
    make_png_bytes,
    register_and_login_doctor,
    register_and_login_patient,
)
from tests.test_prediction import StubPredictor


def test_doctor_verification_and_consultation_workflow(app, client):
    set_predictor_override(StubPredictor())
    patient_token, patient_id = register_and_login_patient(client, email="pat@example.com")
    other_patient_token, other_patient_id = register_and_login_patient(client, email="other@example.com")
    doctor_token, doctor_id = register_and_login_doctor(client, email="doc@example.com")
    admin_token, _ = create_and_login_admin(app, client)

    # Pending doctor cannot access patients or consultations
    blocked = client.get("/api/doctor/patients", headers={"Authorization": f"Bearer {doctor_token}"})
    assert blocked.status_code == 403

    # Admin verifies doctor
    client.put(
        f"/api/admin/doctors/{doctor_id}/verify",
        json={"verification_status": "verified"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Patient classifies a scan & requests consultation
    pred_res = client.post(
        "/api/prediction/classify",
        data={"image": (make_png_bytes(), "scan.png")},
        content_type="multipart/form-data",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    pred_id = pred_res.get_json()["prediction"]["id"]

    cons_res = client.post(
        "/api/consultations",
        json={
            "doctor_id": doctor_id,
            "prediction_id": pred_id,
            "consultation_reason": "Review diabetic retinopathy flag",
        },
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    cons_id = cons_res.get_json()["consultation"]["id"]

    # Verified doctor sees assigned patient, NOT unassigned other patient
    patients_res = client.get("/api/doctor/patients", headers={"Authorization": f"Bearer {doctor_token}"})
    assert patients_res.status_code == 200
    assert len(patients_res.get_json()["patients"]) == 1

    unassigned = client.get(
        f"/api/doctor/patients/{other_patient_id}",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert unassigned.status_code == 403

    # Doctor accepts consultation and adds notes & clinical assessment
    accept_res = client.put(
        f"/api/doctor/consultations/{cons_id}",
        json={"consultation_status": "accepted"},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert accept_res.status_code == 200
    assert accept_res.get_json()["consultation"]["consultation_status"] == "accepted"

    notes_res = client.post(
        f"/api/doctor/consultations/{cons_id}/notes",
        json={
            "consultation_notes": "Recommend OCT scan and HbA1c review.",
            "recommendations": "Schedule in-clinic dilated exam.",
            "consultation_status": "completed",
        },
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert notes_res.status_code == 200
    assert notes_res.get_json()["consultation"]["consultation_status"] == "completed"

    assess_res = client.put(
        f"/api/doctor/predictions/{pred_id}/assessment",
        json={"clinical_impression": "Mild NPDR suspected", "assessment_notes": "Follow up in 4 weeks."},
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert assess_res.status_code == 200
    assert assess_res.get_json()["prediction"]["doctor_assessment"]["clinical_impression"] == "Mild NPDR suspected"
