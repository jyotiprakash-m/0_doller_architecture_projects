/**
 * LegalShield AI — Main Application
 * SPA Router, State Management, API Client
 */

const API_BASE = 'http://localhost:8000';

// --- State ---
const state = {
    user: null,
    currentPage: 'dashboard',
    documents: [],
    dashboardStats: null,
    currentAudit: null,
    drawer: {
        active: false,
        docId: null,
        filename: null
    },
    chatMessages: [],
    isLoading: false,
};

// --- API Client ---
const api = {
    async get(endpoint) {
        const token = localStorage.getItem('ls_token');
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (res.status === 401) return handleLogout();
            if (!res.ok) throw new Error(await res.text());
            return await res.json();
        } catch (e) {
            console.error(`GET ${endpoint} failed:`, e);
            throw e;
        }
    },

    async post(endpoint, data) {
        const token = localStorage.getItem('ls_token');
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(data),
            });
            if (res.status === 401) return handleLogout();
            if (!res.ok) throw new Error(await res.text());
            return await res.json();
        } catch (e) {
            console.error(`POST ${endpoint} failed:`, e);
            throw e;
        }
    },

    async upload(endpoint, file) {
        const token = localStorage.getItem('ls_token');
        const formData = new FormData();
        formData.append('file', file);
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` },
                body: formData,
            });
            if (res.status === 401) return handleLogout();
            if (!res.ok) throw new Error(await res.text());
            return await res.json();
        } catch (e) {
            console.error(`UPLOAD ${endpoint} failed:`, e);
            throw e;
        }
    },

    async delete(endpoint) {
        try {
            const res = await fetch(`${API_BASE}${endpoint}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(await res.text());
            return await res.json();
        } catch (e) {
            console.error(`DELETE ${endpoint} failed:`, e);
            throw e;
        }
    },
};

// --- Toast Notifications ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-message">${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
}

// --- Utility ---
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

function formatDate(isoString) {
    if (!isoString) return '—';
    const d = new Date(isoString);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function getStatusBadge(status) {
    const map = {
        uploaded: '<span class="badge badge-info">Uploaded</span>',
        processing: '<span class="badge badge-warning">Processing</span>',
        indexed: '<span class="badge badge-success">Indexed</span>',
        audited: '<span class="badge badge-success">Audited</span>',
        error: '<span class="badge badge-danger">Error</span>',
    };
    return map[status] || `<span class="badge badge-neutral">${status}</span>`;
}

function getRiskBadge(level) {
    const map = {
        high: '<span class="badge badge-danger">High Risk</span>',
        medium: '<span class="badge badge-warning">Medium Risk</span>',
        low: '<span class="badge badge-success">Low Risk</span>',
        info: '<span class="badge badge-info">Info</span>',
    };
    return map[level] || '<span class="badge badge-neutral">Unknown</span>';
}

// --- Router ---
function navigate(page, params = {}) {
    const token = localStorage.getItem('ls_token');
    
    // Auth Guard
    if (!token && page !== 'login') {
        window.location.hash = '#login';
        return;
    }

    if (token && page === 'login') {
        window.location.hash = '#dashboard';
        return;
    }

    state.currentPage = page;

    // Toggle sidebar visibility
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    
    if (page === 'login' || page === 'register') {
        if (sidebar) sidebar.style.display = 'none';
        if (mainContent) mainContent.style.marginLeft = '0';
    } else {
        if (sidebar) sidebar.style.display = '';
        if (mainContent) mainContent.style.marginLeft = '';
    }

    // Update nav active states
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    // Update document title for SEO and UX
    const titles = {
        'dashboard': 'Dashboard | LegalShield AI',
        'upload': 'Upload | LegalShield AI',
        'documents': 'Documents | LegalShield AI',
        'audit': 'Audit Report | LegalShield AI',
        'chat': 'AI Chat | LegalShield AI'
    };
    document.title = titles[page] || 'LegalShield AI';

    // Render page with transition
    const container = document.getElementById('page-content');
    
    // Smooth transition
    container.style.opacity = '0';
    
    setTimeout(() => {
        container.innerHTML = '';
        container.style.opacity = '1';

        switch (page) {
            case 'login':
                renderLogin(container);
                break;
            case 'pricing':
                renderPricing(container);
                break;
            case 'dashboard':
                renderDashboard(container);
                break;
            case 'upload':
                renderUpload(container);
                break;
            case 'documents':
                renderDocuments(container);
                break;
            case 'audit':
                renderAuditReport(container, params);
                break;
            case 'chat':
                renderChat(container);
                break;
            default:
                renderDashboard(container);
        }
    }, 50);
}


// --- Hash Router ---
function handleHashChange() {
    const hash = window.location.hash.slice(1) || 'dashboard';
    const [page, ...paramParts] = hash.split('/');
    const params = {};
    if (paramParts.length) params.id = paramParts[0];
    navigate(page, params);
}

// --- Init ---
window.addEventListener('hashchange', handleHashChange);
window.addEventListener('DOMContentLoaded', async () => {
    // Session restore
    const token = localStorage.getItem('ls_token');
    const userId = localStorage.getItem('ls_user_id');
    if (token && userId) {
        state.user = { id: userId, credits: 0 };
        try {
            const data = await api.get('/api/auth/me');
            state.user = { id: data.id, credits: data.credits };
            updateSidebarAuthInfo();
        } catch (e) {
            handleLogout();
        }
    }
    handleHashChange();
});

// --- Global Actions ---
async function runAudit(docId, filename = 'Document') {
    const container = document.getElementById('page-content');

    // --- Switch to Audit Progress View ---
    container.innerHTML = `
        <div class="audit-progress-container">
            <div class="scanner-container">
                <div class="scanner-circle"></div>
                <div class="scanner-shield">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <div class="scanner-line"></div>
            </div>
            
            <div class="progress-status">
                <h2 id="progress-title">Auditing Document</h2>
                <p id="progress-subtitle">${filename}</p>
            </div>

            <div class="work-log" id="work-log">
                <div class="log-item active">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                    Initializing local RAG context...
                </div>
            </div>
        </div>
    `;

    const logs = [
        "Connecting to local Ollama instance...",
        "Partitioning document into semantic chunks...",
        "Generating nomic-embed-text vectors...",
        "Analyzing liability and indemnification clauses...",
        "Evaluating termination and force majeure risks...",
        "Identifying missing protective clauses...",
        "Calculating overall compliance score...",
        "Mistral LLM is finalizing executive summary...",
        "Optimizing local ChromaDB indices...",
    ];

    let logIndex = 0;
    const logContainer = document.getElementById('work-log');
    const progressTitle = document.getElementById('progress-title');

    const logInterval = setInterval(() => {
        if (logIndex < logs.length) {
            const lastLog = logContainer.querySelector('.log-item.active');
            if (lastLog) lastLog.classList.remove('active');

            const item = document.createElement('div');
            item.className = 'log-item active';
            item.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                ${logs[logIndex]}
            `;
            logContainer.prepend(item);
            logIndex++;

            if (logIndex > 5) progressTitle.textContent = "AI Analysis Deep Dive...";
            if (logIndex > 8) progressTitle.textContent = "Finalizing Audit Report...";
        }
    }, 4500);

    try {
        const result = await api.post(`/api/audit/${docId}`, {});
        clearInterval(logInterval);
        state.currentAudit = result;
        
        // Ensure credits remain synced with backend
        try {
            if (state.user) {
                const userData = await api.get('/api/auth/me');
                state.user.credits = userData.credits;
                if (typeof updateSidebarAuthInfo === 'function') updateSidebarAuthInfo();
            }
        } catch(e) {
            console.error("Failed to sync credits", e);
        }

        showToast('Audit completed successfully!', 'success');
        
        // Wait a beat for the user to see the "success" state
        setTimeout(() => {
            window.location.hash = `#audit/${docId}`;
        }, 800);
    } catch (e) {
        clearInterval(logInterval);
        
        // Parse the error message if it's JSON from FastAPI
        let errorMsg = e.message;
        try {
            const parsed = JSON.parse(e.message);
            if (parsed.detail) errorMsg = parsed.detail;
        } catch(err) {
            // keep default e.message if not JSON
        }
        
        showToast(errorMsg || 'Audit failed. Ensure Ollama is running.', 'error');
        navigate('dashboard'); // Re-render to restore state
    }
}

// --- Chat Drawer Global Functions ---
function openChatDrawer(docId, filename) {
    state.drawer.active = true;
    state.drawer.docId = docId;
    state.drawer.filename = filename;

    const overlay = document.getElementById('chat-drawer-overlay');
    const drawer = document.getElementById('chat-drawer');
    const content = document.getElementById('chat-drawer-content');

    // Setup the basic UI template inside the drawer
    content.innerHTML = `
        <div class="chat-drawer-header">
            <div style="min-width: 0;">
                <div class="chat-drawer-title">Chat: ${filename}</div>
                <div style="font-size: 0.8rem; color: var(--text-muted);">AI Context bound to this document</div>
            </div>
            <button class="drawer-close-btn" onclick="closeChatDrawer()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
        </div>
        
        <div class="chat-messages" id="drawer-chat-messages">
            <div class="chat-welcome">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                </svg>
                <h3>Document Analysis Mode</h3>
                <p>Ask anything about this document. Queries deduct 0.1 standard credits.</p>
            </div>
        </div>

        <div class="chat-input-area">
            <textarea
                class="chat-input"
                id="drawer-chat-input"
                placeholder="Ask about this document..."
                rows="1"
                onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault();sendDrawerMessage()}"
            ></textarea>
            <button class="btn btn-primary" id="drawer-chat-send-btn" onclick="sendDrawerMessage()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
        </div>
    `;

    // Make the UI visible with CSS animations
    if (overlay) overlay.classList.add('active');
    if (drawer) drawer.classList.add('active');

    // Auto-resize textarea setup
    const textarea = document.getElementById('drawer-chat-input');
    if (textarea) {
        textarea.addEventListener('input', () => {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
        });
        setTimeout(() => textarea.focus(), 300); // Focus after animation completes
    }
}

function closeChatDrawer() {
    state.drawer.active = false;
    state.drawer.docId = null;
    
    const overlay = document.getElementById('chat-drawer-overlay');
    const drawer = document.getElementById('chat-drawer');
    
    if (overlay) overlay.classList.remove('active');
    if (drawer) drawer.classList.remove('active');
}


