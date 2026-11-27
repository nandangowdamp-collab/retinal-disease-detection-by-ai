import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { MessageSquare, Stethoscope } from 'lucide-react';
import { getApiErrorMessage } from '../../services/api';
import { consultationService } from '../../services/consultationService';
import { messageService } from '../../services/messageService';
import { predictionService } from '../../services/predictionService';
import PatientLayout from './PatientLayout';

export default function FindDoctor() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [doctors, setDoctors] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [consultations, setConsultations] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedDoctor, setSelectedDoctor] = useState(null);
  const [predictionId, setPredictionId] = useState(searchParams.get('predictionId') || '');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadData = async (q = search) => {
    try {
      const [docRes, predRes, consRes] = await Promise.all([
        consultationService.getAvailableDoctors(q),
        predictionService.getHistory(),
        consultationService.listConsultations(),
      ]);
      setDoctors(docRes.doctors || []);
      setPredictions(predRes.predictions || []);
      setConsultations(consRes.consultations || []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadData('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRequestConsultation = async (e) => {
    e.preventDefault();
    if (!selectedDoctor) return;
    setError('');
    setNotice('');
    try {
      await consultationService.requestConsultation({
        doctor_id: selectedDoctor.id,
        prediction_id: predictionId || undefined,
        consultation_reason: reason,
      });
      setNotice(`Consultation request sent to ${selectedDoctor.full_name}.`);
      setSelectedDoctor(null);
      setReason('');
      loadData();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleOpenMessenger = async (doctorId) => {
    try {
      const res = await messageService.startConversation(doctorId, 'patient');
      navigate(`/patient/messenger?conversationId=${res.conversation.id}`);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <PatientLayout>
      <div className="page-header">
        <div>
          <h1>Verified Eye Specialists &amp; Consultations</h1>
          <p>Browse verified ophthalmologists, request a consultation, or start a direct chat.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="filter-bar">
        <input
          type="text"
          className="form-input"
          placeholder="Search doctor name, specialization, hospital..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="button" className="btn btn-primary" onClick={() => loadData(search)}>
          Search Doctors
        </button>
      </div>

      {selectedDoctor && (
        <form className="card" style={{ marginBottom: '1.5rem' }} onSubmit={handleRequestConsultation}>
          <h3 style={{ marginBottom: '0.75rem' }}>Request Consultation with {selectedDoctor.full_name}</h3>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Attach Retinal Prediction (optional)</label>
              <select className="form-select" value={predictionId} onChange={(e) => setPredictionId(e.target.value)}>
                <option value="">None</option>
                {predictions.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.prediction_id} — {p.predicted_class} ({(p.confidence_score * 100).toFixed(1)}%)
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Consultation Reason / Symptoms</label>
              <input
                type="text"
                className="form-input"
                required
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="Please review my recent retinal screening result..."
              />
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.6rem' }}>
            <button type="submit" className="btn btn-primary">Submit Request</button>
            <button type="button" className="btn btn-secondary" onClick={() => setSelectedDoctor(null)}>Cancel</button>
          </div>
        </form>
      )}

      <div className="grid-3" style={{ marginBottom: '1.75rem' }}>
        {doctors.length === 0 ? (
          <div className="card" style={{ gridColumn: '1 / -1', color: 'var(--text-muted)' }}>
            No verified doctors found yet. An administrator must verify registered doctors first.
          </div>
        ) : (
          doctors.map((doc) => (
            <div key={doc.id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.08rem' }}>{doc.full_name}</h3>
                  <div style={{ fontSize: '0.84rem', color: 'var(--brand-primary)', fontWeight: 600 }}>
                    {doc.specialization}
                  </div>
                </div>
                <span className="badge badge-verified">Verified</span>
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.9rem' }}>
                <div>{doc.qualification}</div>
                <div>{doc.hospital_name} • {doc.experience} yrs exp.</div>
                <div>Availability: {doc.availability}</div>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <button type="button" className="btn btn-primary btn-sm" onClick={() => setSelectedDoctor(doc)}>
                  <Stethoscope size={14} />
                  Consult
                </button>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => handleOpenMessenger(doc.id)}>
                  <MessageSquare size={14} />
                  Message
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>My Consultation Requests</h3>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Doctor</th>
                <th>Linked Scan</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Recommendations / Notes</th>
              </tr>
            </thead>
            <tbody>
              {consultations.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No consultation requests submitted.</td>
                </tr>
              ) : (
                consultations.map((c) => (
                  <tr key={c.id}>
                    <td>{c.doctor_name}</td>
                    <td>{c.prediction ? `${c.prediction.prediction_id} (${c.prediction.predicted_class})` : '—'}</td>
                    <td>{c.consultation_reason}</td>
                    <td><span className={`badge badge-${c.consultation_status}`}>{c.consultation_status}</span></td>
                    <td>{c.recommendations || c.consultation_notes || c.rejection_reason || 'Awaiting doctor review'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </PatientLayout>
  );
}
