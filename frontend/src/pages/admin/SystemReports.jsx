import { useEffect, useState } from 'react';
import api, { getApiErrorMessage } from '../../services/api';
import AdminLayout from './AdminLayout';

export default function SystemReports() {
  const [logs, setLogs] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [moderated, setModerated] = useState(null);
  const [settings, setSettings] = useState({
    allow_patient_registration: true,
    allow_doctor_registration: true,
    require_doctor_verification: true,
    max_upload_mb: 10,
    clinical_disclaimer: '',
  });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadAll = async () => {
    try {
      const [logRes, convRes, setRes] = await Promise.all([
        api.get('/admin/audit-logs'),
        api.get('/admin/conversations'),
        api.get('/admin/settings'),
      ]);
      setLogs(logRes.data.audit_logs || []);
      setConversations(convRes.data.conversations || []);
      if (setRes.data.settings) setSettings(setRes.data.settings);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    try {
      await api.put('/admin/settings', settings);
      setNotice('Platform settings saved.');
      loadAll();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleModerate = async (convId) => {
    const reason = window.prompt('Enter moderation audit reason:');
    if (!reason || !reason.trim()) return;
    try {
      const { data } = await api.get(`/admin/conversations/${convId}/moderate`, { params: { reason } });
      setModerated(data);
      loadAll();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <AdminLayout>
      <div className="page-header">
        <div>
          <h1>System Reports, Messenger Metadata &amp; Audit Logs</h1>
          <p>Private message contents remain hidden unless a conversation is flagged for audited moderation.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <form className="card" onSubmit={handleSaveSettings}>
          <h3 style={{ marginBottom: '1rem' }}>Platform Settings</h3>
          <div className="form-group">
            <label className="form-label">Max Retinal Upload Size (MB)</label>
            <input
              type="number"
              min="1"
              max="50"
              className="form-input"
              value={settings.max_upload_mb}
              onChange={(e) => setSettings({ ...settings, max_upload_mb: Number(e.target.value) })}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Clinical Disclaimer</label>
            <textarea
              className="form-textarea"
              rows={3}
              value={settings.clinical_disclaimer}
              onChange={(e) => setSettings({ ...settings, clinical_disclaimer: e.target.value })}
            />
          </div>
          <button type="submit" className="btn btn-primary">Save Platform Settings</button>
        </form>

        <div className="card">
          <h3 style={{ marginBottom: '1rem' }}>Messenger Metadata</h3>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Participants</th>
                  <th>Messages</th>
                  <th>Reported</th>
                </tr>
              </thead>
              <tbody>
                {conversations.map((c) => (
                  <tr key={c.id}>
                    <td>{c.patient_name} ↔ {c.doctor_name}</td>
                    <td>{c.message_count}</td>
                    <td>
                      {c.reported ? (
                        <button type="button" className="btn btn-danger btn-sm" onClick={() => handleModerate(c.id)}>
                          Review Flagged
                        </button>
                      ) : (
                        <span className="badge badge-normal">Normal</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {moderated && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>Audited Moderation View (Flagged Conversation)</h3>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setModerated(null)}>Close</button>
          </div>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Report Reason: {moderated.conversation.report_reason}
          </p>
          {moderated.messages.map((m) => (
            <div key={m.id} style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)', fontSize: '0.88rem' }}>
              <strong className="mono">{m.sender_id}</strong>: {m.message}
            </div>
          ))}
        </div>
      )}

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Security &amp; Administrative Audit Logs</h3>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Action</th>
                <th>Resource</th>
                <th>User ID</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td>{new Date(l.timestamp).toLocaleString()}</td>
                  <td className="mono">{l.action}</td>
                  <td>{l.resource_type} ({l.resource_id || '—'})</td>
                  <td className="mono">{l.user_id || 'system'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  );
}
