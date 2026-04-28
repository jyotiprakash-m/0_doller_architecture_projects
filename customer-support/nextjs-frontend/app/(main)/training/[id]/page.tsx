'use client';

import React, { useEffect, useState, useRef, use } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { APIClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Send, User, Bot, StopCircle, ArrowLeft, Sparkles, Loader2, Database, Folder, File as FileIcon, ChevronRight, ChevronDown, CheckSquare, Square, Search } from 'lucide-react';

export default function TrainingSessionPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const sessionId = resolvedParams.id;
  const router = useRouter();

  const [session, setSession] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [scenario, setScenario] = useState<any>(null);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  
  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [suggestionContext, setSuggestionContext] = useState<string>('');
  const [showContext, setShowContext] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  
  // Knowledge Selector States
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [isSelectorOpen, setIsSelectorOpen] = useState(false);
  const [expandedKbs, setExpandedKbs] = useState<Record<string, boolean>>({});
  const [searchQuery, setSearchQuery] = useState('');

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    APIClient.get<any>(`/api/simulation/sessions/${sessionId}`)
      .then(data => {
        setSession(data.session);
        setMessages(data.messages);
        setScenario(data.scenario);
      })
      .catch(console.error);
      
    APIClient.get<any[]>('/api/kb')
      .then(async (kbs) => {
        const kbDocs = await Promise.all(kbs.map(async (kb) => {
          const docs = await APIClient.get<any[]>(`/api/kb/${kb.id}/documents`);
          return { ...kb, documents: docs };
        }));
        setKnowledgeBases(kbDocs);
      })
      .catch(console.error);
  }, [sessionId]);

  // Set initial selected documents to the scenario's KB
  useEffect(() => {
    if (scenario && knowledgeBases.length > 0 && selectedDocIds.length === 0) {
      const scenarioKb = knowledgeBases.find(kb => kb.id === scenario.kb_id);
      if (scenarioKb && scenarioKb.documents) {
        setSelectedDocIds(scenarioKb.documents.map((d: any) => d.id));
        setExpandedKbs({ [scenario.kb_id]: true });
      }
    }
  }, [scenario, knowledgeBases]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!inputText.trim() || isTyping || session?.status === 'completed') return;

    const userMessage = { role: 'agent', content: inputText };
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);

    try {
      const result = await APIClient.post<any>(`/api/simulation/${sessionId}/respond`, { message: userMessage.content });
      
      setMessages(prev => [...prev, {
        role: 'customer',
        content: result.customer_message,
        emotional_state: result.emotional_state,
      }]);

      setSession((prev: any) => ({
        ...prev,
        current_emotional_state: result.emotional_state,
        status: result.session_status,
      }));

    } catch (e: any) {
      alert(e.message || 'Failed to send message');
    } finally {
      setIsTyping(false);
    }
  };

  const fetchSuggestions = async () => {
    if (isLoadingSuggestions || isTyping || session?.status === 'completed') return;
    setIsLoadingSuggestions(true);
    setSuggestions([]);
    setSuggestionContext('');
    setShowContext(false);
    try {
      const result = await APIClient.post<any>(`/api/simulation/${sessionId}/suggestions`, {
        selected_doc_ids: selectedDocIds
      });
      setSuggestions(result.suggestions || []);
      setSuggestionContext(result.context || '');
    } catch (e: any) {
      alert(e.message || 'Failed to fetch suggestions');
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const applySuggestion = (message: string) => {
    setInputText(message);
    setSuggestions([]);
  };

  const handleEndSession = async () => {
    try {
      await APIClient.post(`/api/simulation/${sessionId}/end`);
      router.push(`/review/${sessionId}`);
    } catch (e) {
      console.error(e);
    }
  };

  const getEmotionEmoji = (emotion: string) => {
    const map: Record<string, string> = { angry: "😡", frustrated: "😤", neutral: "😐", satisfied: "😊", happy: "😄" };
    return map[emotion] || "😐";
  };

  if (!session || !scenario) {
    return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto mt-20"></div>;
  }

  const isCompleted = session.status === 'completed';

  const toggleKb = (docs: any[]) => {
    if (!docs) return;
    const allDocIds = docs.map(d => d.id);
    const areAllSelected = allDocIds.every(id => selectedDocIds.includes(id));
    
    if (areAllSelected) {
      setSelectedDocIds(prev => prev.filter(id => !allDocIds.includes(id)));
    } else {
      setSelectedDocIds(prev => Array.from(new Set([...prev, ...allDocIds])));
    }
  };

  const toggleDoc = (docId: string) => {
    setSelectedDocIds(prev => 
      prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]
    );
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      {/* Header */}
      <div className="glass-card rounded-xl p-4 flex items-center justify-between mb-4 flex-shrink-0">
        <div className="flex items-center space-x-4">
          <button onClick={() => router.push('/training')} className="text-slate-400 hover:text-white transition-colors">
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-lg font-bold text-slate-50 flex items-center space-x-2">
              <User className="h-5 w-5 text-emerald-400" />
              <span>{scenario.persona_name}</span>
            </h2>
            <div className="flex items-center space-x-2 text-xs text-slate-400 mt-1">
              <Badge variant={scenario.difficulty === 'easy' ? 'success' : scenario.difficulty === 'hard' ? 'danger' : 'warning'}>
                {scenario.difficulty}
              </Badge>
              <Badge variant="outline" className="capitalize">{scenario.category?.replace('_', ' ')}</Badge>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700">
            <span className="text-sm text-slate-300">Mood:</span>
            <span className="text-lg" title={session.current_emotional_state}>{getEmotionEmoji(session.current_emotional_state)}</span>
          </div>
          
          <Button 
            variant="outline" 
            size="sm" 
            onClick={() => setIsSelectorOpen(true)}
            className="border-slate-700 text-slate-300 hover:text-white"
          >
            <Database className="h-4 w-4 mr-2 text-indigo-400" /> Sources
            {selectedDocIds.length > 0 && (
              <span className="ml-2 bg-indigo-500 text-white text-[10px] px-1.5 py-0.5 rounded-[4px] leading-none">
                {selectedDocIds.length}
              </span>
            )}
          </Button>

          {!isCompleted ? (
            <Button variant="danger" size="sm" onClick={handleEndSession}>
              <StopCircle className="h-4 w-4 mr-2" /> End
            </Button>
          ) : (
            <Button variant="primary" size="sm" onClick={() => router.push(`/review/${sessionId}`)}>
              View Evaluation
            </Button>
          )}
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 glass-card rounded-xl overflow-y-auto p-4 space-y-4 mb-4">
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex flex-col ${msg.role === 'agent' ? 'items-end' : 'items-start'}`}
          >
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              msg.role === 'agent' 
                ? 'bg-gradient-to-br from-emerald-600 to-teal-700 text-white rounded-br-sm shadow-md' 
                : 'bg-slate-800 text-slate-200 border border-slate-700 rounded-bl-sm'
            }`}>
              <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
            </div>
            {msg.role === 'customer' && msg.emotional_state && (
              <span className="text-xs text-slate-500 mt-1 ml-1 flex items-center">
                {getEmotionEmoji(msg.emotional_state)} {msg.emotional_state}
              </span>
            )}
          </motion.div>
        ))}

        {isTyping && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-start">
            <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3 flex space-x-2">
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></span>
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
              <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></span>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* AI Suggestions Area */}
      <AnimatePresence>
        {(suggestions.length > 0 || isLoadingSuggestions) && !isCompleted && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-4"
          >
            {isLoadingSuggestions ? (
              <div className="flex items-center justify-center space-x-2 text-emerald-400 p-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">AI Co-pilot is reading the knowledge base...</span>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {suggestions.map((s, i) => (
                    <div 
                      key={i} 
                      onClick={() => applySuggestion(s.message)}
                      className="glass-card p-3 rounded-xl border border-emerald-500/30 cursor-pointer hover:bg-emerald-500/10 transition-colors flex flex-col h-full"
                    >
                      <div className="text-xs font-bold text-emerald-400 mb-1 flex items-center">
                        <Sparkles className="h-3 w-3 mr-1" />
                        {s.style}
                      </div>
                      <p className="text-xs text-slate-300 line-clamp-3">{s.message}</p>
                    </div>
                  ))}
                </div>
                
                {suggestionContext && (
                  <div>
                    <button 
                      type="button"
                      onClick={() => setShowContext(!showContext)}
                      className="text-xs text-emerald-500 hover:text-emerald-400 font-medium mb-2"
                    >
                      {showContext ? 'Hide Knowledge Context' : 'View Knowledge Context Used'}
                    </button>
                    <AnimatePresence>
                      {showContext && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          className="bg-slate-900/80 rounded-lg p-3 text-xs text-slate-400 max-h-40 overflow-y-auto whitespace-pre-wrap font-mono border border-slate-800"
                        >
                          {suggestionContext}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <div className="glass-card rounded-xl p-3 flex-shrink-0">
        <form 
          onSubmit={e => { e.preventDefault(); handleSend(); }}
          className="flex space-x-3 items-end"
        >
          <Button
            type="button"
            variant="outline"
            className="h-[52px] px-3 flex-shrink-0 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20"
            onClick={fetchSuggestions}
            disabled={isTyping || isCompleted || isLoadingSuggestions}
            title="Get AI Suggestions from Knowledge Base"
          >
            {isLoadingSuggestions ? <Loader2 className="h-5 w-5 animate-spin" /> : <Sparkles className="h-5 w-5" />}
          </Button>
          <div className="flex-1 relative">
            <textarea
              className="w-full bg-slate-900/50 border border-slate-700 rounded-lg p-3 text-sm text-slate-50 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none"
              placeholder={isCompleted ? "Session ended." : "Type your response..."}
              rows={2}
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyDown={e => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={isTyping || isCompleted}
            />
          </div>
          <Button 
            type="submit"  
            disabled={!inputText.trim() || isTyping || isCompleted}
            className="h-[52px] w-[52px] p-0 flex items-center justify-center rounded-lg"
          >
            <Send className="h-5 w-5" />
          </Button>
        </form>
      </div>

      {/* Knowledge Selector Drawer */}
      <AnimatePresence>
        {isSelectorOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsSelectorOpen(false)}
              className="fixed inset-0 bg-black/50 z-40"
            />
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed top-0 right-0 h-full w-80 bg-slate-900 border-l border-slate-800 shadow-2xl z-50 flex flex-col"
            >
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-semibold text-slate-200 flex items-center">
                  <Database className="w-4 h-4 mr-2 text-indigo-400" />
                  Knowledge Sources
                </h3>
                <button onClick={() => setIsSelectorOpen(false)} className="text-slate-400 hover:text-white">
                  &times;
                </button>
              </div>
              <div className="p-4 overflow-y-auto flex-1 space-y-4">
                <p className="text-xs text-slate-400 mb-2">Select the documents the AI Copilot should use to generate suggestions.</p>
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search folders or files..."
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>
                {knowledgeBases
                  .filter(kb => {
                    if (!searchQuery) return true;
                    const query = searchQuery.toLowerCase();
                    const kbMatches = kb.name.toLowerCase().includes(query);
                    const docMatches = kb.documents?.some((d: any) => d.filename.toLowerCase().includes(query));
                    return kbMatches || docMatches;
                  })
                  .map((kb) => {
                  const query = searchQuery.toLowerCase();
                  const kbMatches = !searchQuery || kb.name.toLowerCase().includes(query);
                  const displayDocs = kbMatches ? kb.documents : (kb.documents?.filter((d: any) => d.filename.toLowerCase().includes(query)) || []);
                  
                  const allDocsSelected = displayDocs?.length > 0 && displayDocs.every((d: any) => selectedDocIds.includes(d.id));
                  const someDocsSelected = displayDocs?.some((d: any) => selectedDocIds.includes(d.id)) && !allDocsSelected;
                  const isExpanded = expandedKbs[kb.id] !== false || (searchQuery.length > 0 && !kbMatches); // Auto-expand if searching docs

                  return (
                    <div key={kb.id} className="border border-slate-800 rounded-lg overflow-hidden bg-slate-900/50">
                      <div className="flex items-center p-2 hover:bg-slate-800 cursor-pointer">
                        <button 
                          onClick={(e) => { e.stopPropagation(); setExpandedKbs(prev => ({...prev, [kb.id]: !isExpanded})); }}
                          className="p-1 mr-1 text-slate-400 hover:text-white"
                        >
                          {isExpanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        </button>
                        <button 
                          onClick={(e) => { e.stopPropagation(); toggleKb(displayDocs || []); }}
                          className="mr-2 text-indigo-400 hover:text-indigo-300"
                        >
                          {allDocsSelected ? <CheckSquare className="w-4 h-4" /> : 
                           someDocsSelected ? <span className="w-4 h-4 flex items-center justify-center border border-indigo-400 rounded-[3px] bg-indigo-400/20"><span className="w-2 h-2 bg-indigo-400" /></span> : 
                           <Square className="w-4 h-4 opacity-50" />}
                        </button>
                        <Folder className="w-4 h-4 mr-2 text-amber-400" />
                        <span className="text-sm text-slate-300 truncate font-medium select-none" onClick={() => setExpandedKbs(prev => ({...prev, [kb.id]: !isExpanded}))}>{kb.name}</span>
                      </div>
                      
                      <AnimatePresence>
                        {isExpanded && displayDocs && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="overflow-hidden"
                          >
                            <div className="pl-9 pr-2 pb-2 space-y-1">
                              {displayDocs.length === 0 ? (
                                <div className="text-xs text-slate-500 py-1">No documents</div>
                              ) : (
                                displayDocs.map((doc: any) => {
                                  const isSelected = selectedDocIds.includes(doc.id);
                                  return (
                                    <div key={doc.id} className="flex items-center py-1 hover:bg-slate-800 rounded px-1 cursor-pointer" onClick={() => toggleDoc(doc.id)}>
                                      <button className="mr-2 text-indigo-400">
                                        {isSelected ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5 opacity-50" />}
                                      </button>
                                      <FileIcon className="w-3.5 h-3.5 mr-2 text-slate-400" />
                                      <span className="text-xs text-slate-400 truncate select-none" title={doc.filename}>{doc.filename}</span>
                                    </div>
                                  );
                                })
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
