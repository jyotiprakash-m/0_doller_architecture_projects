/**
 * Chat component — RAG-powered Q&A over legal documents
 */
async function renderChat(container) {
    container.innerHTML = `
        <div class="page-header">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; width: 100%;">
                <div>
                    <h1>AI Chat</h1>
                    <p>Ask questions about your legal documents — powered by local AI</p>
                </div>
                <button class="btn btn-secondary btn-sm" onclick="clearChatHistory()" id="clear-chat-btn">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>
                    Clear History
                </button>
            </div>
        </div>

        <div class="card chat-container">
            <div class="chat-messages" id="chat-messages">
                <div class="chat-welcome">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                    </svg>
                    <h3>Ask anything about your documents</h3>
                    <p>Your questions are processed locally using RAG. Responses include citations from your uploaded documents.</p>
                </div>
            </div>

            <div class="chat-input-area">
                <textarea
                    class="chat-input"
                    id="chat-input"
                    placeholder="Ask a question about your legal documents..."
                    rows="1"
                    onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault();sendChatMessage()}"
                ></textarea>
                <button class="btn btn-primary" id="chat-send-btn" onclick="sendChatMessage()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                </button>
            </div>
        </div>
    `;

    // Load chat history
    try {
        const data = await api.get('/api/chat/history');
        const messages = data.messages || [];
        if (messages.length > 0) {
            const messagesEl = document.getElementById('chat-messages');
            messagesEl.innerHTML = '';
            messages.forEach(msg => addChatBubble(msg.role, msg.content, msg.sources));
        }
    } catch (e) {
        // Chat history not available
    }

    // Auto-resize textarea
    const textarea = document.getElementById('chat-input');
    textarea.addEventListener('input', () => {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    });
}

async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const query = input.value.trim();
    if (!query) return;

    const sendBtn = document.getElementById('chat-send-btn');
    sendBtn.disabled = true;
    input.value = '';
    input.style.height = 'auto';

    // Clear welcome message if first message
    const messagesEl = document.getElementById('chat-messages');
    const welcome = messagesEl.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    // Add user bubble
    addChatBubble('user', query);

    // Add typing indicator
    const typingId = 'typing-' + Date.now();
    messagesEl.insertAdjacentHTML('beforeend', `
        <div class="typing-indicator" id="${typingId}">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {
        const result = await api.post('/api/chat', { query });
        document.getElementById(typingId)?.remove();
        addChatBubble('assistant', result.answer, result.sources);

        // Ensure credits remain synced with backend after 0.1 deduction
        try {
            if (state.user) {
                const userData = await api.get('/api/auth/me');
                state.user.credits = userData.credits;
                if (typeof updateSidebarAuthInfo === 'function') updateSidebarAuthInfo();
            }
        } catch(e) {
            console.error("Failed to sync credits", e);
        }

    } catch (e) {
        document.getElementById(typingId)?.remove();
        
        let errorMsg = e.message;
        try {
            const parsed = JSON.parse(e.message);
            if (parsed.detail) errorMsg = parsed.detail;
        } catch (err) {
            // keep standard error message if not JSON
        }
        
        addChatBubble('assistant', 'Sorry, I could not process your question. ' + (errorMsg || 'Make sure Ollama is running.'), []);
        showToast(errorMsg || 'Chat failed.', 'error');
    }

    sendBtn.disabled = false;
    input.focus();
}

function addChatBubble(role, content, sources = []) {
    const messagesEl = document.getElementById('chat-messages');

    let sourcesHtml = '';
    if (sources && sources.length > 0 && role === 'assistant') {
        sourcesHtml = `
            <div class="chat-sources collapsed">
                <div class="chat-sources-title" onclick="toggleChatSources(this)">
                    <span>Sources (${sources.length})</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="6 9 12 15 18 9"/></svg>
                </div>
                <div class="chat-sources-content">
                    ${sources.map(s => `
                        <div class="chat-source-item">
                            <div style="flex: 1;">
                                <div style="font-weight: 600; font-size: 0.75rem;">${s.filename || 'Document'}</div>
                                ${s.score ? `<div style="font-size: 0.65rem; color: var(--color-success); opacity: 0.8;">Relevance: ${(s.score * 100).toFixed(0)}%</div>` : ''}
                                <div style="margin-top: 4px;">— ${(s.text || '').substring(0, 150)}...</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    messagesEl.insertAdjacentHTML('beforeend', `
        <div class="chat-bubble ${role}">
            <div>${formatChatContent(content)}</div>
            ${sourcesHtml}
        </div>
    `);

    messagesEl.scrollTop = messagesEl.scrollHeight;
}

function formatChatContent(text) {
    // Basic markdown-like formatting
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code style="background:rgba(255,255,255,0.06);padding:2px 6px;border-radius:4px;font-size:0.85em;">$1</code>');
}

async function clearChatHistory() {
    if (!confirm('Are you sure you want to clear the entire chat history? This cannot be undone.')) return;

    const btn = document.getElementById('clear-chat-btn');
    const originalContent = btn.innerHTML;
    
    try {
        btn.disabled = true;
        btn.innerHTML = '<div class="spinner-sm"></div> Clearing...';
        
        await api.delete('/api/chat/history');
        
        const messagesEl = document.getElementById('chat-messages');
        messagesEl.innerHTML = `
            <div class="chat-welcome">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                </svg>
                <h3>Ask anything about your documents</h3>
                <p>Your questions are processed locally using RAG. Responses include citations from your uploaded documents.</p>
            </div>
        `;
        
        showToast('Chat history cleared.', 'success');
    } catch (e) {
        showToast('Failed to clear chat history.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    }
}

function toggleChatSources(element) {
    const sourcesDiv = element.closest('.chat-sources');
    sourcesDiv.classList.toggle('collapsed');
}

// --- Document-Specific Chat Drawer Logic ---

async function sendDrawerMessage() {
    if (!state.drawer.active || !state.drawer.docId) return;

    const input = document.getElementById('drawer-chat-input');
    const query = input.value.trim();
    if (!query) return;

    const sendBtn = document.getElementById('drawer-chat-send-btn');
    sendBtn.disabled = true;
    input.value = '';
    input.style.height = 'auto';

    // Clear welcome message if first message
    const messagesEl = document.getElementById('drawer-chat-messages');
    const welcome = messagesEl.querySelector('.chat-welcome');
    if (welcome) welcome.remove();

    // Add user bubble
    addDrawerChatBubble('user', query);

    // Add typing indicator
    const typingId = 'drawer-typing-' + Date.now();
    messagesEl.insertAdjacentHTML('beforeend', `
        <div class="typing-indicator" id="${typingId}">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `);
    messagesEl.scrollTop = messagesEl.scrollHeight;

    try {
        // Critical: pass the specific docId to isolate the RAG context
        const result = await api.post('/api/chat', { 
            query: query,
            document_ids: [state.drawer.docId] 
        });
        
        document.getElementById(typingId)?.remove();
        addDrawerChatBubble('assistant', result.answer, result.sources);

        // Deduct 0.1 credit locally & refetch to stay synced
        try {
            if (state.user) {
                const userData = await api.get('/api/auth/me');
                state.user.credits = userData.credits;
                if (typeof updateSidebarAuthInfo === 'function') updateSidebarAuthInfo();
            }
        } catch(e) { /* ignore */ }

    } catch (e) {
        document.getElementById(typingId)?.remove();
        
        let errorMsg = e.message;
        try {
            const parsed = JSON.parse(e.message);
            if (parsed.detail) errorMsg = parsed.detail;
        } catch (err) {}
        
        addDrawerChatBubble('assistant', 'Sorry, I could not process your question. ' + (errorMsg || 'Make sure Ollama is running.'), []);
        showToast(errorMsg || 'Chat failed.', 'error');
    }

    sendBtn.disabled = false;
    input.focus();
}

function addDrawerChatBubble(role, content, sources = []) {
    const messagesEl = document.getElementById('drawer-chat-messages');

    let sourcesHtml = '';
    if (sources && sources.length > 0 && role === 'assistant') {
        sourcesHtml = `
            <div class="chat-sources collapsed">
                <div class="chat-sources-title" onclick="toggleChatSources(this)">
                    <span>Sources (${sources.length})</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="6 9 12 15 18 9"/></svg>
                </div>
                <div class="chat-sources-content">
                    ${sources.map(s => `
                        <div class="chat-source-item">
                            <div style="flex: 1;">
                                <div style="font-weight: 600; font-size: 0.75rem;">${s.filename || 'Document'}</div>
                                ${s.score ? `<div style="font-size: 0.65rem; color: var(--color-success); opacity: 0.8;">Relevance: ${(s.score * 100).toFixed(0)}%</div>` : ''}
                                <div style="margin-top: 4px;">— ${(s.text || '').substring(0, 150)}...</div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    // Use identical chat-bubble styling from main chat
    messagesEl.insertAdjacentHTML('beforeend', `
        <div class="chat-bubble ${role}">
            <div>${typeof formatChatContent === 'function' ? formatChatContent(content) : content}</div>
            ${sourcesHtml}
        </div>
    `);

    messagesEl.scrollTop = messagesEl.scrollHeight;
}
