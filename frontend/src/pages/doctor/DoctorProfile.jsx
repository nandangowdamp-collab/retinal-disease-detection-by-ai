import { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import api, { getApiErrorMessage } from '../../services/api';
import { authService } from '../../services/authService';
import DoctorLayout from './DoctorLayout';

export default function DoctorProfile() {
  const { refreshProfile } = useAuth();
  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    qualification: '',
    specialization: '',
    experience: '',
    hospital_name: '',
    availability: '',
  });
  const [verificationStatus, setVerificationStatus] = useState('pending');
  const [regNumber, setRegNumber] = useState('');
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    api
      .get('/doctor/profile')
      .then(({ data }) => {
        setForm({
          full_name: data.user?.full_name || '',
          phone: data.user?.phone || '',
          qualification: data.profile?.qualification || '',
          specialization: data.profile?.specialization || '',
          experience: data.profile?.experience ?? '',
          hospital_name: data.profile?.hospital_name || '',
          availability: data.profile?.availability || '',
        });
        setVerificationStatus(data.profile?.verification_status || 'pending');
        setRegNumber(data.profile?.registration_number || '');
      })
      .catch((err) => setError(getApiErrorMessage(err)));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setError('');
    setNotice('');
    try {
      await api.put('/doctor/profile', form);
      await refreshProfile();
      setNotice('Doctor profile updated.');
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setError('');
    setNotice('');
    try {
      const res = await authService.changePassword(pwForm);
      setNotice(res.message);
      setPwForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      setError(getApiErrorMessage(err));
    }
  };

  return (
    <DoctorLayout>
      <div className="page-header">
        <div>
          <h1>Doctor Profile</h1>
          <p>Registration No: <span className="mono">{regNumber}</span></p>
        </div>
        <span className={`badge badge-${verificationStatus}`}>Status: {verificationStatus}</span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {notice && <div className="alert alert-success">{notice}</div>}

      <div className="grid-2">
        <form className="card" onSubmit={handleSave}>
          <h3 style={{ marginBottom: '1rem' }}>Professional Details</h3>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input className="form-input" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">Phone</label>
            <input className="form-input" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">Qualification</label>
            <input className="form-input" value={form.qualification} onChange={(e) => setForm({ ...form, qualification: e.target.value })} required />
          </div>
          <div className="form-group">
            <label className="form-label">Specialization</label>
            <input className="form-input" value={form.specialization} onChange={(e) => setForm({ ...form, specialization: e.target.value })} required />
          </div>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Years of Experience</label>
              <input type="number" className="form-input" value={form.experience} onChange={(e) => setForm({ ...form, experience: e.target.value })} required />
            </div>
            <div className="form-group">
              <label className="form-label">Hospital / Clinic</label>
              <input className="form-input" value={form.hospital_name} onChange={(e) => setForm({ ...form, hospital_name: e.target.value })} required />
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Availability Schedule</label>
            <input className="form-input" value={form.availability} onChange={(e) => setForm({ ...form, availability: e.target.value })} />
          </div>
          <button type="submit" className="btn btn-primary">Save Changes</button>
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
    </DoctorLayout>
  );
}
