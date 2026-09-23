
import api from '../../../utils/api';

const BASE = '/api/assistant';
const ADMIN_BASE = '/api/assistant/admin';

const getStatus = () => api.get(`${BASE}/status`);

const getSuggestions = () => api.get(`${BASE}/suggestions`);

/**
 * Send a chat message.
 * @param {string} message - User's message
 * @param {number|null} conversationId - Existing conversation ID, or null for new
 */
const sendMessage = (message, conversationId = null) => {
    const payload = { message };
    if (conversationId) payload.conversation_id = conversationId;
    return api.post(`${BASE}/chat`, payload);
};

const listConversations = () => api.get(`${BASE}/conversations`);

const getMessages = (conversationId) =>
    api.get(`${BASE}/conversations/${conversationId}/messages`);

const archiveConversation = (conversationId) =>
    api.delete(`${BASE}/conversations/${conversationId}`);

const renameConversation = (conversationId, title) =>
    api.patch(`${BASE}/conversations/${conversationId}`, { title });


// ADMIN ENDPOINTS

const admin = {
    getConfig: () => api.get(`${ADMIN_BASE}/config`),

    getConfigByCategory: (category) =>
        api.get(`${ADMIN_BASE}/config/${category}`),

    /**
     * Update a single config value.
     * @param {string} key - Config key (e.g., "LLM_API_KEY")
     * @param {any} value - New value
     */
    updateConfig: (key, value) =>
        api.put(`${ADMIN_BASE}/config/${key}`, { value }),

    bulkUpdateConfigs: (updates) =>
        api.post(`${ADMIN_BASE}/config/bulk`, { updates }),

    /**
     * Test LLM connection.
     * @param {object} opts - Optional { api_key, model } to test without saving
     */
    testConnection: (opts = {}) =>
        api.post(`${ADMIN_BASE}/test-connection`, opts),

    getModels: () => api.get(`${ADMIN_BASE}/models`),

    getProviders: () => api.get(`${ADMIN_BASE}/providers`),

    getModelsForProvider: (provider, { live = true, refresh = false } = {}) => {
    const params = new URLSearchParams();
    if (live) params.set('live', 'true');
    if (refresh) params.set('refresh', 'true');
    const query = params.toString();
    return api.get(`${ADMIN_BASE}/models/${provider}${query ? `?${query}` : ''}`);
},

    switchProvider: (data) =>
        api.post(`${ADMIN_BASE}/switch-provider`, data),

    clearCache: () => api.post(`${ADMIN_BASE}/cache/clear`),
};

export const assistantAPI = {
    getStatus,
    getSuggestions,
    sendMessage,
    listConversations,
    getMessages,
    archiveConversation,
    renameConversation,
    admin,
};

export default assistantAPI;