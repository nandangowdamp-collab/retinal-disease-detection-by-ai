import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { authService } from '../services/authService';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const saved = localStorage.getItem('retinal_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });
  const [profile, setProfile] = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem('retinal_token'));
  const [loading, setLoading] = useState(Boolean(localStorage.getItem('retinal_token')));

  const refreshProfile = useCallback(async () => {
    const activeToken = localStorage.getItem('retinal_token');
    if (!activeToken) {
      setLoading(false);
      return null;
    }
    try {
      const data = await authService.getProfile();
      setUser(data.user);
      setProfile(data.profile || null);
      localStorage.setItem('retinal_user', JSON.stringify(data.user));
      return data;
    } catch {
      localStorage.removeItem('retinal_token');
      localStorage.removeItem('retinal_user');
      setToken(null);
      setUser(null);
      setProfile(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (token) {
      refreshProfile();
    } else {
      setLoading(false);
    }
  }, [token, refreshProfile]);

  const login = async (credentials) => {
    const data = await authService.login(credentials);
    localStorage.setItem('retinal_token', data.access_token);
    localStorage.setItem('retinal_user', JSON.stringify(data.user));
    setToken(data.access_token);
    setUser(data.user);
    setProfile(data.profile || null);
    return data;
  };

  const logout = async () => {
    try {
      if (localStorage.getItem('retinal_token')) {
        await authService.logout();
      }
    } catch {
      // Clear local session regardless
    } finally {
      localStorage.removeItem('retinal_token');
      localStorage.removeItem('retinal_user');
      setToken(null);
      setUser(null);
      setProfile(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        token,
        loading,
        isAuthenticated: Boolean(user && token),
        login,
        logout,
        refreshProfile,
        setUser,
        setProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used inside AuthProvider');
  }
  return ctx;
}
