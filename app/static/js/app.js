/**
 * 主应用 — 路由、状态、页面渲染
 */
const App = {
    currentPage: 'home',
    scenarios: [],
    categories: {},
    activeFilter: 'all',

    async init() {
        Sidebar.init();
        SearchModal.init();
        await this.loadData();
        this.navigateTo('home');
    },

    async loadData() {
        try {
            const [scData, catData] = await Promise.all([
                API.getScenarios(),
                API.getCategories(),
            ]);
            this.scenarios = scData.scenarios || [];
            this.categories = catData.categories || {};
        } catch (e) {
            console.error('加载数据失败:', e);
        }
    },

    navigateTo(page) {
        this.currentPage = page;
        Sidebar.setActive(page);
        const container = document.getElementById('pageContainer');
        switch (page) {
            case 'home': this._renderHome(container); break;
            case 'knowledge': this._renderKnowledge(container); break;
            case 'history': this._renderHistory(container); break;
            case 'reports': this._renderReports(container); break;
            default: this._renderHome(container);
        }
    },

    // ── 排查首页 ──

    _renderHome(container) {
        const cats = Object.keys(this.categories);
        const filterHtml = cats.map(cat => {
            const info = this.categories[cat];
            const icon = info.icon || '•';
            return `<button class="filter-btn ${this.activeFilter === cat ? 'active' : ''}"
                            onclick="App.setFilter('${this._esc(cat)}')">${icon} ${this._esc(cat)}</button>`;
        }).join('');

        container.innerHTML = `
            <h1 class="page-title">故障排查</h1>
            <p class="page-subtitle">选择故障场景开始交互式排查，或使用顶部搜索快速定位</p>
            <div class="category-filters">
                <button class="filter-btn ${this.activeFilter === 'all' ? 'active' : ''}"
                        onclick="App.setFilter('all')">全部</button>
                ${filterHtml}
            </div>
            <div id="scenarioGrid"></div>
        `;

        this._renderFilteredGrid();
    },

    setFilter(cat) {
        this.activeFilter = cat;
        this._renderHome(document.getElementById('pageContainer'));
    },

    _renderFilteredGrid() {
        const grid = document.getElementById('scenarioGrid');
        if (!grid) return;
        let filtered = this.scenarios;
        if (this.activeFilter !== 'all') {
            filtered = filtered.filter(s => s.category === this.activeFilter);
        }
        ScenarioCard.renderGrid(filtered, grid);
    },

    // ── 开始诊断 ──

    async startDiagnosis(scenarioKey) {
        const container = document.getElementById('pageContainer');
        container.innerHTML = `<div style="text-align:center;padding:40px"><span class="spinner"></span><p style="margin-top:12px;color:var(--text-secondary)">正在初始化诊断...</p></div>`;

        try {
            const result = await API.startDiagnosis(scenarioKey);
            const scenario = await API.getScenario(scenarioKey);
            DiagnosisPanel.init(scenarioKey, scenario, result.session_id);
            DiagnosisPanel.render(container);
        } catch (e) {
            container.innerHTML = `
                <div class="card"><div class="card-body">
                    <p style="color:var(--color-danger)">启动诊断失败: ${this._esc(e.message)}</p>
                    <button class="btn btn-outline" style="margin-top:12px" onclick="App.navigateTo('home')">返回首页</button>
                </div></div>`;
        }
    },

    // ── 知识库管理页 ──

    _renderKnowledge(container) {
        const rows = this.scenarios.map(s => `
            <tr>
                <td style="font-weight:600">${this._esc(s.name)}</td>
                <td><span class="tag tag-category">${this._esc(s.category)}</span></td>
                <td>${s.question_count || 0}</td>
                <td>${s.diagnostic_count || 0}</td>
                <td>${s.solution_count || 0}</td>
                <td>${s.is_custom ? '<span class="badge badge-info">自定义</span>' : '<span class="badge badge-success">内置</span>'}</td>
                <td>
                    ${s.is_custom ? `<button class="btn btn-outline btn-sm" onclick="App.deleteScenario('${this._esc(s.key)}')">删除</button>` : ''}
                </td>
            </tr>
        `).join('');

        container.innerHTML = `
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
                <div>
                    <h1 class="page-title">知识库管理</h1>
                    <p class="page-subtitle" style="margin:0">共 ${this.scenarios.length} 个场景（${this.scenarios.filter(s => !s.is_custom).length} 内置 + ${this.scenarios.filter(s => s.is_custom).length} 自定义）</p>
                </div>
                <button class="btn btn-primary" onclick="App.showCreateScenario()">+ 新建场景</button>
            </div>
            <div class="card">
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>场景名称</th>
                                <th>分类</th>
                                <th>问题数</th>
                                <th>检查项</th>
                                <th>方案数</th>
                                <th>类型</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody>${rows}</tbody>
                    </table>
                </div>
            </div>
            <div id="scenarioForm"></div>
        `;
    },

    showCreateScenario() {
        const formEl = document.getElementById('scenarioForm');
        if (!formEl) return;

        const catOptions = Object.keys(this.categories).map(c =>
            `<option value="${this._esc(c)}">${this._esc(c)}</option>`
        ).join('');

        formEl.innerHTML = `
            <div class="modal-overlay show">
                <div class="modal">
                    <h3 style="margin-bottom:16px">新建自定义场景</h3>
                    <div class="form-group">
                        <label class="form-label">场景名称 *</label>
                        <input class="form-input" id="cs_name" placeholder="如：Redis 连接异常">
                    </div>
                    <div class="form-group">
                        <label class="form-label">分类</label>
                        <select class="form-select" id="cs_category">
                            ${catOptions}
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">描述</label>
                        <input class="form-input" id="cs_desc" placeholder="简要描述故障现象">
                    </div>
                    <div class="form-group">
                        <label class="form-label">常见症状（每行一条）</label>
                        <textarea class="form-textarea" id="cs_symptoms" placeholder="连接超时&#10;日志报错..."></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">解决方案标题</label>
                        <input class="form-input" id="cs_sol_title" placeholder="如：检查 Redis 服务状态">
                    </div>
                    <div class="form-group">
                        <label class="form-label">解决步骤（每行一条）</label>
                        <textarea class="form-textarea" id="cs_sol_steps" placeholder="检查 Redis 进程&#10;查看日志&#10;重启服务"></textarea>
                    </div>
                    <div style="display:flex;gap:8px;margin-top:16px">
                        <button class="btn btn-primary" onclick="App._submitNewScenario()">保存场景</button>
                        <button class="btn btn-outline" onclick="document.getElementById('scenarioForm').innerHTML=''">取消</button>
                    </div>
                </div>
            </div>
        `;
    },

    async _submitNewScenario() {
        const name = document.getElementById('cs_name').value.trim();
        if (!name) { alert('请输入场景名称'); return; }

        const symptoms = document.getElementById('cs_symptoms').value.split('\n').map(s => s.trim()).filter(Boolean);
        const solTitle = document.getElementById('cs_sol_title').value.trim();
        const solSteps = document.getElementById('cs_sol_steps').value.split('\n').map(s => s.trim()).filter(Boolean);

        const data = {
            name,
            category: document.getElementById('cs_category').value,
            description: document.getElementById('cs_desc').value.trim() || name,
            symptoms: symptoms.length ? symptoms : [name],
            questions: [{ id: 'q1', text: '请描述具体错误信息或现象：', type: 'text' }],
            diagnostics: [],
            solutions: solTitle ? [{ title: solTitle, condition: '默认', steps: solSteps.length ? solSteps : ['请补充解决步骤'] }] : [],
        };

        try {
            await API.createScenario(data);
            document.getElementById('scenarioForm').innerHTML = '';
            await this.loadData();
            this._renderKnowledge(document.getElementById('pageContainer'));
        } catch (e) {
            alert('创建失败: ' + e.message);
        }
    },

    async deleteScenario(key) {
        if (!confirm('确认删除此场景？')) return;
        try {
            await API.deleteScenario(key);
            await this.loadData();
            this._renderKnowledge(document.getElementById('pageContainer'));
        } catch (e) {
            alert('删除失败: ' + e.message);
        }
    },

    // ── 历史记录页 ──

    async _renderHistory(container) {
        container.innerHTML = `<div style="text-align:center;padding:40px"><span class="spinner"></span><p style="margin-top:12px;color:var(--text-secondary)">加载中...</p></div>`;

        try {
            const result = await API.listHistory();
            const history = result.history || [];

            if (!history.length) {
                container.innerHTML = `
                    <h1 class="page-title">历史记录</h1>
                    <div class="empty-state">
                        <div class="empty-state-icon">📋</div>
                        <div class="empty-state-text">暂无排障记录</div>
                    </div>`;
                return;
            }

            const rows = history.map(h => {
                const statusMap = {
                    'completed': '<span class="badge badge-success">已完成</span>',
                    'diagnosed': '<span class="badge badge-info">已诊断</span>',
                    'in_progress': '<span class="badge badge-warning">进行中</span>',
                };
                const status = statusMap[h.status] || `<span class="badge">${this._esc(h.status)}</span>`;
                const created = h.created_at ? new Date(h.created_at).toLocaleString('zh-CN') : '-';
                return `
                    <tr style="cursor:pointer" onclick="App.showHistoryDetail('${this._esc(h.id)}')">
                        <td style="font-weight:600">${this._esc(h.scenario_name || '未知')}</td>
                        <td>${status}</td>
                        <td>${created}</td>
                    </tr>
                `;
            }).join('');

            container.innerHTML = `
                <h1 class="page-title">历史记录</h1>
                <p class="page-subtitle">共 ${history.length} 条记录</p>
                <div class="card">
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr><th>故障场景</th><th>状态</th><th>时间</th></tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </div>
                <div id="historyDetail"></div>
            `;
        } catch (e) {
            container.innerHTML = `<p style="color:var(--color-danger)">加载失败: ${e.message}</p>`;
        }
    },

    async showHistoryDetail(id) {
        const el = document.getElementById('historyDetail');
        if (!el) return;
        try {
            const detail = await API.getHistoryDetail(id);
            const timeline = detail.timeline || [];
            el.innerHTML = `
                <div class="card" style="margin-top:16px">
                    <div class="card-header">📋 ${this._esc(detail.scenario_name || '排障记录')}</div>
                    <div class="card-body">
                        ${Timeline.render(timeline)}
                    </div>
                </div>
            `;
        } catch (e) {
            el.innerHTML = `<p style="color:var(--color-danger)">加载详情失败</p>`;
        }
    },

    // ── 报告页 ──

    async _renderReports(container) {
        container.innerHTML = `<div style="text-align:center;padding:40px"><span class="spinner"></span><p style="margin-top:12px;color:var(--text-secondary)">加载中...</p></div>`;

        try {
            const result = await API.listReports();
            const reports = result.reports || [];

            if (!reports.length) {
                container.innerHTML = `
                    <h1 class="page-title">故障报告</h1>
                    <div class="empty-state">
                        <div class="empty-state-icon">📄</div>
                        <div class="empty-state-text">暂无导出的报告</div>
                    </div>`;
                return;
            }

            const rows = reports.map(r => {
                const date = r.exported_at ? new Date(r.exported_at).toLocaleString('zh-CN') : '-';
                return `
                    <tr style="cursor:pointer" onclick="App.showReport('${this._esc(r.uuid)}')">
                        <td style="font-weight:600">${this._esc(r.scenario_name || '未知')}</td>
                        <td>${date}</td>
                        <td>
                            <a href="/api/reports/${this._esc(r.uuid)}/download" class="btn btn-outline btn-sm" onclick="event.stopPropagation()">下载</a>
                        </td>
                    </tr>
                `;
            }).join('');

            container.innerHTML = `
                <h1 class="page-title">故障报告</h1>
                <p class="page-subtitle">共 ${reports.length} 份报告</p>
                <div class="card">
                    <div class="table-wrapper">
                        <table>
                            <thead>
                                <tr><th>故障场景</th><th>导出时间</th><th>操作</th></tr>
                            </thead>
                            <tbody>${rows}</tbody>
                        </table>
                    </div>
                </div>
                <div id="reportDetail"></div>
            `;
        } catch (e) {
            container.innerHTML = `<p style="color:var(--color-danger)">加载失败: ${e.message}</p>`;
        }
    },

    async showReport(uuid) {
        const el = document.getElementById('reportDetail');
        if (!el) return;
        try {
            const report = await API.getReport(uuid);
            el.innerHTML = `
                <div class="card" style="margin-top:16px">
                    <div class="card-header">
                        📄 ${this._esc(report.scenario_name || '报告')}
                        <a href="/api/reports/${this._esc(uuid)}/download" class="btn btn-outline btn-sm" style="margin-left:auto">下载 .md</a>
                    </div>
                    <div class="card-body report-content">
                        ${this._renderMarkdown(report.content || '')}
                    </div>
                </div>
            `;
        } catch (e) {
            el.innerHTML = `<p style="color:var(--color-danger)">加载报告失败</p>`;
        }
    },

    // ── 简易 Markdown 渲染 ──

    _renderMarkdown(md) {
        let html = this._esc(md);
        // 表格
        html = html.replace(/^(\|.+\|)\n(\|[-| :]+\|)\n((?:\|.+\|\n?)*)/gm, (_, header, sep, body) => {
            const ths = header.split('|').filter(c => c.trim()).map(c => `<th>${c.trim()}</th>`).join('');
            const rows = body.trim().split('\n').map(row => {
                const tds = row.split('|').filter(c => c.trim()).map(c => `<td>${c.trim()}</td>`).join('');
                return `<tr>${tds}</tr>`;
            }).join('');
            return `<table><thead><tr>${ths}</tr></thead><tbody>${rows}</tbody></table>`;
        });
        // 代码块
        html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        // 行内代码
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // 标题
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
        // 粗体
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        // 水平线
        html = html.replace(/^---$/gm, '<hr>');
        // 列表
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`);
        // 换行
        html = html.replace(/\n/g, '<br>');
        return html;
    },

    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};

// ── 启动 ──
document.addEventListener('DOMContentLoaded', () => App.init());
