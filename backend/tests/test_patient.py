from tests.conftest import (
    create_and_login_admin,
    register_and_login_doctor,
    register_and_login_patient,
)


def test_patient_dashboard_profile_and_consultation_request(app, client):
    patient_token, _ = register_and_login_patient(client)
    _, doctor_id = register_and_login_doctor(client)
    admin_token, _ = create_and_login_admin(app, client)

    # Unverified doctor should not appear in patient's available doctor list
    docs_before = client.get("/api/patient/doctors", headers={"Authorization": f"Bearer {patient_token}"})
    assert docs_before.status_code == 200
    assert docs_before.get_json()["doctors"] == []

    # Verify doctor as admin
    verify_res = client.put(
        f"/api/admin/doctors/{doctor_id}/verify",
        json={"verification_status": "verified"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert verify_res.status_code == 200

    docs_after = client.get("/api/patient/doctors", headers={"Authorization": f"Bearer {patient_token}"})
    assert len(docs_after.get_json()["doctors"]) == 1

    # Request consultation
    cons_res = client.post(
        "/api/consultations",
        json={"doctor_id": doctor_id, "consultation_reason": "Blurred vision screening follow-up"},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert cons_res.status_code == 201
    assert cons_res.get_json()["consultation"]["consultation_status"] == "pending"

    # Update patient profile
    upd = client.put(
        "/api/patient/profile",
        json={"full_name": "Aarav Updated", "age": 39},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert upd.status_code == 200
    assert upd.get_json()["user"]["full_name"] == "Aarav Updated"
    assert upd.get_json()["profile"]["age"] == 39

    dash = client.get("/api/patient/dashboard", headers={"Authorization": f"Bearer {patient_token}"})
    assert dash.status_code == 200
    assert dash.get_json()["stats"]["total_consultations"] == 1
