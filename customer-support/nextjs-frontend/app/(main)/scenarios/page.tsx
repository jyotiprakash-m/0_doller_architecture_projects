'use client';

import React, { useEffect, useState } from 'react';
import { APIClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Target, Bot, User, Trash2 } from 'lucide-react';

export default function ScenariosPage() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [kbs, setKbs] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [generateCount, setGenerateCount] = useState(3);
  const [selectedKb, setSelectedKb] = useState('');

  // Manual form
  const [personaName, setPersonaName] = useState('');
  const [personaDesc, setPersonaDesc] = useState('');
  const [issueDesc, setIssueDesc] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [category, setCategory] = useState('general_inquiry');
  const [emotion, setEmotion] = useState('neutral');
  const [expected, setExpected] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [scens, kbList] = await Promise.all([
        APIClient.get<any[]>('/api/simulation/scenarios'),
        APIClient.get<any[]>('/api/kb')
      ]);
      setScenarios(scens);
      setKbs(kbList);
      if (kbList.length > 0) setSelectedKb(kbList[0].id);
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerate = async () => {
    if (!selectedKb) return;
    setIsGenerating(true);
    try {
      await APIClient.post('/api/simulation/scenarios/generate', { kb_id: selectedKb, count: generateCount });
      fetchData();
    } catch (e: any) {
      alert(e.message || 'Failed to generate scenarios');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);
    try {
      await APIClient.post('/api/simulation/scenarios', {
        persona_name: personaName,
        persona_description: personaDesc,
        issue_description: issueDesc,
        difficulty,
        category,
        initial_emotional_state: emotion,
        expected_resolution: expected,
        kb_id: selectedKb || null,
      });
      setPersonaName('');
      setPersonaDesc('');
      setIssueDesc('');
      setExpected('');
      fetchData();
    } catch (e: any) {
      alert(e.message || 'Failed to create scenario');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await APIClient.delete(`/api/simulation/scenarios/${id}`);
      fetchData();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3 mb-6">
        <Target className="h-8 w-8 text-emerald-500" />
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Scenario Manager</h1>
          <p className="text-slate-400">Create custom scenarios or auto-generate them from your knowledge bases.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Auto Generate */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Bot className="h-5 w-5 text-teal-500" />
              <span>Auto-Generate via RAG</span>
            </CardTitle>
            <CardDescription>AI creates realistic scenarios directly from your docs.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Knowledge Base</label>
              <select 
                className="flex h-10 w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-50"
                value={selectedKb}
                onChange={(e) => setSelectedKb(e.target.value)}
              >
                {kbs.length === 0 ? <option value="">No KBs available</option> : null}
                {kbs.map(kb => (
                  <option key={kb.id} value={kb.id}>{kb.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">Number of Scenarios</label>
              <input 
                type="number" 
                min="1" max="10" 
                className="flex h-10 w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-50"
                value={generateCount}
                onChange={(e) => setGenerateCount(Number(e.target.value))}
              />
            </div>
            <Button 
              className="w-full" 
              onClick={handleGenerate} 
              isLoading={isGenerating} 
              disabled={kbs.length === 0}
            >
              Generate Scenarios (Cost: 1 Credit)
            </Button>
          </CardContent>
        </Card>

        {/* Manual Create */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <User className="h-5 w-5 text-emerald-500" />
              <span>Manual Creation</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreate} className="space-y-4">
              <Input label="Customer Name" value={personaName} onChange={e => setPersonaName(e.target.value)} required />
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Background / Personality</label>
                <textarea 
                  className="flex w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-50 min-h-[60px]"
                  value={personaDesc} onChange={e => setPersonaDesc(e.target.value)} required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1.5">Issue Description</label>
                <textarea 
                  className="flex w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 py-2 text-sm text-slate-50 min-h-[60px]"
                  value={issueDesc} onChange={e => setIssueDesc(e.target.value)} required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">Difficulty</label>
                  <select className="flex h-10 w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 text-sm text-slate-50" value={difficulty} onChange={e => setDifficulty(e.target.value)}>
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">Initial Emotion</label>
                  <select className="flex h-10 w-full rounded-md border border-slate-700 bg-slate-900/50 px-3 text-sm text-slate-50" value={emotion} onChange={e => setEmotion(e.target.value)}>
                    <option value="neutral">Neutral</option>
                    <option value="frustrated">Frustrated</option>
                    <option value="angry">Angry</option>
                  </select>
                </div>
              </div>

              <Button type="submit" className="w-full" variant="outline" isLoading={isCreating}>Create Scenario</Button>
            </form>
          </CardContent>
        </Card>
      </div>

      <h2 className="text-xl font-bold text-slate-50 pt-4">All Scenarios</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map(scen => (
          <Card key={scen.id} className="relative group">
            <button 
              onClick={() => handleDelete(scen.id)}
              className="absolute top-4 right-4 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-400"
            >
              <Trash2 className="h-4 w-4" />
            </button>
            <CardHeader className="pb-2">
              <div className="flex items-center space-x-2 mb-2">
                {scen.is_auto_generated ? <Bot className="h-4 w-4 text-teal-400" /> : <User className="h-4 w-4 text-emerald-400" />}
                <CardTitle className="text-lg">{scen.persona_name}</CardTitle>
              </div>
              <div className="flex space-x-2">
                <Badge variant={scen.difficulty === 'easy' ? 'success' : scen.difficulty === 'hard' ? 'danger' : 'warning'}>
                  {scen.difficulty}
                </Badge>
                <Badge variant="outline" className="capitalize">{scen.category?.replace('_', ' ')}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400 mt-2 line-clamp-3">{scen.issue_description}</p>
            </CardContent>
          </Card>
        ))}
        {scenarios.length === 0 && (
          <div className="col-span-full text-center py-12 text-slate-500">
            No scenarios available. Generate or create one above!
          </div>
        )}
      </div>
    </div>
  );
}
