import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import api, { getApiErrorMessage } from '../../services/api';
import { consultationService } from '../../services/consultationService';
import PredictionCard from '../../components/PredictionCard';
import DoctorLayout from './DoctorLayout';

export default function PatientDetails() {
  const { patientId } = useParams();
  const [details, setDetails] = useState(null);
  const [impression, setImpression] = useState('');
  const [notes, setNotes] = useState('');
  const [activePredId, setActivePredId] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadDetails = async () => {
    try {
      const { data } = await api.get(`/doctor/patients/${patientId}`);
      setDetails(data);
      if (!activePredId && data.predictions?.length > 0) {
        setActivePredId(data.predictions[0].id);
      }
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadDetails();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [patientId]);

  const handleSaveAssessment = async (e) => {
    e.preventDefault();
    if (!activePredId) return;
    setError('');
    setNotice('');
    try {
      await consultationService.addDoctorAssessment(activePredId, {
        clinical_impression: impression,
        assessment_notes: notes,
      });
      setNotice('Clinical assessment recorded separately from AI screening output.');
      setImpression('');
      setNotes('');
      loadDetails();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <DoctorLayout>
      <div className="page-header">
        <div>
          <h1>Patient Clinical Review</h1>
          <p>{details?.patient?.full_name} • {details?.profile?.age} yrs • {details?.profile?.gender}</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      {details && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div className="card">
            <h3 style={{ marginBottom: '0.6rem' }}>Patient Contact &amp; Profile</h3>
            <div className="grid-3" style={{ fontSize: '0.9rem' }}>
              <div><strong>Email:</strong> {details.patient.email}</div>
              <div><strong>Phone:</strong> {details.patient.phone}</div>
              <div><strong>Address:</strong> {details.profile?.address}</div>
            </div>
          </div>

          {details.predictions.length > 0 && (
            <form className="card" onSubmit={handleSaveAssessment}>
              <h3 style={{ marginBottom: '0.75rem' }}>Add Separate Physician Assessment</h3>
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Select Prediction Scan</label>
                  <select className="form-select" value={activePredId} onChange={(e) => setActivePredId(e.target.value)}>
                    {details.predictions.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.prediction_id} — {p.predicted_class}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Clinical Impression</label>
                  <input
                    className="form-input"
                    required
                    value={impression}
                    onChange={(e) => setImpression(e.target.value)}
                    placeholder="e.g. Confirm dilated fundus exam needed"
                  />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Assessment Notes</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter your clinical observations independent of AI score..."
                />
              </div>
              <button type="submit" className="btn btn-primary">Save Physician Assessment</button>
            </form>
          )}

          {details.predictions.map((pred) => (
            <PredictionCard key={pred.id} prediction={pred} />
          ))}
        </div>
      )}
    </DoctorLayout>
  );
}
