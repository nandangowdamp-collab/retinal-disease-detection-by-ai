import api from './api';

export const consultationService = {
  async getAvailableDoctors(search = '') {
    const { data } = await api.get('/patient/doctors', { params: { search } });
    return data;
  },
  async requestConsultation(payload) {
    const { data } = await api.post('/consultations', payload);
    return data;
  },
  async listConsultations(status = '') {
    const { data } = await api.get('/consultations', { params: { status } });
    return data;
  },
  async updateDoctorConsultation(id, payload) {
    const { data } = await api.put(`/doctor/consultations/${id}`, payload);
    return data;
  },
  async addConsultationNotes(id, payload) {
    const { data } = await api.post(`/doctor/consultations/${id}/notes`, payload);
    return data;
  },
  async addDoctorAssessment(predictionId, payload) {
    const { data } = await api.put(`/doctor/predictions/${predictionId}/assessment`, payload);
    return data;
  },
};
