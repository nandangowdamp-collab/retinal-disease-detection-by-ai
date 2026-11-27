import { useEffect, useState } from 'react';
import api, { getApiErrorMessage } from '../../services/api';
import { consultationService } from '../../services/consultationService';
import DoctorLayout from './DoctorLayout';

export default function Consultations() {
  const [consultations, setConsultations] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [editing, setEditing] = useState(null);
  const [notes, setNotes] = useState('');
  const [recommendations, setRecommendations] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadConsultations = async () => {
    try {
      const { data } = await api.get('/doctor/consultations', { params: { status: statusFilter } });
      setConsultations(data.consultations || []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadConsultations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusFilter]);

  const handleStatusChange = async (id, status) => {
    setError('');
    setNotice('');
    let rejection_reason = '';
    if (status === 'rejected') {
      rejection_reason = window.prompt('Enter rejection reason for patient:') || '';
      if (!rejection_reason.trim()) return;
    }
    try {
      await consultationService.updateDoctorConsultation(id, {
        consultation_status: status,
        rejection_reason,
      });
      setNotice(`Consultation marked as ${status}.`);
      loadConsultations();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleSaveNotes = async (e) => {
    e.preventDefault();
    if (!editing) return;
    try {
      await consultationService.addConsultationNotes(editing.id, {
        consultation_notes: notes,
        recommendations,
      });
      setNotice('Consultation notes updated.');
      setEditing(null);
      loadConsultations();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <DoctorLayout>
      <div className="page-header">
        <div>
          <h1>Consultation Management</h1>
          <p>Accept or reject consultation requests, add clinical notes, and record recommendations.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="filter-bar">
        <select className="form-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="completed">Completed</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      {editing && (
        <form className="card" style={{ marginBottom: '1.25rem' }} onSubmit={handleSaveNotes}>
          <h3 style={{ marginBottom: '0.75rem' }}>Notes for {editing.patient_name}</h3>
          <div className="form-group">
            <label className="form-label">Consultation Notes</label>
            <textarea className="form-textarea" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          <div className="form-group">
            <label className="form-label">Recommendations</label>
            <textarea className="form-textarea" rows={2} value={recommendations} onChange={(e) => setRecommendations(e.target.value)} />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="submit" className="btn btn-primary">Save Notes</button>
            <button type="button" className="btn btn-secondary" onClick={() => setEditing(null)}>Cancel</button>
          </div>
        </form>
      )}

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Patient</th>
              <th>Reason &amp; AI Scan</th>
              <th>Status</th>
              <th>Notes / Recommendations</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {consultations.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                  No consultation records match this filter.
                </td>
              </tr>
            ) : (
              consultations.map((c) => (
                <tr key={c.id}>
                  <td>{c.patient_name}</td>
                  <td>
                    <div>{c.consultation_reason}</div>
                    {c.prediction && (
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Scan: {c.prediction.prediction_id} — {c.prediction.predicted_class}
                      </div>
                    )}
                  </td>
                  <td><span className={`badge badge-${c.consultation_status}`}>{c.consultation_status}</span></td>
                  <td>{c.recommendations || c.consultation_notes || c.rejection_reason || '—'}</td>
                  <td>
                    <div className="doctor-action-row">
                      {c.consultation_status === 'pending' && (
                        <>
                          <button type="button" className="btn btn-primary btn-sm" onClick={() => handleStatusChange(c.id, 'accepted')}>
                            Accept
                          </button>
                          <button type="button" className="btn btn-danger btn-sm" onClick={() => handleStatusChange(c.id, 'rejected')}>
                            Reject
                          </button>
                        </>
                      )}
                      {c.consultation_status === 'accepted' && (
                        <button type="button" className="btn btn-primary btn-sm" onClick={() => handleStatusChange(c.id, 'completed')}>
                          Complete
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => {
                          setEditing(c);
                          setNotes(c.consultation_notes || '');
                          setRecommendations(c.recommendations || '');
                        }}
                      >
                        Notes
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </DoctorLayout>
  );
}
