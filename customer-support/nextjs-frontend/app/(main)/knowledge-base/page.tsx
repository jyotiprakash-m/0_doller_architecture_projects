'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { APIClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { BookOpen, Trash2, UploadCloud, FileText, CheckCircle, Clock, Loader2, MessageSquare, X, Send } from 'lucide-react';

export default function KnowledgeBasePage() {
  const [kbs, setKbs] = useState<any[]>([]);
  const [newKbName, setNewKbName] = useState('');
  const [newKbDesc, setNewKbDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [docsMap, setDocsMap] = useState<Record<string, any[]>>({});
  const [uploadingKbId, setUploadingKbId] = useState<string | null>(null);
  const [urlInputs, setUrlInputs] = useState<Record<string, string>>({});
  
  // Doc Chat States
  const [chatDoc, setChatDoc] = useState<{kbId: string, doc: any} | null>(null);
  const [chatHistory, setChatHistory] = useState<{role: string, content: string, sources?: any[]}[]>([]);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const [globalChat, setGlobalChat] = useState<{kbId: string, kbName: string} | null>(null);
  const [chatInput, setChatInput] = useState('');
  const [isChatting, setIsChatting] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (chatDoc || globalChat) {
      scrollToBottom();
    }
  }, [chatHistory, chatDoc, globalChat]);

  const pollingRef = useRef<Record<string, NodeJS.Timeout>>({});

  // Cleanup polling intervals on unmount
  useEffect(() => {
    return () => {
      Object.values(pollingRef.current).forEach(clearInterval);
    };
  }, []);

  useEffect(() => {
    fetchKbs();
  }, []);

  const fetchKbs = async () => {
    try {
      const data = await APIClient.get<any[]>('/api/kb');
      setKbs(data);
      data.forEach(kb => fetchDocs(kb.id));
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDocs = async (kbId: string) => {
    try {
      const docs = await APIClient.get<any[]>(`/api/kb/${kbId}/documents`);
      setDocsMap(prev => ({ ...prev, [kbId]: docs }));

      // Auto-start polling if any document is still processing
      const hasProcessing = docs.some(d => d.status === 'processing');
      if (hasProcessing) {
        startPolling(kbId);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleCreateKb = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKbName) return;
    setIsCreating(true);
    try {
      await APIClient.post('/api/kb', { name: newKbName, description: newKbDesc });
      setNewKbName('');
      setNewKbDesc('');
      fetchKbs();
    } catch (e) {
      console.error(e);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteKb = async (kbId: string) => {
    if (!confirm('Are you sure you want to delete this knowledge base?')) return;
    try {
      await APIClient.delete(`/api/kb/${kbId}`);
      fetchKbs();
    } catch (e) {
      console.error(e);
    }
  };

  const startPolling = useCallback((kbId: string) => {
    // Don't create duplicate pollers for the same KB
    if (pollingRef.current[kbId]) return;

    const interval = setInterval(async () => {
      try {
        const docs = await APIClient.get<any[]>(`/api/kb/${kbId}/documents`);
        setDocsMap(prev => ({ ...prev, [kbId]: docs }));

        // Stop polling if all docs are indexed or errored (no more "processing")
        const hasProcessing = docs.some(d => d.status === 'processing');
        if (!hasProcessing) {
          clearInterval(interval);
          delete pollingRef.current[kbId];
          fetchKbs(); // refresh doc counts
        }
      } catch (e) {
        console.error(e);
      }
    }, 5000); // Poll every 5 seconds

    pollingRef.current[kbId] = interval;
  }, []);

  const handleUpload = async (kbId: string, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingKbId(kbId);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await APIClient.post(`/api/kb/${kbId}/upload`, formData, true);
      fetchDocs(kbId);
      fetchKbs();
      // Start polling for status updates (processing → indexed)
      startPolling(kbId);
    } catch (err) {
      console.error(err);
      alert('Failed to upload document');
    } finally {
      setUploadingKbId(null);
      if (e.target) e.target.value = '';
    }
  };

  const handleDeleteDoc = async (kbId: string, docId: string) => {
    if (!confirm('Delete this document?')) return;
    try {
      await APIClient.delete(`/api/kb/${kbId}/documents/${docId}`);
      fetchDocs(kbId);
      fetchKbs();
    } catch (e) {
      console.error(e);
    }
  };

  const handleScrapeUrl = async (kbId: string) => {
    const url = urlInputs[kbId];
    if (!url) return;

    setUploadingKbId(kbId);
    try {
      await APIClient.post(`/api/kb/${kbId}/url`, { url });
      setUrlInputs(prev => ({ ...prev, [kbId]: '' }));
      fetchDocs(kbId);
    } catch (error: any) {
      console.error(error);
      alert('Failed to scrape URL: ' + (error.message || 'Unknown error'));
    } finally {
      setUploadingKbId(null);
    }
  };

  const handleSendDocChat = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!chatInput.trim() || (!chatDoc && !globalChat)) return;

    const userMsg = chatInput.trim();
    setChatInput('');
    setChatHistory(prev => [...prev, { role: 'user', content: userMsg }]);
    setIsChatting(true);

    try {
      const endpoint = chatDoc
        ? `/api/kb/${chatDoc.kbId}/documents/${chatDoc.doc.id}/chat`
        : `/api/kb/${globalChat!.kbId}/chat`;

      const response = await APIClient.post<any>(endpoint, { 
        question: userMsg,
        chat_history: chatHistory
      });
      setChatHistory(prev => [...prev, { 
        role: 'ai', 
        content: response.answer || response,
        sources: response.sources || []
      }]);
    } catch (e) {
      console.error(e);
      setChatHistory(prev => [...prev, { role: 'ai', content: 'Sorry, I encountered an error.' }]);
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3 mb-6">
        <BookOpen className="h-8 w-8 text-emerald-500" />
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Knowledge Base</h1>
          <p className="text-slate-400">Upload your company's documents to power realistic training scenarios.</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create New Knowledge Base</CardTitle>
          <CardDescription>Group your documents by product line or department.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateKb} className="flex gap-4 items-end">
            <div className="flex-1">
              <Input
                label="Name"
                placeholder="e.g., Support Runbook 2024"
                value={newKbName}
                onChange={(e) => setNewKbName(e.target.value)}
                required
              />
            </div>
            <div className="flex-1">
              <Input
                label="Description"
                placeholder="Optional description"
                value={newKbDesc}
                onChange={(e) => setNewKbDesc(e.target.value)}
              />
            </div>
            <Button type="submit" isLoading={isCreating}>Create</Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-6">
        {kbs.map((kb) => (
          <Card key={kb.id}>
            <CardHeader className="flex flex-row items-start justify-between">
              <div>
                <CardTitle className="text-xl flex items-center space-x-2">
                  <BookOpen className="h-5 w-5 text-emerald-500" />
                  <span>{kb.name}</span>
                </CardTitle>
                <CardDescription className="mt-1">{kb.description}</CardDescription>
                <div className="mt-2 text-xs text-slate-500">
                  {kb.doc_count || 0} documents · Created {new Date(kb.created_at).toLocaleDateString()}
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button 
                  size="sm" 
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-xs"
                  onClick={() => {
                    setChatDoc(null);
                    setGlobalChat({ kbId: kb.id, kbName: kb.name });
                    setChatHistory([{ role: 'ai', content: `Hi! I have access to all **${kb.doc_count || 0} documents** in **${kb.name}**. Ask me anything across the entire knowledge base!` }]);
                    setExpandedSources({});
                  }}
                  disabled={!kb.doc_count}
                >
                  <MessageSquare className="h-3.5 w-3.5 mr-1.5" /> Chat with KB
                </Button>
                <Button variant="danger" size="sm" onClick={() => handleDeleteKb(kb.id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="mt-4 border border-slate-700 rounded-lg overflow-hidden bg-slate-900/50">
                <div className="p-4 border-b border-slate-700 flex justify-between items-center bg-slate-800/50">
                  <h4 className="font-medium text-slate-200 text-sm">Documents</h4>
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <Input
                        placeholder="https://example.com/docs"
                        className="h-8 text-xs w-48 bg-slate-950 border-slate-700"
                        value={urlInputs[kb.id] || ''}
                        onChange={(e) => setUrlInputs(prev => ({ ...prev, [kb.id]: e.target.value }))}
                        onKeyDown={(e) => e.key === 'Enter' && handleScrapeUrl(kb.id)}
                        disabled={uploadingKbId === kb.id}
                      />
                      <Button 
                        size="sm" 
                        variant="secondary" 
                        className="h-8 text-xs" 
                        onClick={() => handleScrapeUrl(kb.id)}
                        disabled={uploadingKbId === kb.id || !urlInputs[kb.id]}
                      >
                        Scrape URL
                      </Button>
                    </div>
                    <div className="relative">
                      <input
                        type="file"
                        id={`file-${kb.id}`}
                        className="hidden"
                        accept=".pdf,.txt,.md,.docx"
                        onChange={(e) => handleUpload(kb.id, e)}
                      />
                      <label htmlFor={`file-${kb.id}`}>
                        <div className={`cursor-pointer inline-flex items-center justify-center rounded-lg font-medium transition-colors border-2 border-emerald-600 text-emerald-500 hover:bg-emerald-600/10 h-8 px-3 text-xs ${uploadingKbId === kb.id ? 'opacity-50 pointer-events-none' : ''}`}>
                          <span className="flex items-center space-x-2">
                            {uploadingKbId === kb.id ? (
                              <svg className="animate-spin h-4 w-4 text-current" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                            ) : (
                              <UploadCloud className="h-4 w-4" />
                            )}
                            <span>Upload & Index</span>
                          </span>
                        </div>
                      </label>
                    </div>
                  </div>
                </div>
                
                <ul className="divide-y divide-slate-800">
                  {(docsMap[kb.id] || []).length === 0 ? (
                    <li className="p-4 text-center text-sm text-slate-500">No documents uploaded yet.</li>
                  ) : (
                    docsMap[kb.id]?.map((doc) => (
                      <li key={doc.id} className="p-4 hover:bg-slate-800/30 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <FileText className="h-5 w-5 text-slate-400" />
                            <div>
                              <p className="text-sm font-medium text-slate-200">{doc.filename}</p>
                              <div className="flex items-center space-x-2 text-xs text-slate-500 mt-1">
                                <span>{(doc.file_size / 1024).toFixed(1)} KB</span>
                                <span>·</span>
                                <span>{doc.chunk_count || 0} chunks</span>
                                <span>·</span>
                                {doc.status === 'indexed' ? (
                                  <span className="flex items-center text-emerald-500"><CheckCircle className="h-3 w-3 mr-1" /> Indexed</span>
                                ) : doc.status === 'error' ? (
                                  <span className="flex items-center text-red-500"><Clock className="h-3 w-3 mr-1" /> Error</span>
                                ) : (
                                  <span className="flex items-center text-amber-500"><Loader2 className="h-3 w-3 mr-1 animate-spin" /> Processing {doc.progress || 0}%</span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-1">
                            {doc.status === 'indexed' && (
                              <button
                                onClick={() => {
                                  setGlobalChat(null);
                                  setChatDoc({ kbId: kb.id, doc });
                                  setChatHistory([{ role: 'ai', content: `Hi! I've analyzed **${doc.filename}**. What would you like to know about it?` }]);
                                  setExpandedSources({});
                                }}
                                className="p-2 text-slate-500 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-lg transition-colors"
                                title="Chat with Document"
                              >
                                <MessageSquare className="h-4 w-4" />
                              </button>
                            )}
                            <button
                              onClick={() => handleDeleteDoc(kb.id, doc.id)}
                              className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                              title="Delete Document"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                        {(doc.status === 'processing' || doc.status === 'uploaded') && (
                          <div className="mt-3 ml-8">
                            <div className="w-full bg-slate-700/50 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-gradient-to-r from-amber-500 to-emerald-500 h-1.5 rounded-full transition-all duration-700 ease-out"
                                style={{ width: `${doc.progress || 0}%` }}
                              />
                            </div>
                            <p className="text-[10px] text-slate-500 mt-1">
                              {(doc.progress || 0) < 20 ? 'Extracting text...' :
                               (doc.progress || 0) < 25 ? 'Chunking document...' :
                               (doc.progress || 0) < 85 ? 'AI extracting keywords & summaries...' :
                               (doc.progress || 0) < 95 ? 'Embedding vectors...' : 'Finalizing...'}
                            </p>
                          </div>
                        )}
                      </li>
                    ))
                  )}
                </ul>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Right-side Sliding Drawer for Chat */}
      <div 
        className={`fixed top-0 right-0 h-full w-96 bg-slate-900 border-l border-slate-800 shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${(chatDoc || globalChat) ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
          <div>
            <h3 className="font-semibold text-slate-200 flex items-center">
              {globalChat ? (
                <><BookOpen className="w-4 h-4 mr-2 text-emerald-400" /> Knowledge Base Chat</>
              ) : (
                <><FileText className="w-4 h-4 mr-2 text-indigo-400" /> Document Chat</>
              )}
            </h3>
            <p className="text-xs text-slate-500 mt-1 truncate max-w-[250px]" title={globalChat ? globalChat.kbName : chatDoc?.doc?.filename}>
              {globalChat ? globalChat.kbName : chatDoc?.doc?.filename}
            </p>
          </div>
          <button 
            onClick={() => { setChatDoc(null); setGlobalChat(null); }}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-950/50">
          {chatHistory.map((msg, i) => (
            <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm ${
                msg.role === 'user' 
                  ? 'bg-indigo-600 text-white rounded-br-none' 
                  : 'bg-slate-800 text-slate-200 rounded-bl-none'
              }`}>
                {msg.content}
              </div>
              {/* Citation Badges */}
              {msg.role === 'ai' && msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 max-w-[85%]">
                  <div className="flex flex-wrap gap-1.5">
                    {msg.sources.map((src: any, si: number) => (
                      <button
                        key={si}
                        onClick={() => setExpandedSources(prev => ({ ...prev, [`${i}-${si}`]: !prev[`${i}-${si}`] }))}
                        className={`inline-flex items-center text-[10px] px-2 py-1 rounded-full border transition-all cursor-pointer ${
                          expandedSources[`${i}-${si}`]
                            ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300'
                            : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:border-indigo-500/40 hover:text-indigo-300'
                        }`}
                      >
                        📄 Source {si + 1}{src.score ? ` · ${(src.score * 100).toFixed(0)}%` : ''}
                      </button>
                    ))}
                  </div>
                  {/* Expanded Source Detail */}
                  {msg.sources.map((src: any, si: number) => (
                    expandedSources[`${i}-${si}`] && (
                      <div key={`detail-${si}`} className="mt-2 p-3 bg-slate-800/80 border border-slate-700 rounded-lg text-xs">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-indigo-400 font-medium truncate max-w-[200px]" title={src.filename}>
                            📄 {src.filename?.length > 30 ? src.filename.slice(0, 30) + '...' : src.filename}
                          </span>
                          {src.score && <span className="text-slate-500">Score: {(src.score * 100).toFixed(1)}%</span>}
                        </div>
                        <p className="text-slate-300 leading-relaxed whitespace-pre-wrap border-l-2 border-indigo-500/30 pl-3">
                          {src.text}
                        </p>
                      </div>
                    )
                  ))}
                </div>
              )}
            </div>
          ))}
          {isChatting && (
            <div className="flex justify-start">
              <div className="bg-slate-800 text-slate-400 rounded-2xl rounded-bl-none px-4 py-2 text-sm flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>AI is thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="p-4 border-t border-slate-800 bg-slate-900">
          <form onSubmit={handleSendDocChat} className="flex space-x-2">
            <Input
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder="Ask about this document..."
              disabled={isChatting}
              className="flex-1 bg-slate-950 border-slate-800"
            />
            <Button type="submit" disabled={isChatting || !chatInput.trim()} size="sm" className="bg-indigo-600 hover:bg-indigo-700 text-white shrink-0 mt-1">
              <Send className="w-4 h-4" />
            </Button>
          </form>
        </div>
      </div>

    </div>
  );
}
