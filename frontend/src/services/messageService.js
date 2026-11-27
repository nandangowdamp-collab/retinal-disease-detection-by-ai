import api from './api';

export const messageService = {
  async listConversations() {
    const { data } = await api.get('/messages/conversations');
    return data;
  },
  async startConversation(targetUserId, role) {
    const payload = role === 'patient' ? { doctor_id: targetUserId } : { patient_id: targetUserId };
    const { data } = await api.post('/messages/conversations', payload);
    return data;
  },
  async getMessages(conversationId) {
    const { data } = await api.get(`/messages/${conversationId}`);
    return data;
  },
  async sendMessage(payload) {
    const { data } = await api.post('/messages', payload);
    return data;
  },
  async markConversationRead(conversationId) {
    const { data } = await api.put(`/messages/conversations/${conversationId}/read`);
    return data;
  },
  async reportConversation(conversationId, reason) {
    const { data } = await api.post(`/messages/conversations/${conversationId}/report`, { reason });
    return data;
  },
};
