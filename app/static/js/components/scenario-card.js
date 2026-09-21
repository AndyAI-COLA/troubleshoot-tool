/**
 * 场景卡片组件
 */
const ScenarioCard = {
    render(scenario) {
        const symptomsHtml = (scenario.symptoms || []).slice(0, 3).map(s =>
            `<span class="tag tag-symptom">${this._esc(s)}</span>`
        ).join('');

        const customTag = scenario.is_custom ? '<span class="tag tag-custom">自定义</span>' : '';

        return `
            <div class="scenario-card" data-key="${this._esc(scenario.key)}" onclick="App.startDiagnosis('${this._esc(scenario.key)}')">
                <div class="scenario-card-title">
                    ${this._esc(scenario.name)}
                    ${customTag}
                </div>
                <div class="scenario-card-desc">${this._esc(scenario.description)}</div>
                <div class="scenario-card-meta">
                    <span class="tag tag-category">${this._esc(scenario.category)}</span>
                    ${symptomsHtml}
                </div>
            </div>
        `;
    },

    renderGrid(scenarios, container) {
        if (!scenarios.length) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <div class="empty-state-text">暂无匹配的故障场景</div>
                </div>
            `;
            return;
        }
        container.innerHTML = `<div class="scenario-grid">${scenarios.map(s => this.render(s)).join('')}</div>`;
    },

    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
