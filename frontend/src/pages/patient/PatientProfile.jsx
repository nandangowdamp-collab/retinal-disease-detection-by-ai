import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api, { getApiErrorMessage } from '../../services/api';
import { authService } from '../../services/authService';
import PatientLayout from './PatientLayout';

export default function PatientProfile() {
  const { refreshProfile } = useAuth();
  const [form, setForm] = useState({ full_name: '', phone: '', age: '', gender: '', address: '' });
  const [consultations, setConsultations] = useState([]);
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api
      .get('/patient/profile')
      .then(({ data }) => {
        setForm({
          full_name: data.user?.full_name || '',
          phone: data.user?.phone || '',
          age: data.profile?.age || '',
          gender: data.profile?.gender || 'Female',
          address: data.profile?.address || '',
        });
        setConsultations(data.consultations || []);
      })
      .catch((err) => setError(getApiErrorMessage(err)));
  }, []);

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      await api.put('/patient/profile', form);
      await refreshProfile();
      setMessage('Profile updated successfully.');
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');
    setMessage('');
    try {
      const res = await authService.changePassword(pwForm);
      setMessage(res.message);
      setPwForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <PatientLayout>
      <div className="page-header">
        <div>
          <h1>My Profile &amp; Account</h1>
          <p>Update personal contact details, change your password, and review consultation history.</p>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {message && <div className="alert alert-success">{message}</div>}

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <form className="card" onSubmit={handleSaveProfile}>
          <h3 style={{ marginBottom: '1rem' }}>Personal Information</h3>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input className="form-input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">Phone Number</label>
            <input className="form-input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Age</label>
              <input type="number" className="form-input" value={form.age} onChange={(e) => setForm({ ...form, age: e.target.value })} required />
            </div>
            <div className="form-group">
              <label className="form-label">Gender</label>
              <select className="form-select" value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })}>
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Address</label>
            <input className="form-input" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required />
          </div>
          <button type="submit" className="btn btn-primary">Save Profile</button>
        </form>

        <form className="card" onSubmit={handleChangePassword}>
          <h3 style={{ marginBottom: '1rem' }}>Change Password</h3>
          <div className="form-group">
            <label className="form-label">Current Password</label>
            <input type="password" className="form-input" value={pwForm.current_password} onChange={(e) => setPwForm({ ...pwForm, current_password: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">New Password</label>
            <input type="password" className="form-input" value={pwForm.new_password} onChange={(e) => setPwForm({ ...pwForm, new_password: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">Confirm New Password</label>
            <input type="password" className="form-input" value={pwForm.confirm_password} onChange={(e) => setPwForm({ ...pwForm, confirm_password: e.target.value })} required />
          </div>
          <button type="submit" className="btn btn-secondary">Update Password</button>
        </form>
      </div>

      <div className="card">
        <h3 style={{ marginBottom: '1rem' }}>Consultation History</h3>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Doctor</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Doctor Notes</th>
              </tr>
            </thead>
            <tbody>
              {consultations.length === 0 ? (
                <tr>
                  <td colSpan="4" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No consultations yet.</td>
                </tr>
              ) : (
                consultations.map((c) => (
                  <tr key={c.id}>
                    <td>{c.doctor_name}</td>
                    <td>{c.consultation_reason}</td>
                    <td><span className={`badge badge-${c.consultation_status}`}>{c.consultation_status}</span></td>
                    <td>{c.consultation_notes || c.rejection_reason || '—'}</td>
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
