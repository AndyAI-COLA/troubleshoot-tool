/**
 * API 调用封装
 */
const API = {
    base: '/api',

    async _get(path) {
        const res = await fetch(this.base + path);
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `请求失败 (${res.status})`);
        }
        return res.json();
    },

    async _post(path, body = {}) {
        const res = await fetch(this.base + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `请求失败 (${res.status})`);
        }
        return res.json();
    },

    async _put(path, body = {}) {
        const res = await fetch(this.base + path, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `请求失败 (${res.status})`);
        }
        return res.json();
    },

    async _delete(path) {
        const res = await fetch(this.base + path, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `请求失败 (${res.status})`);
        }
        return res.json();
    },

    // ── 场景 ──
    async getScenarios() { return this._get('/scenarios'); },
    async getScenario(key) { return this._get(`/scenarios/${key}`); },
    async getCategories() { return this._get('/scenarios/categories'); },
    async createScenario(data) { return this._post('/scenarios', data); },
    async updateScenario(key, data) { return this._put(`/scenarios/${key}`, data); },
    async deleteScenario(key) { return this._delete(`/scenarios/${key}`); },

    // ── 搜索 ──
    async search(keyword) { return this._get(`/search?keyword=${encodeURIComponent(keyword)}`); },

    // ── 诊断 ──
    async startDiagnosis(scenarioId) { return this._post('/diagnosis/start', { scenario_id: scenarioId }); },
    async submitAnswer(sessionId, questionId, answer) {
        return this._post(`/diagnosis/${sessionId}/answer`, { question_id: questionId, answer });
    },
    async runDiagnosis(sessionId) { return this._post(`/diagnosis/${sessionId}/run`); },
    async getSuggestions(sessionId) { return this._post(`/diagnosis/${sessionId}/suggest`); },
    async getSession(sessionId) { return this._get(`/diagnosis/${sessionId}`); },

    // ── 报告 ──
    async listReports() { return this._get('/reports'); },
    async getReport(uuid) { return this._get(`/reports/${uuid}`); },
    async exportReport(sessionId, notes = '') {
        return this._post('/reports/export', { session_id: sessionId, notes });
    },

    // ── 历史 ──
    async listHistory() { return this._get('/history'); },
    async getHistoryDetail(id) { return this._get(`/history/${id}`); },
};
