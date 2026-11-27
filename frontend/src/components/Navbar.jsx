import { Link, useNavigate } from 'react-router-dom';
import { Eye, LogOut, ShieldCheck, Stethoscope, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const dashboardPath = user ? `/${user.role}/dashboard` : '/';

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <Link to="/" className="brand">
          <span className="brand-mark">
            <Eye size={20} />
          </span>
          <span>RetinaAI Screening</span>
        </Link>

        <nav className="nav-links">
          {!isAuthenticated ? (
            <>
              <Link to="/" className="nav-link">
                Overview
              </Link>
              <Link to="/login" className="nav-link">
                Sign In
              </Link>
              <Link to="/register" className="btn btn-primary btn-sm">
                Create Account
              </Link>
            </>
          ) : (
            <>
              <Link to={dashboardPath} className="nav-link" style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem' }}>
                {user.role === 'doctor' ? (
                  <Stethoscope size={16} />
                ) : user.role === 'admin' ? (
                  <ShieldCheck size={16} />
                ) : (
                  <User size={16} />
                )}
                <span>{user.full_name}</span>
                <span className="badge badge-normal" style={{ textTransform: 'uppercase' }}>
                  {user.role}
                </span>
              </Link>
              <button type="button" className="btn btn-secondary btn-sm" onClick={handleLogout}>
                <LogOut size={15} />
                Logout
              </button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
