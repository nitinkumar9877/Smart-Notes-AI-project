/**
 * AI Smart Notes - Main JavaScript
 * Handles: Theme, Auth, Sidebar, Global utilities
 */

// ─── Theme Management ──────────────────────────────────────────────────────
function getTheme() {
    return localStorage.getItem('theme') || 'light';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    document.querySelectorAll('.theme-icon').forEach(el => {
        el.textContent = theme === 'dark' ? '☀️' : '🌙';
    });
}

function toggleTheme() {
    const current = getTheme();
    const next = current === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', next);
    applyTheme(next);
}

// Apply on load
applyTheme(getTheme());

// ─── Logout ────────────────────────────────────────────────────────────────
async function handleLogout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
    } catch (e) {}
    window.location.href = '/';
}

// ─── Sidebar Toggle (Mobile) ───────────────────────────────────────────────
function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.toggle('open');
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
    const sidebar = document.querySelector('.sidebar');
    const toggle = document.querySelector('.mobile-nav-toggle');
    if (sidebar && sidebar.classList.contains('open') &&
        !sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove('open');
    }
});

// ─── HTML Escape ───────────────────────────────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// ─── Keyboard Shortcuts ────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
    // Escape to close modals
    if (e.key === 'Escape') {
        const modal = document.getElementById('note-modal');
        const chatbot = document.getElementById('chatbot-panel');
        if (modal && !modal.classList.contains('hidden')) {
            modal.classList.add('hidden');
            document.body.style.overflow = '';
        }
        if (chatbot && !chatbot.classList.contains('hidden')) {
            chatbot.classList.add('hidden');
        }
    }
});

// ─── Smooth scroll for anchors ─────────────────────────────────────────────
document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
        const target = document.querySelector(a.getAttribute('href'));
        if (target) { e.preventDefault(); target.scrollIntoView({ behavior: 'smooth' }); }
    });
});

// ─── Toast Notifications ───────────────────────────────────────────────────
function showToast(message, type = 'info') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%) translateY(80px);
        background: ${type === 'success' ? '#06d6a0' : type === 'error' ? '#ef233c' : '#4361ee'};
        color: white; padding: 12px 24px; border-radius: 100px;
        font-family: var(--font-main, 'Sora', sans-serif); font-size: 14px; font-weight: 600;
        z-index: 999; box-shadow: 0 8px 30px rgba(0,0,0,0.2);
        transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
    `;
    document.body.appendChild(toast);
    requestAnimationFrame(() => { toast.style.transform = 'translateX(-50%) translateY(0)'; });
    setTimeout(() => {
        toast.style.transform = 'translateX(-50%) translateY(80px)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

console.log('%c🧠 AI Smart Notes', 'font-size: 18px; font-weight: bold; color: #4361ee;');
console.log('%cB.Tech Final Year Project | SDG 4 – Quality Education', 'font-size: 12px; color: #6b7280;');
