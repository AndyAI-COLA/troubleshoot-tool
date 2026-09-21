/**
 * 诊断面板组件 — 排查流程页面
 */
const DiagnosisPanel = {
    currentStep: 0, // 0=问答, 1=诊断, 2=建议, 3=完成
    sessionId: null,
    scenarioKey: null,
    scenario: null,
    questions: [],
    answers: {},

    init(scenarioKey, scenario, sessionId) {
        this.currentStep = 0;
        this.sessionId = sessionId;
        this.scenarioKey = scenarioKey;
        this.scenario = scenario;
        this.questions = scenario.questions || [];
        this.answers = {};
    },

    render(container) {
        const steps = ['问答诊断', '执行检查', '解决方案', '完成'];
        const stepNames = ['问答', '诊断', '建议', '完成'];

        let stepsHtml = steps.map((name, i) => {
            let cls = i < this.currentStep ? 'done' : (i === this.currentStep ? 'active' : '');
            return `
                <div class="step-item ${cls}">
                    <div class="step-circle">${i < this.currentStep ? '✔' : (i + 1)}</div>
                    <span class="step-label">${name}</span>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <div>
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
                    <button class="btn btn-outline btn-sm" onclick="App.navigateTo('home')">← 返回</button>
                    <h2 class="page-title" style="margin:0">${this._esc(this.scenario.name)}</h2>
                </div>
                <p class="page-subtitle">${this._esc(this.scenario.description)}</p>
                <div class="steps-bar">${stepsHtml}</div>
                <div id="stepContent"></div>
            </div>
        `;

        this._renderStep();
    },

    _renderStep() {
        const el = document.getElementById('stepContent');
        if (!el) return;
        switch (this.currentStep) {
            case 0: this._renderQuestions(el); break;
            case 1: this._renderDiagnostics(el); break;
            case 2: this._renderSuggestions(el); break;
            case 3: this._renderComplete(el); break;
        }
    },

    _renderQuestions(el) {
        const q = this.questions[this._currentQIndex()];
        if (!q) {
            // 所有问题已回答
            this.currentStep = 1;
            this._renderStep();
            return;
        }

        const idx = this._currentQIndex();
        let inputHtml;
        if (q.type === 'choice' && q.options) {
            inputHtml = `<div class="form-group">
                <div style="display:flex;flex-direction:column;gap:8px">
                    ${q.options.map((opt, i) => `
                        <label style="display:flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;transition:all 0.15s"
                               class="choice-option" onmouseover="this.style.borderColor='var(--color-primary)'" onmouseout="this.style.borderColor='var(--border)'">
                            <input type="radio" name="q_${q.id}" value="${this._esc(opt)}" style="accent-color:var(--color-primary)">
                            ${this._esc(opt)}
                        </label>
                    `).join('')}
                </div>
            </div>`;
        } else {
            inputHtml = `<div class="form-group">
                <input type="text" class="form-input" id="q_input_${q.id}" placeholder="请输入..."
                       onkeydown="if(event.key==='Enter')DiagnosisPanel._submitAnswer('${q.id}')">
            </div>`;
        }

        el.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <span style="color:var(--text-muted)">问题 ${idx + 1}/${this.questions.length}</span>
                </div>
                <div class="card-body">
                    <p style="font-weight:600;margin-bottom:16px;font-size:1.05rem">${this._esc(q.text)}</p>
                    ${inputHtml}
                    <button class="btn btn-primary" onclick="DiagnosisPanel._submitAnswer('${q.id}')">
                        ${idx < this.questions.length - 1 ? '下一题 →' : '开始诊断 →'}
                    </button>
                </div>
            </div>
        `;

        // 重新激活当前步骤的样式
        this._updateStepsBar();
    },

    _currentQIndex() {
        return Object.keys(this.answers).length;
    },

    async _submitAnswer(qId) {
        const q = this.questions.find(q => q.id === qId);
        let answer;
        if (q.type === 'choice') {
            const radio = document.querySelector(`input[name="q_${qId}"]:checked`);
            if (!radio) { alert('请选择一个选项'); return; }
            answer = radio.value;
        } else {
            const input = document.getElementById(`q_input_${qId}`);
            answer = input ? input.value.trim() : '';
            if (!answer) { alert('请输入内容'); return; }
        }

        this.answers[qId] = answer;

        try {
            await API.submitAnswer(this.sessionId, qId, answer);
        } catch (e) {
            console.warn('提交答案失败（可忽略）:', e);
        }

        this._renderQuestions(document.getElementById('stepContent'));
    },

    async _renderDiagnostics(el) {
        el.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <span class="spinner"></span>
                    <span>正在执行诊断检查...</span>
                </div>
                <div class="card-body" id="diagResults"></div>
            </div>
        `;
        this._updateStepsBar();

        try {
            const result = await API.runDiagnosis(this.sessionId);
            const results = result.results || [];
            const container = document.getElementById('diagResults');

            let html = '';
            results.forEach((r, i) => {
                const cls = r.is_normal ? 'pass' : 'fail';
                const icon = r.is_normal ? '✔' : '✘';
                const output = r.output || r.error || '无输出';
                html += `
                    <div class="diagnostic-item ${cls}" style="animation: fadeIn 0.3s ease ${i * 0.1}s both">
                        <div class="diagnostic-icon">${icon}</div>
                        <div class="diagnostic-info">
                            <div class="diagnostic-name">${this._esc(r.description)}</div>
                            <div class="diagnostic-detail" style="font-family:monospace;font-size:0.8rem;color:var(--text-muted)">$ ${this._esc(r.command)}</div>
                            <div class="diagnostic-output">${this._esc(output)}</div>
                        </div>
                        <div class="diagnostic-duration">${r.duration_ms || 0}ms</div>
                    </div>
                `;
            });

            container.innerHTML = html || '<p style="color:var(--text-muted)">无诊断项</p>';

            // 自动进入下一步
            setTimeout(() => {
                this.currentStep = 2;
                this._render(document.getElementById('pageContainer'));
            }, 1500);

        } catch (e) {
            el.innerHTML = `<div class="card"><div class="card-body"><p style="color:var(--color-danger)">诊断执行失败: ${this._esc(e.message)}</p>
                <button class="btn btn-outline" onclick="DiagnosisPanel.currentStep=1;DiagnosisPanel._render(document.getElementById('pageContainer'))">重试</button>
            </div></div>`;
        }
    },

    async _renderSuggestions(el) {
        el.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <span class="spinner"></span>
                    <span>正在分析解决方案...</span>
                </div>
                <div class="card-body"></div>
            </div>
        `;
        this._updateStepsBar();

        try {
            const result = await API.getSuggestions(this.sessionId);
            const solutions = result.solutions || [];
            const body = el.querySelector('.card-body');

            if (!solutions.length) {
                body.innerHTML = `<p style="color:var(--text-muted)">暂未匹配到具体方案，请根据诊断结果手动分析。</p>`;
            } else {
                body.innerHTML = solutions.map(sol => `
                    <div class="solution-card">
                        <div class="solution-title">■ ${this._esc(sol.title)}</div>
                        <ol class="solution-steps">
                            ${sol.steps.map(s => `<li>${this._esc(s)}</li>`).join('')}
                        </ol>
                    </div>
                `).join('');
            }

            body.innerHTML += `
                <div style="margin-top:20px;display:flex;gap:8px;flex-wrap:wrap">
                    <button class="btn btn-success" onclick="DiagnosisPanel.currentStep=3;DiagnosisPanel._render(document.getElementById('pageContainer'))">导出报告 →</button>
                    <button class="btn btn-outline" onclick="App.navigateTo('home')">返回首页</button>
                </div>
            `;
        } catch (e) {
            el.innerHTML = `<div class="card"><div class="card-body"><p style="color:var(--color-danger)">获取方案失败: ${this._esc(e.message)}</p></div></div>`;
        }
    },

    _renderComplete(el) {
        this._updateStepsBar();
        el.innerHTML = `
            <div class="card">
                <div class="card-body" style="text-align:center;padding:40px">
                    <div style="font-size:3rem;margin-bottom:12px">✅</div>
                    <h3 style="margin-bottom:8px">排查完成</h3>
                    <p style="color:var(--text-secondary);margin-bottom:24px">诊断已完成，你可以导出报告或返回首页</p>
                    <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap">
                        <button class="btn btn-primary" onclick="DiagnosisPanel._exportReport()">📄 导出故障报告</button>
                        <button class="btn btn-outline" onclick="App.navigateTo('home')">🏠 返回首页</button>
                        <button class="btn btn-outline" onclick="App.navigateTo('history')">📋 查看历史</button>
                    </div>
                    <div id="exportResult" style="margin-top:16px"></div>
                </div>
            </div>
        `;
    },

    async _exportReport() {
        const notesEl = document.getElementById('exportResult');
        try {
            const result = await API.exportReport(this.sessionId);
            notesEl.innerHTML = `
                <div class="badge badge-success" style="font-size:0.9rem">✔ 报告已导出</div>
                <p style="margin-top:8px;font-size:0.85rem;color:var(--text-secondary)">报告 ID: ${result.uuid}</p>
            `;
        } catch (e) {
            notesEl.innerHTML = `<p style="color:var(--color-danger)">导出失败: ${e.message}</p>`;
        }
    },

    _updateStepsBar() {
        const steps = document.querySelectorAll('.step-item');
        steps.forEach((item, i) => {
            item.classList.remove('active', 'done');
            if (i < this.currentStep) item.classList.add('done');
            else if (i === this.currentStep) item.classList.add('active');
            const circle = item.querySelector('.step-circle');
            if (i < this.currentStep) circle.textContent = '✔';
            else circle.textContent = (i + 1);
        });
    },

    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
