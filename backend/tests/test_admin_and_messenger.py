from app import socketio
from tests.conftest import (
    create_and_login_admin,
    register_and_login_doctor,
    register_and_login_patient,
)


def test_realtime_messenger_privacy_and_admin_moderation(app, client):
    patient_token, _ = register_and_login_patient(client, email="msgpat@example.com")
    intruder_token, _ = register_and_login_patient(client, email="intruder@example.com")
    doctor_token, doctor_id = register_and_login_doctor(client, email="msgdoc@example.com", reg_num="MED-998")
    admin_token, _ = create_and_login_admin(app, client)

    # Verify doctor
    client.put(
        f"/api/admin/doctors/{doctor_id}/verify",
        json={"verification_status": "verified"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Patient starts conversation
    conv_res = client.post(
        "/api/messages/conversations",
        json={"doctor_id": doctor_id},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert conv_res.status_code == 201
    conv_id = conv_res.get_json()["conversation"]["id"]

    # Socket.IO real-time messaging between patient and doctor
    s_pat = socketio.test_client(app, auth={"token": patient_token})
    s_doc = socketio.test_client(app, auth={"token": doctor_token})
    assert s_pat.is_connected()
    assert s_doc.is_connected()

    s_pat.emit("join_conversation", {"conversation_id": conv_id})
    s_doc.emit("join_conversation", {"conversation_id": conv_id})

    s_pat.emit("send_message", {"conversation_id": conv_id, "message": "Hello Doctor, I uploaded my scan."})
    doc_events = s_doc.get_received()
    assert any(
        ev["name"] == "new_message" and ev["args"][0]["message"] == "Hello Doctor, I uploaded my scan."
        for ev in doc_events
    )

    # Intruder cannot read or send in conversation
    intruder_read = client.get(f"/api/messages/{conv_id}", headers={"Authorization": f"Bearer {intruder_token}"})
    assert intruder_read.status_code == 403

    # Admin metadata view does not expose private message content
    meta_res = client.get("/api/admin/conversations", headers={"Authorization": f"Bearer {admin_token}"})
    assert meta_res.status_code == 200
    conv_meta = meta_res.get_json()["conversations"][0]
    assert "last_message" not in conv_meta
    assert conv_meta["message_count"] == 1

    # Admin cannot moderate unflagged conversation
    blocked_mod = client.get(
        f"/api/admin/conversations/{conv_id}/moderate",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert blocked_mod.status_code == 403

    # Patient reports conversation -> Admin can open audited moderation view
    rep = client.post(
        f"/api/messages/conversations/{conv_id}/report",
        json={"reason": "Abuse check test"},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert rep.status_code == 200

    mod_res = client.get(
        f"/api/admin/conversations/{conv_id}/moderate?reason=Reviewing+report",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert mod_res.status_code == 200
    assert len(mod_res.get_json()["messages"]) == 1

    logs_res = client.get("/api/admin/audit-logs", headers={"Authorization": f"Bearer {admin_token}"})
    assert any(l["action"] == "ADMIN_MODERATED_CONVERSATION" for l in logs_res.get_json()["audit_logs"])
