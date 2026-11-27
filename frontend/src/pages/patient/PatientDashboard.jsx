import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Activity, CalendarCheck, Image, MessageSquare, Upload } from 'lucide-react';
import api, { getApiErrorMessage } from '../../services/api';
import { getDiseaseBadgeClass } from '../../components/PredictionCard';
import PatientLayout from './PatientLayout';
import '../../styles/dashboard.css';
import '../../styles/patient.css';

export default function PatientDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/patient/dashboard')
      .then((res) => setData(res.data))
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <PatientLayout>
      <div className="page-header">
        <div>
          <h1>Welcome, {data?.user?.full_name || 'Patient'}</h1>
          <p>Monitor your retinal AI screening reports, doctor consultations, and messages.</p>
        </div>
        <Link to="/patient/upload" className="btn btn-primary">
          <Upload size={16} />
          New Retinal Screening
        </Link>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {loading ? (
        <div className="spinner" />
      ) : (
        data && (
          <>
            <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Images Uploaded</div>
                  <div className="stat-value">{data.stats.total_images}</div>
                </div>
                <div className="stat-icon" style={{ background: '#ccfbf1', color: '#0f766e' }}>
                  <Image size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">AI Predictions</div>
                  <div className="stat-value">{data.stats.total_predictions}</div>
                </div>
                <div className="stat-icon" style={{ background: '#e0f2fe', color: '#0284c7' }}>
                  <Activity size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Consultations</div>
                  <div className="stat-value">{data.stats.total_consultations}</div>
                </div>
                <div className="stat-icon" style={{ background: '#ede9fe', color: '#6d28d9' }}>
                  <CalendarCheck size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Unread Messages</div>
                  <div className="stat-value">{data.stats.unread_messages}</div>
                </div>
                <div className="stat-icon" style={{ background: '#fef3c7', color: '#b45309' }}>
                  <MessageSquare size={20} />
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3>Recent AI Predictions</h3>
                  <Link to="/patient/history" style={{ fontSize: '0.85rem', color: 'var(--brand-primary)', fontWeight: 600 }}>
                    View All
                  </Link>
                </div>
                {data.recent_predictions.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)' }}>No retinal classifications yet. Upload a scan to start.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem' }}>
                    {data.recent_predictions.map((p) => (
                      <div key={p.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.7rem', background: 'var(--bg-subtle)', borderRadius: 8 }}>
                        <div>
                          <div className="mono" style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{p.prediction_id}</div>
                          <div style={{ fontWeight: 600 }}>{p.predicted_class}</div>
                        </div>
                        <span className={`badge ${getDiseaseBadgeClass(p.predicted_class)}`}>
                          {(p.confidence_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                  <h3>Recent Consultations</h3>
                  <Link to="/patient/doctors" style={{ fontSize: '0.85rem', color: 'var(--brand-primary)', fontWeight: 600 }}>
                    Request Consultation
                  </Link>
                </div>
                {data.recent_consultations.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)' }}>No consultation requests yet.</p>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.7rem' }}>
                    {data.recent_consultations.map((c) => (
                      <div key={c.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.7rem', background: 'var(--bg-subtle)', borderRadius: 8 }}>
                        <div>
                          <div style={{ fontWeight: 600 }}>{c.doctor_name}</div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{c.consultation_reason}</div>
                        </div>
                        <span className={`badge badge-${c.consultation_status}`}>{c.consultation_status}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </>
        )
      )}
    </PatientLayout>
  );
}
