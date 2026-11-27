import { useEffect, useState } from 'react';
import api, { getApiErrorMessage } from '../../services/api';
import AdminLayout from './AdminLayout';

export default function ManagePatients() {
  const [patients, setPatients] = useState([]);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const loadPatients = async (q = search) => {
    try {
      const { data } = await api.get('/admin/patients', { params: { search: q } });
      setPatients(data.patients || []);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  useEffect(() => {
    loadPatients('');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleStatus = async (patient) => {
    const nextStatus = patient.account_status === 'active' ? 'inactive' : 'active';
    try {
      await api.put(`/admin/patients/${patient.id}`, { account_status: nextStatus });
      setNotice(`Patient ${patient.full_name} set to ${nextStatus}.`);
      loadPatients();
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const inspectPatient = async (patientId) => {
    try {
      const { data } = await api.get(`/admin/patients/${patientId}`);
      setSelected(data);
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <AdminLayout>
      <div className="page-header">
        <div>
          <h1>Patient Management</h1>
          <p>Search registered patients, toggle account access, and inspect screening records.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="filter-bar">
        <input
          type="text"
          className="form-input"
          placeholder="Search name, email, phone..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <button type="button" className="btn btn-primary" onClick={() => loadPatients(search)}>
          Search
        </button>
      </div>

      {selected && (
        <div className="card" style={{ marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <h3>{selected.patient.full_name} — Records</h3>
            <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelected(null)}>
              Close
            </button>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
            {selected.patient.email} • Age: {selected.profile?.age} • Predictions: {selected.predictions.length} • Consultations: {selected.consultations.length}
          </p>
        </div>
      )}

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Contact</th>
              <th>Age / Gender</th>
              <th>Predictions</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id}>
                <td>{p.full_name}</td>
                <td>
                  <div>{p.email}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{p.phone}</div>
                </td>
                <td>{p.age} / {p.gender}</td>
                <td>{p.prediction_count}</td>
                <td><span className={`badge badge-${p.account_status}`}>{p.account_status}</span></td>
                <td>
                  <div style={{ display: 'flex', gap: '0.45rem' }}>
                    <button type="button" className="btn btn-secondary btn-sm" onClick={() => inspectPatient(p.id)}>
                      Inspect
                    </button>
                    <button
                      type="button"
                      className={`btn btn-sm ${p.account_status === 'active' ? 'btn-danger' : 'btn-primary'}`}
                      onClick={() => toggleStatus(p)}
                    >
                      {p.account_status === 'active' ? 'Deactivate' : 'Activate'}
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
