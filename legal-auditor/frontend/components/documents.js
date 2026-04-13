/**
 * Documents component — Document library with list/table view
 */
async function renderDocuments(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1>Documents</h1>
            <p>Your uploaded legal documents — securely stored locally</p>
        </div>

        <div class="card">
            <div class="section-header" style="margin-top:0;">
                <h2>All Documents</h2>
                <a href="#upload" class="btn btn-primary btn-sm">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                    Upload New
                </a>
            </div>
            <div id="documents-list">
                <div class="loading-overlay"><div class="spinner"></div><p>Loading documents...</p></div>
            </div>
        </div>
    `;

    try {
        const data = await api.get('/api/documents');
        const docs = data.documents || [];
        const listEl = document.getElementById('documents-list');

        if (docs.length === 0) {
            listEl.innerHTML = `
                <div class="empty-state">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <h3>No documents uploaded</h3>
                    <p>Upload your first legal document to begin AI-powered analysis.</p>
                    <a href="#upload" class="btn btn-primary">Upload Document</a>
                </div>
            `;
            return;
        }

        listEl.innerHTML = `
            <table class="doc-table">
                <thead>
                    <tr>
                        <th>Document</th>
                        <th>Status</th>
                        <th>Type</th>
                        <th>Pages</th>
                        <th>Chunks</th>
                        <th>Uploaded</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${docs.map(doc => `
                        <tr id="doc-row-${doc.id}">
                            <td>
                                <div class="doc-name">
                                    <div class="doc-icon">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                    </div>
                                    <div style="min-width: 0;">
                                        <div class="doc-filename">${doc.filename}</div>
                                        <div class="doc-meta">${formatFileSize(doc.file_size)}</div>
                                    </div>
                                </div>
                            </td>
                            <td>${getStatusBadge(doc.status)}</td>
                            <td><span class="badge badge-neutral">${doc.file_type.replace('.', '').toUpperCase()}</span></td>
                            <td>${doc.page_count || '—'}</td>
                            <td>${doc.chunk_count || 0}</td>
                            <td>${formatDate(doc.uploaded_at)}</td>
                            <td>
                                <div class="actions">
                                    <button class="btn btn-primary btn-sm" onclick="runAudit('${doc.id}', '${doc.filename.replace(/'/g, "\\'")}')" title="Run AI Audit">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                                        Audit
                                    </button>
                                    <button class="btn btn-secondary btn-sm" onclick="openChatDrawer('${doc.id}', '${doc.filename.replace(/'/g, "\\'")}')" title="Chat with Document">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                                        Chat
                                    </button>
                                    ${doc.status === 'audited' ? `
                                        <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#audit/${doc.id}'" title="View Report">
                                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                                            Report
                                        </button>
                                    ` : ''}
                                    <button class="btn btn-danger btn-sm" onclick="deleteDocument('${doc.id}')" title="Delete">
                                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        state.documents = docs;

    } catch (e) {
        document.getElementById('documents-list').innerHTML = `
            <div class="empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>
                <h3>Could not load documents</h3>
                <p>Make sure the backend server is running.</p>
            </div>
        `;
    }
}

async function deleteDocument(docId) {
    if (!confirm('Are you sure you want to delete this document? This cannot be undone.')) return;

    try {
        await api.delete(`/api/documents/${docId}`);
        showToast('Document deleted successfully.', 'success');
        const row = document.getElementById(`doc-row-${docId}`);
        if (row) row.remove();
    } catch (e) {
        showToast('Failed to delete document.', 'error');
    }
}
