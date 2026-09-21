/**
 * 侧边栏组件
 */
const Sidebar = {
    init() {
        const toggle = document.getElementById('menuToggle');
        const sidebar = document.getElementById('sidebar');
        if (toggle) {
            toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
        }
        // 点击导航项
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.setActive(page);
                sidebar.classList.remove('open');
                App.navigateTo(page);
            });
        });
    },

    setActive(page) {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });
    },
};
