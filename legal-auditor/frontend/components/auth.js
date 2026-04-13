/**
 * Auth Component — Handles Login and Signup
 */
async function renderLogin(container) {
    container.innerHTML = `
        <div class="auth-wrapper">
            <div class="auth-card glass-panel">
                <div class="auth-header">
                    <div class="brand-icon" style="margin: 0 auto 1.5rem;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                        </svg>
                    </div>
                    <h2>Welcome to LegalShield</h2>
                    <p>Secure local-first legal document analysis</p>
                </div>

                <div class="auth-tabs">
                    <button class="auth-tab active" id="tab-login" onclick="switchAuthTab('login')">Login</button>
                    <button class="auth-tab" id="tab-register" onclick="switchAuthTab('register')">Register</button>
                </div>

                <form id="auth-form" onsubmit="handleAuthSubmit(event)">
                    <div class="form-group">
                        <label>Email Address</label>
                        <input type="email" id="auth-email" required placeholder="name@company.com">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" id="auth-password" required placeholder="••••••••">
                    </div>
                    <div id="register-fields" style="display: none;">
                        <div class="form-group">
                            <label>Confirm Password</label>
                            <input type="password" id="auth-confirm-password" placeholder="••••••••">
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary" id="auth-submit-btn" style="width: 100%; margin-top: 1rem;">
                        Login to Dashboard
                    </button>
                </form>

                <div class="auth-footer">
                    <p class="privacy-note">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        All data is encrypted and processing remains regional.
                    </p>
                </div>
            </div>
        </div>
    `;
}

let authMode = 'login';

function switchAuthTab(mode) {
    authMode = mode;
    document.getElementById('tab-login').classList.toggle('active', mode === 'login');
    document.getElementById('tab-register').classList.toggle('active', mode === 'register');
    document.getElementById('register-fields').style.display = mode === 'register' ? 'block' : 'none';
    document.getElementById('auth-submit-btn').textContent = mode === 'login' ? 'Login to Dashboard' : 'Create Account';
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('auth-email').value;
    const password = document.getElementById('auth-password').value;

    if (authMode === 'register') {
        const confirm = document.getElementById('auth-confirm-password').value;
        if (password !== confirm) {
            showToast('Passwords do not match', 'error');
            return;
        }

        try {
            await api.post('/api/auth/register', { email, password });
            showToast('Account created! Please login.', 'success');
            switchAuthTab('login');
        } catch (err) {
            showToast(err.message || 'Registration failed', 'error');
        }
    } else {
        try {
            // OAuth2PasswordRequestForm expects x-www-form-urlencoded or multipart/form-data
            const formData = new FormData();
            formData.append('username', email);
            formData.append('password', password);

            const res = await fetch(`${API_BASE}/api/auth/login`, {
                method: 'POST',
                body: formData
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error.detail || 'Login failed');
            }

            const data = await res.json();
            
            // Store auth state
            localStorage.setItem('ls_token', data.access_token);
            localStorage.setItem('ls_user_id', data.user_id);
            state.user = { id: data.user_id, credits: data.credits };
            
            showToast('Logged in successfully', 'success');
            window.location.hash = '#dashboard';
            
            // Refresh sidebar/header logic if needed
            updateSidebarAuthInfo();
        } catch (err) {
            showToast(err.message || 'Login failed', 'error');
        }
    }
}

function updateSidebarAuthInfo() {
    const sidebarFooter = document.querySelector('.sidebar-footer');
    if (sidebarFooter && state.user) {
        sidebarFooter.innerHTML = `
            <div class="user-profile-badge">
                <div class="user-avatar">${state.user.id.slice(0, 2).toUpperCase()}</div>
                <div class="user-info">
                    <span class="user-id">${state.user.id}</span>
                    <span class="user-credits">${Number.isInteger(state.user.credits) ? state.user.credits : Number(state.user.credits).toFixed(1)} Credits</span>
                </div>
            </div>
            <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
                <a href="#pricing" class="btn btn-primary btn-sm" style="flex: 2; text-align: center;">Buy Credits</a>
                <button class="btn btn-secondary btn-sm" onclick="handleLogout()" style="flex: 1; display: flex; align-items: center; justify-content: center; gap: 4px; padding: 0 0.75rem;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                    Logout
                </button>
            </div>
        `;
    }
}

function handleLogout() {
    localStorage.removeItem('ls_token');
    localStorage.removeItem('ls_user_id');
    state.user = null;
    showToast('Logged out', 'info');
    window.location.hash = '#login';
}
