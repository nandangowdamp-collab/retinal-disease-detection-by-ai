import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, MessageSquare } from 'lucide-react';
import api, { getApiErrorMessage } from '../../services/api';
import { messageService } from '../../services/messageService';
import { getDiseaseBadgeClass } from '../../components/PredictionCard';
import DoctorLayout from './DoctorLayout';

export default function MyPatients() {
  const navigate = useNavigate();
  const [patients, setPatients] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/doctor/patients')
      .then((res) => setPatients(res.data.patients || []))
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const handleChat = async (patientId) => {
    try {
      const res = await messageService.startConversation(patientId, 'doctor');
      navigate(`/doctor/messenger?conversationId=${res.conversation.id}`);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <DoctorLayout>
      <div className="page-header">
        <div>
          <h1>Assigned Patients</h1>
          <p>View patients who have requested or authorized consultations with you.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <div className="spinner" />
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Demographics</th>
                <th>Latest AI Scan</th>
                <th>Predictions</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {patients.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem' }}>
                    No assigned patients found.
                  </td>
                </tr>
              ) : (
                patients.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{p.full_name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{p.email}</div>
                    </td>
                    <td>{p.age} yrs • {p.gender}</td>
                    <td>
                      {p.latest_prediction ? (
                        <span className={`badge ${getDiseaseBadgeClass(p.latest_prediction.predicted_class)}`}>
                          {p.latest_prediction.predicted_class} ({(p.latest_prediction.confidence_score * 100).toFixed(1)}%)
                        </span>
                      ) : (
                        'None'
                      )}
                    </td>
                    <td>{p.prediction_count}</td>
                    <td>
                      <div className="doctor-action-row">
                        <Link to={`/doctor/patients/${p.id}`} className="btn btn-primary btn-sm">
                          <Eye size={14} />
                          Review Records
                        </Link>
                        <button type="button" className="btn btn-secondary btn-sm" onClick={() => handleChat(p.id)}>
                          <MessageSquare size={14} />
                          Chat
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </DoctorLayout>
  );
}
