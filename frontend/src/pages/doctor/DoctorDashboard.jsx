import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { CalendarCheck, CheckCircle2, Clock, MessageSquare, Users } from 'lucide-react';
import api, { getApiErrorMessage } from '../../services/api';
import DoctorLayout from './DoctorLayout';
import '../../styles/dashboard.css';
import '../../styles/doctor.css';

export default function DoctorDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/doctor/dashboard')
      .then((res) => setData(res.data))
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const verification = data?.verification_status || 'pending';

  return (
    <DoctorLayout>
      <div className="page-header">
        <div>
          <h1>Doctor Dashboard — {data?.user?.full_name || 'Clinician'}</h1>
          <p>{data?.profile?.specialization} • {data?.profile?.hospital_name}</p>
        </div>
        <span className={`badge badge-${verification}`}>Verification: {verification}</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {verification !== 'verified' && data && (
        <div className="alert alert-warning">
          <span>
            <strong>Administrator Verification Required:</strong> Your account status is currently{' '}
            <strong>{verification}</strong>. Access to patient retinal records, consultations, and
            live messaging unlocks once an administrator verifies your medical registration.
          </span>
        </div>
      )}

      {loading ? (
        <div className="spinner" />
      ) : (
        data && (
          <>
            <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Assigned Patients</div>
                  <div className="stat-value">{data.stats.assigned_patients}</div>
                </div>
                <div className="stat-icon" style={{ background: '#dbeafe', color: '#1d4ed8' }}>
                  <Users size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Pending Requests</div>
                  <div className="stat-value">{data.stats.pending_consultations}</div>
                </div>
                <div className="stat-icon" style={{ background: '#fef3c7', color: '#b45309' }}>
                  <Clock size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Completed Consultations</div>
                  <div className="stat-value">{data.stats.completed_consultations}</div>
                </div>
                <div className="stat-icon" style={{ background: '#d1fae5', color: '#059669' }}>
                  <CheckCircle2 size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Unread Messages</div>
                  <div className="stat-value">{data.stats.unread_messages}</div>
                </div>
                <div className="stat-icon" style={{ background: '#ede9fe', color: '#6d28d9' }}>
                  <MessageSquare size={20} />
                </div>
              </div>
            </div>

            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>Recent Patient Activities &amp; Consultations</h3>
                {verification === 'verified' && (
                  <Link to="/doctor/consultations" className="btn btn-primary btn-sm">
                    <CalendarCheck size={15} />
                    Manage Consultations
                  </Link>
                )}
              </div>

              {data.recent_consultations.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No patient consultations assigned yet.</p>
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Patient</th>
                        <th>AI Classification</th>
                        <th>Reason</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_consultations.map((c) => (
                        <tr key={c.id}>
                          <td>{c.patient_name}</td>
                          <td>{c.prediction ? `${c.prediction.predicted_class} (${(c.prediction.confidence_score * 100).toFixed(1)}%)` : 'No scan attached'}</td>
                          <td>{c.consultation_reason}</td>
                          <td><span className={`badge badge-${c.consultation_status}`}>{c.consultation_status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </>
        )
      )}
    </DoctorLayout>
  );
}
