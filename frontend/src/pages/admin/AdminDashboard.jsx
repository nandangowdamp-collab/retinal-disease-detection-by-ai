import { useEffect, useState } from 'react';
import { Activity, CalendarCheck, MessageSquare, ShieldAlert, Stethoscope, Users } from 'lucide-react';
import api, { getApiErrorMessage } from '../../services/api';
import AdminLayout from './AdminLayout';
import '../../styles/dashboard.css';
import '../../styles/admin.css';

const DISEASE_COLORS = {
  Normal: '#059669',
  Glaucoma: '#d97706',
  'Hypertensive Retinopathy': '#7c3aed',
  'Diabetic Retinopathy': '#dc2626',
};

export default function AdminDashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get('/admin/dashboard')
      .then((res) => setData(res.data))
      .catch((err) => setError(getApiErrorMessage(err)))
      .finally(() => setLoading(false));
  }, []);

  const diseaseTotal = data
    ? Math.max(1, Object.values(data.charts.disease_distribution || {}).reduce((a, b) => a + b, 0))
    : 1;
  const consultTotal = data
    ? Math.max(1, Object.values(data.charts.consultation_status || {}).reduce((a, b) => a + b, 0))
    : 1;

  return (
    <AdminLayout>
      <div className="page-header">
        <div>
          <h1>Platform Administration Dashboard</h1>
          <p>Monitor patients, doctor verifications, retinal AI classifications, and consultations.</p>
        </div>
        {data?.model_status && (
          <span className={`badge ${data.model_status.ready ? 'badge-verified' : 'badge-pending'}`}>
            AI Model: {data.model_status.ready ? 'Ready' : 'Not Configured'}
          </span>
        )}
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {data?.model_status && !data.model_status.ready && (
        <div className="alert alert-warning">{data.model_status.message}</div>
      )}

      {loading ? (
        <div className="spinner" />
      ) : (
        data && (
          <>
            <div className="grid-4" style={{ marginBottom: '1.25rem' }}>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Registered Patients</div>
                  <div className="stat-value">{data.stats.total_patients}</div>
                </div>
                <div className="stat-icon" style={{ background: '#ccfbf1', color: '#0f766e' }}>
                  <Users size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Verified / Total Doctors</div>
                  <div className="stat-value">
                    {data.stats.verified_doctors} / {data.stats.total_doctors}
                  </div>
                </div>
                <div className="stat-icon" style={{ background: '#dbeafe', color: '#1d4ed8' }}>
                  <Stethoscope size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Pending Doctor Approvals</div>
                  <div className="stat-value">{data.stats.pending_doctor_approvals}</div>
                </div>
                <div className="stat-icon" style={{ background: '#fef3c7', color: '#b45309' }}>
                  <ShieldAlert size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">AI Predictions</div>
                  <div className="stat-value">{data.stats.total_predictions}</div>
                </div>
                <div className="stat-icon" style={{ background: '#e0e7ff', color: '#4338ca' }}>
                  <Activity size={20} />
                </div>
              </div>
            </div>

            <div className="grid-3" style={{ marginBottom: '1.5rem' }}>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Total Consultations</div>
                  <div className="stat-value">{data.stats.total_consultations}</div>
                </div>
                <div className="stat-icon" style={{ background: '#ede9fe', color: '#6d28d9' }}>
                  <CalendarCheck size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Active Conversations</div>
                  <div className="stat-value">{data.stats.total_active_conversations}</div>
                </div>
                <div className="stat-icon" style={{ background: '#f0f9ff', color: '#0284c7' }}>
                  <MessageSquare size={20} />
                </div>
              </div>
              <div className="stat-card">
                <div>
                  <div className="stat-label">Total Messages Sent</div>
                  <div className="stat-value">{data.stats.total_messages}</div>
                </div>
                <div className="stat-icon" style={{ background: '#d1fae5', color: '#059669' }}>
                  <MessageSquare size={20} />
                </div>
              </div>
            </div>

            <div className="grid-2">
              <div className="card">
                <h3 style={{ marginBottom: '1rem' }}>Disease Classification Distribution</h3>
                {Object.entries(data.charts.disease_distribution || {}).map(([label, count]) => (
                  <div key={label} className="chart-bar-row">
                    <span>{label}</span>
                    <div className="chart-track">
                      <div
                        className="chart-fill"
                        style={{
                          width: `${(count / diseaseTotal) * 100}%`,
                          background: DISEASE_COLORS[label] || '#4338ca',
                        }}
                      />
                    </div>
                    <span className="mono" style={{ textAlign: 'right' }}>{count}</span>
                  </div>
                ))}
              </div>

              <div className="card">
                <h3 style={{ marginBottom: '1rem' }}>Consultation Status Breakdown</h3>
                {Object.entries(data.charts.consultation_status || {}).map(([label, count]) => (
                  <div key={label} className="chart-bar-row">
                    <span style={{ textTransform: 'capitalize' }}>{label}</span>
                    <div className="chart-track">
                      <div
                        className="chart-fill"
                        style={{
                          width: `${(count / consultTotal) * 100}%`,
                          background: '#4338ca',
                        }}
                      />
                    </div>
                    <span className="mono" style={{ textAlign: 'right' }}>{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )
      )}
    </AdminLayout>
  );
}
