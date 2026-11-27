import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getApiErrorMessage } from '../services/api';
import { authService } from '../services/authService';
import '../styles/auth.css';

const initialPatient = {
  full_name: '',
  email: '',
  phone: '',
  age: '',
  gender: 'Female',
  address: '',
  password: '',
  confirm_password: '',
};

const initialDoctor = {
  full_name: '',
  email: '',
  phone: '',
  registration_number: '',
  qualification: '',
  specialization: 'Ophthalmology',
  experience: '',
  hospital_name: '',
  password: '',
  confirm_password: '',
};

export default function Register() {
  const navigate = useNavigate();
  const [role, setRole] = useState('patient');
  const [patientForm, setPatientForm] = useState(initialPatient);
  const [doctorForm, setDoctorForm] = useState(initialDoctor);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const form = role === 'patient' ? patientForm : doctorForm;
  const setField = (key, value) => {
    if (role === 'patient') {
      setPatientForm((prev) => ({ ...prev, [key]: value }));
    } else {
      setDoctorForm((prev) => ({ ...prev, [key]: value }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (form.password !== form.confirm_password) {
      setError('Password and confirm password do not match.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = { ...form, role };
      const res = await authService.register(payload);
      setSuccess(res.message || 'Registration successful! Redirecting to sign in...');
      setTimeout(() => navigate('/login'), 1300);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Registration failed. Check all fields and try again.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-wide">
        <div className="auth-header">
          <h1>Create Your Account</h1>
          <p>Register as a patient for retinal screening or as a doctor for clinical consultations.</p>
        </div>

        <div className="role-tabs role-tabs-2">
          <button
            type="button"
            className={`role-tab ${role === 'patient' ? 'active' : ''}`}
            onClick={() => {
              setRole('patient');
              setError('');
            }}
          >
            Patient Registration
          </button>
          <button
            type="button"
            className={`role-tab ${role === 'doctor' ? 'active' : ''}`}
            onClick={() => {
              setRole('doctor');
              setError('');
            }}
          >
            Doctor Registration
          </button>
        </div>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}

        {role === 'doctor' && (
          <div className="alert alert-info" style={{ fontSize: '0.84rem' }}>
            Doctor accounts require administrator verification before accessing patient records or consultations.
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="grid-2">
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className="form-input"
                required
                value={form.full_name}
                onChange={(e) => setField('full_name', e.target.value)}
                placeholder={role === 'doctor' ? 'Dr. Priya Nair' : 'Aarav Sharma'}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-input"
                required
                value={form.email}
                onChange={(e) => setField('email', e.target.value)}
                placeholder="name@example.com"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Phone Number</label>
              <input
                type="tel"
                className="form-input"
                required
                value={form.phone}
                onChange={(e) => setField('phone', e.target.value)}
                placeholder="+1 555 234 5678"
              />
            </div>

            {role === 'patient' ? (
              <>
                <div className="form-group">
                  <label className="form-label">Age</label>
                  <input
                    type="number"
                    min="1"
                    max="120"
                    className="form-input"
                    required
                    value={patientForm.age}
                    onChange={(e) => setField('age', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Gender</label>
                  <select
                    className="form-select"
                    value={patientForm.gender}
                    onChange={(e) => setField('gender', e.target.value)}
                  >
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Address</label>
                  <input
                    type="text"
                    className="form-input"
                    required
                    value={patientForm.address}
                    onChange={(e) => setField('address', e.target.value)}
                    placeholder="Street, City, State"
                  />
                </div>
              </>
            ) : (
              <>
                <div className="form-group">
                  <label className="form-label">Medical Registration Number</label>
                  <input
                    type="text"
                    className="form-input"
                    required
                    value={doctorForm.registration_number}
                    onChange={(e) => setField('registration_number', e.target.value)}
                    placeholder="MED-2026-0412"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Qualification</label>
                  <input
                    type="text"
                    className="form-input"
                    required
                    value={doctorForm.qualification}
                    onChange={(e) => setField('qualification', e.target.value)}
                    placeholder="MBBS, MS (Ophthalmology)"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Specialization</label>
                  <input
                    type="text"
                    className="form-input"
                    required
                    value={doctorForm.specialization}
                    onChange={(e) => setField('specialization', e.target.value)}
                    placeholder="Retina & Vitreous Specialist"
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Years of Experience</label>
                  <input
                    type="number"
                    min="0"
                    max="80"
                    className="form-input"
                    required
                    value={doctorForm.experience}
                    onChange={(e) => setField('experience', e.target.value)}
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Hospital / Clinic Name</label>
                  <input
                    type="text"
                    className="form-input"
                    required
                    value={doctorForm.hospital_name}
                    onChange={(e) => setField('hospital_name', e.target.value)}
                    placeholder="VisionCare Eye Institute"
                  />
                </div>
              </>
            )}

            <div className="form-group">
              <label className="form-label">Password (min 8 chars, letters + numbers)</label>
              <input
                type="password"
                className="form-input"
                required
                minLength={8}
                value={form.password}
                onChange={(e) => setField('password', e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Confirm Password</label>
              <input
                type="password"
                className="form-input"
                required
                minLength={8}
                value={form.confirm_password}
                onChange={(e) => setField('confirm_password', e.target.value)}
              />
            </div>
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={submitting}>
            {submitting ? 'Creating Account...' : `Register as ${role === 'patient' ? 'Patient' : 'Doctor'}`}
          </button>
        </form>

        <div className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </div>
      </div>
    </div>
  );
}
