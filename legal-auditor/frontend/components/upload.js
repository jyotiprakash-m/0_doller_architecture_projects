/**
 * Upload component — Drag & drop file upload with progress animation
 */
function renderUpload(container) {
    container.innerHTML = `
        <div class="page-header">
            <h1>Upload Document</h1>
            <p>Upload legal documents for AI-powered analysis — all processing stays local</p>
        </div>

        <div class="card">
            <div class="upload-zone" id="upload-zone">
                <input type="file" id="file-input" class="file-input-hidden" accept=".pdf,.docx,.txt">
                <div class="upload-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
                        <polyline points="17 8 12 3 7 8"/>
                        <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                </div>
                <h3>Drop your legal document here</h3>
                <p>or click to browse your files</p>
                <div class="file-types">
                    <span>PDF</span>
                    <span>DOCX</span>
                    <span>TXT</span>
                </div>
            </div>

            <div class="upload-progress" id="upload-progress" style="display:none;">
                <div class="progress-bar-container">
                    <div class="progress-bar" id="progress-bar"></div>
                </div>
                <p class="progress-text" id="progress-text">Processing...</p>
            </div>
        </div>

        <div id="upload-result" style="margin-top: 24px;"></div>
    `;

    // Setup interactions
    const zone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');

    zone.addEventListener('click', () => fileInput.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

async function handleFileUpload(file) {
    const allowedExtensions = ['.pdf', '.docx', '.txt'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(ext)) {
        showToast('Unsupported file type. Use PDF, DOCX, or TXT.', 'error');
        return;
    }

    if (file.size > 50 * 1024 * 1024) {
        showToast('File too large. Maximum 50MB.', 'error');
        return;
    }

    const progressEl = document.getElementById('upload-progress');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const resultEl = document.getElementById('upload-result');

    progressEl.style.display = 'block';
    progressBar.style.width = '20%';
    progressText.textContent = `Uploading ${file.name}...`;

    try {
        progressBar.style.width = '50%';
        progressText.textContent = 'Processing and indexing document...';

        const result = await api.upload('/api/documents/upload', file);

        progressBar.style.width = '100%';
        progressText.textContent = 'Upload complete!';

        showToast(`"${file.name}" uploaded and indexed successfully!`, 'success');

        resultEl.innerHTML = `
            <div class="card" style="border-color: rgba(16, 185, 129, 0.2);">
                <div style="display: flex; align-items: center; gap: 16px; margin-bottom: 16px;">
                    <div class="kpi-icon green">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                    </div>
                    <div>
                        <h3 style="color: var(--color-success); font-size: 1rem;">Document Processed Successfully</h3>
                        <p style="color: var(--text-secondary); font-size: 0.85rem;">${result.message}</p>
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px;">
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Filename</div>
                        <div style="color: var(--text-primary); font-weight: 500;">${result.filename}</div>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Size</div>
                        <div style="color: var(--text-primary); font-weight: 500;">${formatFileSize(result.file_size)}</div>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Pages</div>
                        <div style="color: var(--text-primary); font-weight: 500;">${result.page_count || '—'}</div>
                    </div>
                    <div>
                        <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">Chunks Indexed</div>
                        <div style="color: var(--text-primary); font-weight: 500;">${result.chunk_count || 0}</div>
                    </div>
                </div>
                <div style="margin-top: 20px; display: flex; gap: 12px;">
                    <button class="btn btn-primary" onclick="runAudit('${result.id}')">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
                        Run AI Audit
                    </button>
                    <a href="#documents" class="btn btn-secondary">View All Documents</a>
                </div>
            </div>
        `;

        // Reset after delay
        setTimeout(() => {
            progressBar.style.width = '0%';
            progressEl.style.display = 'none';
        }, 2000);

    } catch (e) {
        progressBar.style.width = '0%';
        progressEl.style.display = 'none';
        showToast('Upload failed. Make sure the backend is running.', 'error');
    }
}
