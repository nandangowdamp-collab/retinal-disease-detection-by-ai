import { useEffect, useState } from 'react';
import api, { getApiErrorMessage } from '../../services/api';
import AdminLayout from './AdminLayout';

export default function ManageConsultations() {
  const [consultations, setConsultations] = useState([]);
  const [status, setStatus] = useState('all');
  const [error, setError] = useState('');

  const loadData = async () => {
    try {
      const { data } = await api.get('/admin/consultations', { params: { status } });
      setConsultations(data.consultations || []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  return (
    <AdminLayout>
      <div className="page-header">
        <div>
          <h1>Consultation Monitoring</h1>
          <p>Track consultation requests, doctor assignments, and resolution status.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="filter-bar">
        <select className="form-select" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="all">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="completed">Completed</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Patient</th>
              <th>Doctor</th>
              <th>Reason</th>
              <th>Status</th>
              <th>Requested At</th>
            </tr>
          </thead>
          <tbody>
            {consultations.map((c) => (
              <tr key={c.id}>
                <td>{c.patient_name}</td>
                <td>{c.doctor_name}</td>
                <td>{c.consultation_reason}</td>
                <td><span className={`badge badge-${c.consultation_status}`}>{c.consultation_status}</span></td>
                <td>{new Date(c.requested_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
