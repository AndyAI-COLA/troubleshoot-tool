/**
 * 搜索组件
 */
const SearchModal = {
    debounceTimer: null,

    init() {
        const input = document.getElementById('globalSearch');
        const dropdown = document.getElementById('searchDropdown');
        if (!input || !dropdown) return;

        input.addEventListener('input', () => {
            clearTimeout(this.debounceTimer);
            const keyword = input.value.trim();
            if (!keyword) {
                dropdown.classList.remove('show');
                return;
            }
            this.debounceTimer = setTimeout(() => this._doSearch(keyword), 250);
        });

        input.addEventListener('focus', () => {
            if (input.value.trim()) dropdown.classList.add('show');
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('.search-box')) {
                dropdown.classList.remove('show');
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                dropdown.classList.remove('show');
                input.blur();
            }
        });
    },

    async _doSearch(keyword) {
        const dropdown = document.getElementById('searchDropdown');
        try {
            const result = await API.search(keyword);
            if (!result.results || !result.results.length) {
                dropdown.innerHTML = '<div class="search-result-item"><span class="search-result-desc">未找到匹配的场景</span></div>';
                dropdown.classList.add('show');
                return;
            }
            dropdown.innerHTML = result.results.slice(0, 8).map(r => `
                <div class="search-result-item" onclick="SearchModal._select('${this._esc(r.key)}')">
                    <div class="search-result-name">${this._esc(r.scenario.name)}</div>
                    <div class="search-result-desc">${this._esc(r.scenario.description).substring(0, 60)}</div>
                    <div class="search-result-match">${r.matches.slice(0, 2).map(m => this._esc(m)).join(' · ')}</div>
                </div>
            `).join('');
            dropdown.classList.add('show');
        } catch (e) {
            console.error('搜索失败:', e);
        }
    },

    _select(key) {
        document.getElementById('searchDropdown').classList.remove('show');
        document.getElementById('globalSearch').value = '';
        App.startDiagnosis(key);
    },

    _esc(str) {
        const div = document.createElement('div');
        div.textContent = str || '';
        return div.innerHTML;
    },
};
