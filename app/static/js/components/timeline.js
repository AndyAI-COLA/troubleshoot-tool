/**
 * 时间线组件
 */
const Timeline = {
    render(timeline) {
        if (!timeline || !timeline.length) {
            return '<p style="color:var(--text-muted)">暂无时间线记录</p>';
        }

        const items = timeline.map(event => {
            const severity = event.severity || 'info';
            return `
                <li class="timeline-item ${severity}">
                    <span class="timeline-time">${this._esc(event.time || '')}</span>
                    <div class="timeline-content">
                        <span class="timeline-phase">${this._esc(event.phase || '')}</span>
                        <div class="timeline-action">${this._esc(event.action || '')}</div>
                        ${event.result ? `<div class="timeline-result">→ ${this._esc(event.result)}</div>` : ''}
                    </div>
                </li>
            `;
        }).join('');

        return `<ul class="timeline-list">${items}</ul>`;
    },

    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
