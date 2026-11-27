import api from './api';

export const authService = {
  async register(payload) {
    const { data } = await api.post('/auth/register', payload);
    return data;
  },
  async login(payload) {
    const { data } = await api.post('/auth/login', payload);
    return data;
  },
  async logout() {
    const { data } = await api.post('/auth/logout');
    return data;
  },
  async getProfile() {
    const { data } = await api.get('/auth/profile');
    return data;
  },
  async updateProfile(payload) {
    const { data } = await api.put('/auth/profile', payload);
    return data;
  },
  async changePassword(payload) {
    const { data } = await api.put('/auth/change-password', payload);
    return data;
  },
  async checkHealth() {
    const { data } = await api.get('/health');
    return data;
  },
};
