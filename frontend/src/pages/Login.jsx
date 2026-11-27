import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { getApiErrorMessage } from '../services/api';
import '../styles/auth.css';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [portalRole, setPortalRole] = useState('patient');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const data = await login({ email, password, expected_role: portalRole });
      const role = data.user?.role || portalRole;
      navigate(`/${role}/dashboard`);
    } catch (err) {
      setError(getApiErrorMessage(err, 'Invalid credentials.'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <h1>Portal Sign In</h1>
          <p>Select your portal role and sign in with your credentials.</p>
        </div>

        <div className="role-tabs">
          {['patient', 'doctor', 'admin'].map((r) => (
            <button
              key={r}
              type="button"
              className={`role-tab ${portalRole === r ? 'active' : ''}`}
              onClick={() => {
                setPortalRole(r);
                setError('');
              }}
              style={{ textTransform: 'capitalize' }}
            >
              {r} Portal
            </button>
          ))}
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {portalRole === 'admin' && (
          <div className="alert alert-info" style={{ fontSize: '0.83rem' }}>
            Administrator accounts are provisioned via the secure server setup script (`create_admin.py`).
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label" htmlFor="login-email">
              Email Address
            </label>
            <input
              id="login-email"
              type="email"
              className="form-input"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@example.com"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="login-password">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              className="form-input"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={submitting}>
            {submitting ? 'Signing in...' : `Sign In to ${portalRole.charAt(0).toUpperCase() + portalRole.slice(1)} Portal`}
          </button>
        </form>

        {portalRole !== 'admin' && (
          <div className="auth-footer">
            Need a patient or doctor account? <Link to="/register">Register here</Link>
          </div>
        )}
      </div>
    </div>
  );
}
