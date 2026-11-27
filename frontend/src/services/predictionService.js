import api from './api';

export const predictionService = {
  async uploadImage(file) {
    const formData = new FormData();
    formData.append('image', file);
    const { data } = await api.post('/prediction/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
  async classifyImage(fileOrUploadId) {
    if (typeof fileOrUploadId === 'string') {
      const { data } = await api.post('/prediction/classify', { upload_id: fileOrUploadId });
      return data;
    }
    const formData = new FormData();
    formData.append('image', fileOrUploadId);
    const { data } = await api.post('/prediction/classify', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },
  async getHistory(params = {}) {
    const { data } = await api.get('/prediction/history', { params });
    return data;
  },
  async getPrediction(id) {
    const { data } = await api.get(`/prediction/${id}`);
    return data;
  },
  async fetchProtectedImageUrl(id) {
    const response = await api.get(`/prediction/${id}/image`, { responseType: 'blob' });
    return URL.createObjectURL(response.data);
  },
  async downloadReportPdf(id, filename = 'retinal-report.pdf') {
    const response = await api.get(`/prediction/${id}/report`, { responseType: 'blob' });
    const url = URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  },
};
