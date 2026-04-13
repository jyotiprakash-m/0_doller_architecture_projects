/**
 * Dashboard component — KPIs, recent activity, and overview
 */
async function renderDashboard(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1>Dashboard</h1>
            <p>Your legal document audit overview — all data processed locally</p>
        </div>

        <div class="kpi-grid" id="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-icon blue">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                </div>
                <div class="kpi-content">
                    <h3>Documents</h3>
                    <div class="kpi-value" id="kpi-docs">0</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                </div>
                <div class="kpi-content">
                    <h3>Audits Completed</h3>
                    <div class="kpi-value" id="kpi-audits">0</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon red">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <div class="kpi-content">
                    <h3>High Risk Findings</h3>
                    <div class="kpi-value" id="kpi-risks">0</div>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-icon amber">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                </div>
                <div class="kpi-content">
                    <h3>Avg Compliance</h3>
                    <div class="kpi-value" id="kpi-compliance">0%</div>
                </div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 24px;">
            <!-- Column 1: Documents -->
            <div class="card">
                <div class="section-header" style="margin-top:0;">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                        Recent Documents
                    </h2>
                    <a href="#upload" class="btn btn-primary btn-sm">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        Upload
                    </a>
                </div>
                <div id="recent-docs-content">
                    <div class="loading-overlay"><div class="spinner"></div><p>Refreshing dashboard...</p></div>
                </div>
            </div>

            <!-- Column 2: Risk Distribution -->
            <div class="card">
                <div class="section-header" style="margin-top:0;">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.21 15.89A10 10 0 118 2.83M22 12A10 10 0 0012 2v10z"/></svg>
                        Risk Profile
                    </h2>
                </div>
                <div id="risk-chart-content" class="risk-chart">
                    <!-- Dynamic chart content -->
                </div>
            </div>
        </div>
    `;

    // Fetch dashboard data
    try {
        const stats = await api.get('/api/dashboard');
        state.dashboardStats = stats;

        // Make sure to extract query parameters if payment=success
        const urlParams = new URLSearchParams(window.location.hash.split('?')[1] || "");
        if (urlParams.get('payment') === 'success') {
            // Give webhook a second to process, then refresh credits
            setTimeout(async () => {
                const userData = await api.get('/api/auth/me');
                state.user.credits = userData.credits;
                updateSidebarAuthInfo();
                window.history.replaceState(null, null, ' '); // Clean URL
                alert("Payment successful! Your credits have been replenished.");
            }, 1500);
        }

        document.getElementById('kpi-docs').textContent = stats.total_documents;
        document.getElementById('kpi-audits').textContent = stats.total_audits;
        document.getElementById('kpi-risks').textContent = stats.high_risk_findings;
        document.getElementById('kpi-compliance').textContent =
            stats.total_audits > 0 ? Math.round(stats.avg_compliance_score) + '%' : '—';

        // Render Risk Chart
        renderRiskChart(stats);

        const recentContent = document.getElementById('recent-docs-content');
        if (stats.recent_documents && stats.recent_documents.length > 0) {
            recentContent.innerHTML = `
                <table class="doc-table">
                    <thead>
                        <tr>
                            <th>Document</th>
                            <th>Status</th>
                            <th>Uploaded</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${stats.recent_documents.map(doc => `
                            <tr>
                                <td>
                                    <div class="doc-name">
                                        <div class="doc-icon">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                        </div>
                                        <div>
                                            <div class="doc-filename">${doc.filename}</div>
                                            <div class="doc-meta">${formatFileSize(doc.file_size)}</div>
                                        </div>
                                    </div>
                                </td>
                                <td>${getStatusBadge(doc.status)}</td>
                                <td>${formatDate(doc.uploaded_at)}</td>
                                <td>
                                    <div class="actions">
                                        ${doc.status === 'audited' ? `
                                            <a href="#audit/${doc.id}" class="btn btn-secondary btn-sm">
                                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                                Report
                                            </a>
                                        ` : `
                                            <button class="btn btn-primary btn-sm" onclick="runAudit('${doc.id}', '${doc.filename.replace(/'/g, "\\'")}')">
                                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                                                Audit
                                            </button>
                                        `}
                                        <button class="btn btn-secondary btn-sm" onclick="openChatDrawer('${doc.id}', '${doc.filename.replace(/'/g, "\\'")}')" title="Chat with Document">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        } else {
            recentContent.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <h3>No documents yet</h3>
                    <p>Upload your first legal document to get started.</p>
                </div>
            `;
        }
    } catch (e) {
        document.getElementById('recent-docs-content').innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                <h3>Connection Error</h3>
                <p>Ensure the FastAPI server is running locally.</p>
            </div>
        `;
    }
}

function renderRiskChart(stats) {
    const container = document.getElementById('risk-chart-content');
    if (!stats.recent_audits || stats.recent_audits.length === 0) {
        container.innerHTML = '<p class="text-muted" style="font-size: 0.9rem; text-align: center; padding: 20px;">No audit data for risk profiling yet.</p>';
        return;
    }

    // Count risks from recent audits
    let high = 0, med = 0, low = 0;
    stats.recent_audits.forEach(audit => {
        const findings = audit.findings || [];
        high += findings.filter(f => f.risk_level === 'high').length;
        med += findings.filter(f => f.risk_level === 'medium').length;
        low += findings.filter(f => f.risk_level === 'low').length;
    });

    const total = high + med + low || 1;
    const hPct = (high / total * 100).toFixed(1);
    const mPct = (med / total * 100).toFixed(1);
    const lPct = (low / total * 100).toFixed(1);

    container.innerHTML = `
        <div class="chart-bars">
            <div class="chart-bar-group">
                <div class="bar-label"><span>High Risk</span> <span>${high} findings</span></div>
                <div class="bar-container"><div class="bar-fill high" style="width: ${hPct}%"></div></div>
            </div>
            <div class="chart-bar-group">
                <div class="bar-label"><span>Medium Risk</span> <span>${med} findings</span></div>
                <div class="bar-container"><div class="bar-fill medium" style="width: ${mPct}%"></div></div>
            </div>
            <div class="chart-bar-group">
                <div class="bar-label"><span>Low Risk</span> <span>${low} findings</span></div>
                <div class="bar-container"><div class="bar-fill low" style="width: ${lPct}%"></div></div>
            </div>
        </div>
        <p style="margin-top: 20px; font-size: 0.75rem; color: var(--text-muted); line-height: 1.4;">
            Based on your last ${stats.recent_audits.length} document audits.
        </p>
    `;
}



