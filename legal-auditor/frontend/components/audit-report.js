/**
 * Audit Report component — Detailed audit view with findings, clauses, and compliance
 */
async function renderAuditReport(container, params = {}) {
    const docId = params.id;
    if (!docId) {
        container.innerHTML = `
            <div class="empty-state">
                <h3>No document selected</h3>
                <p>Select a document from the Documents page to view its audit report.</p>
                <a href="#documents" class="btn btn-primary">Go to Documents</a>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="loading-overlay">
            <div class="spinner"></div>
            <p>Loading audit report...</p>
        </div>
    `;

    try {
        const report = await api.get(`/api/audit/${docId}/report`);
        renderAuditContent(container, report);
    } catch (e) {
        container.innerHTML = `
            <div class="page-header">
                <h1>Audit Report</h1>
                <p>No audit report found for this document.</p>
            </div>
            <div class="card">
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                    <h3>No audit report available</h3>
                    <p>Run an AI audit on this document first.</p>
                    <button class="btn btn-primary" onclick="runAudit('${docId}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        Run AI Audit
                    </button>
                </div>
            </div>
        `;
    }
}

function renderAuditContent(container, report) {
    const findings = report.findings || [];
    const keyClauses = report.key_clauses || [];
    const riskLevel = (report.overall_risk_score || 'low').toLowerCase();
    const complianceScore = report.compliance_score || 0;

    // Compliance ring SVG
    const circumference = 2 * Math.PI * 33;
    const dashoffset = circumference - (complianceScore / 100) * circumference;
    const ringColor = complianceScore >= 80 ? 'var(--color-success)' : complianceScore >= 60 ? 'var(--color-warning)' : 'var(--color-danger)';

    // Group findings
    const highRisks = findings.filter(f => f.risk_level === 'high');
    const medRisks = findings.filter(f => f.risk_level === 'medium');
    const lowRisks = findings.filter(f => f.risk_level === 'low');

    container.innerHTML = `
        <div class="page-header">
            <div class="audit-header">
                <div>
                    <h1>Audit Report</h1>
                    <p style="color: var(--text-secondary); margin-top: 4px;">${report.document_name || 'Document'}</p>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <button class="btn btn-secondary btn-sm" onclick="downloadReport('${report.document_id}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                        Download PDF
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="copySummary('${report.executive_summary.replace(/'/g, "\\'")}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M16 4h2a2 2 0 012 2v14a2 2 0 01-2 2H6a2 2 0 01-2-2V6a2 2 0 012-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
                        Copy Summary
                    </button>
                    <button class="btn btn-primary btn-sm" onclick="openChatDrawer('${report.document_id}', '${(report.document_name || 'Document').replace(/'/g, "\\'")}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                        Chat with Document
                    </button>
                    <div class="risk-score-badge ${riskLevel}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        ${report.overall_risk_score} Risk Profile
                    </div>
                </div>
            </div>
        </div>

        <div class="kpi-grid">
            <div class="kpi-card" style="animation-delay: 0.1s">
                <div class="kpi-icon red">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                </div>
                <div class="kpi-content">
                    <h3>High Risk</h3>
                    <div class="kpi-value">${report.high_risk_count || 0}</div>
                </div>
            </div>
            <div class="kpi-card" style="animation-delay: 0.2s">
                <div class="kpi-icon amber">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                </div>
                <div class="kpi-content">
                    <h3>Medium Risk</h3>
                    <div class="kpi-value">${report.medium_risk_count || 0}</div>
                </div>
            </div>
            <div class="kpi-card" style="animation-delay: 0.3s">
                <div class="kpi-icon green">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                </div>
                <div class="kpi-content">
                    <h3>Low Risk</h3>
                    <div class="kpi-value">${report.low_risk_count || 0}</div>
                </div>
            </div>
            <div class="kpi-card" style="animation-delay: 0.4s">
                <div class="compliance-ring">
                    <svg width="80" height="80" viewBox="0 0 80 80">
                        <circle class="ring-bg" cx="40" cy="40" r="33"/>
                        <circle class="ring-fill" cx="40" cy="40" r="33"
                            stroke="${ringColor}"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${dashoffset}"/>
                    </svg>
                    <span class="compliance-value">${Math.round(complianceScore)}%</span>
                </div>
                <div class="kpi-content">
                    <h3>Compliance</h3>
                </div>
            </div>
        </div>

        <div class="audit-content-grid">
            <!-- Main Content: Findings -->
            <div style="display: flex; flex-direction: column; gap: 24px;">
                <div class="card" style="animation-delay: 0.5s">
                    <div class="section-header" style="margin-top:0;">
                        <h2>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                            Executive Summary
                        </h2>
                    </div>
                    <p style="font-size: 0.95rem; line-height: 1.7; color: var(--text-primary);">${report.executive_summary || 'No summary available.'}</p>
                </div>

                <div class="section-header" style="margin-top: 12px;">
                    <h2>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/></svg>
                        Critical Findings (${findings.length})
                    </h2>
                </div>
                <div class="findings-grid">
                    ${findings.length > 0 ? findings.sort((a,b) => {
                        const rank = {high: 0, medium: 1, low: 2};
                        return rank[a.risk_level] - rank[b.risk_level];
                    }).map((f, i) => `
                        <div class="finding-card ${f.risk_level || 'medium'}" style="animation-delay: ${0.6 + (i * 0.1)}s">
                            <div class="finding-header">
                                <span class="finding-title">${f.title || 'Finding'}</span>
                                ${getRiskBadge(f.risk_level || 'medium')}
                            </div>
                            <p class="finding-desc">${f.description || ''}</p>
                            ${f.clause_text ? `
                                <div class="finding-clause-wrapper">
                                    <div class="clause-label">Referenced Text:</div>
                                    <div class="finding-clause">"${f.clause_text}"</div>
                                </div>
                            ` : ''}
                            ${f.recommendation ? `
                                <div class="finding-recommendation">
                                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>
                                    <span>${f.recommendation}</span>
                                </div>
                            ` : ''}
                        </div>
                    `).join('') : '<p class="text-muted">No findings identified.</p>'}
                </div>
            </div>

            <!-- Sidebar Content: Key Clauses -->
            <div style="display: flex; flex-direction: column; gap: 24px;">
                <div class="card" style="animation-delay: 0.7s">
                    <div class="section-header" style="margin-top:0;">
                        <h2>
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                            Key Clauses
                        </h2>
                    </div>
                    <div class="report-clauses-sidebar">
                        ${keyClauses.length > 0 ? keyClauses.map(c => `
                            <div class="sidebar-clause-item">
                                <div class="sidebar-clause-header">
                                    <span class="clause-type-tag">${c.clause_type || 'General'}</span>
                                    ${c.importance === 'critical' ? '<span class="importance-dot red"></span>' : 
                                      c.importance === 'important' ? '<span class="importance-dot amber"></span>' : ''}
                                </div>
                                <div class="sidebar-clause-title">${c.title || 'Untitled Clause'}</div>
                                <div class="sidebar-clause-summary">${c.summary || 'No summary provided.'}</div>
                                ${c.clause_text && !['none', 'null', 'n/a'].includes(c.clause_text.toString().toLowerCase().trim()) ? `
                                    <div class="finding-clause-wrapper" style="margin-top: 12px;">
                                        <div class="clause-label" style="font-size: 0.7rem; margin-bottom: 2px;">Extract:</div>
                                        <div class="finding-clause" style="font-size: 0.75rem; padding: 8px;">"${c.clause_text}"</div>
                                    </div>
                                ` : ''}
                            </div>
                        `).join('') : '<p class="text-muted">No key clauses identified.</p>'}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function copySummary(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Summary copied to clipboard!', 'success');
    }).catch(err => {
        showToast('Failed to copy summary.', 'error');
    });
}

async function downloadReport(docId) {
    try {
        const response = await fetch(`${API_BASE}/api/audit/${docId}/download`);
        if (!response.ok) throw new Error('Download failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Audit_Report_${docId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showToast('PDF report downloaded successfully', 'success');
    } catch (err) {
        console.error('Download error:', err);
        showToast('Failed to download PDF report', 'error');
    }
}
