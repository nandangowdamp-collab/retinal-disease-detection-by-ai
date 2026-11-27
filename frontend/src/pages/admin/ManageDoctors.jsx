import { useEffect, useState } from 'react';
import api, { getApiErrorMessage } from '../../services/api';
import AdminLayout from './AdminLayout';

export default function ManageDoctors() {
  const [doctors, setDoctors] = useState([]);
  const [filter, setFilter] = useState('all');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadDoctors = async () => {
    try {
      const { data } = await api.get('/admin/doctors', { params: { verification_status: filter } });
      setDoctors(data.doctors || []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadDoctors();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const handleVerify = async (doctorId, status) => {
    let rejection_reason = '';
    if (status === 'rejected') {
      rejection_reason = window.prompt('Reason for rejecting doctor verification:') || '';
      if (!rejection_reason.trim()) return;
    }
    try {
      await api.put(`/admin/doctors/${doctorId}/verify`, {
        verification_status: status,
        rejection_reason,
      });
      setNotice(`Doctor verification status updated to ${status}.`);
      loadDoctors();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const toggleAccount = async (doc) => {
    const nextStatus = doc.account_status === 'active' ? 'inactive' : 'active';
    try {
      await api.put(`/admin/doctors/${doc.id}`, { account_status: nextStatus });
      setNotice(`Doctor account ${nextStatus}.`);
      loadDoctors();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <AdminLayout>
      <div className="page-header">
        <div>
          <h1>Doctor Management &amp; Verification</h1>
          <p>Approve or reject registered clinicians and verify medical registration numbers.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="filter-bar">
        <select className="form-select" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All Verification Statuses</option>
          <option value="pending">Pending Approval</option>
          <option value="verified">Verified</option>
          <option value="rejected">Rejected</option>
        </select>
      </div>

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Doctor</th>
              <th>Reg. Number</th>
              <th>Qualification &amp; Hospital</th>
              <th>Verification</th>
              <th>Account</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {doctors.map((d) => (
              <tr key={d.id}>
                <td>
                  <div style={{ fontWeight: 600 }}>{d.full_name}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{d.email}</div>
                </td>
                <td className="mono">{d.registration_number}</td>
                <td>
                  <div>{d.qualification} — {d.specialization}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{d.hospital_name} ({d.experience} yrs)</div>
                </td>
                <td><span className={`badge badge-${d.verification_status}`}>{d.verification_status}</span></td>
                <td><span className={`badge badge-${d.account_status}`}>{d.account_status}</span></td>
                <td>
                  <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                    {d.verification_status !== 'verified' && (
                      <button type="button" className="btn btn-primary btn-sm" onClick={() => handleVerify(d.id, 'verified')}>
                        Approve
                      </button>
                    )}
                    {d.verification_status !== 'rejected' && (
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => handleVerify(d.id, 'rejected')}>
                        Reject
                      </button>
                    )}
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => toggleAccount(d)}>
                      {d.account_status === 'active' ? 'Deactivate' : 'Activate'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
