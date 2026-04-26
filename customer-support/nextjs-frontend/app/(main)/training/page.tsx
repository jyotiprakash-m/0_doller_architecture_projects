'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { APIClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { MessageSquare, Play } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export default function TrainingIndexPage() {
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [startingScenarioId, setStartingScenarioId] = useState<string | null>(null);
  const router = useRouter();
  const { updateUser, user } = useAuth();

  useEffect(() => {
    APIClient.get<any[]>('/api/simulation/scenarios')
      .then(setScenarios)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  const handleStartSession = async (scenarioId: string) => {
    setStartingScenarioId(scenarioId);
    try {
      const result = await APIClient.post<any>('/api/simulation/start', { scenario_id: scenarioId });
      
      // Update local user credits
      if (result.credits_remaining !== undefined && user) {
        updateUser({ ...user, credits: result.credits_remaining });
      }

      // Route to chat session
      router.push(`/training/${result.session.id}`);
    } catch (e: any) {
      alert(e.message || 'Failed to start session');
      setStartingScenarioId(null);
    }
  };

  if (isLoading) {
    return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto mt-20"></div>;
  }

  const difficulties = ['easy', 'medium', 'hard'];

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3 mb-6">
        <MessageSquare className="h-8 w-8 text-emerald-500" />
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Training Simulator</h1>
          <p className="text-slate-400">Select a scenario to start a real-time training session.</p>
        </div>
      </div>

      {scenarios.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <p className="text-slate-400 mb-4">No scenarios available.</p>
            <Button onClick={() => router.push('/scenarios')}>Go to Scenarios Manager</Button>
          </CardContent>
        </Card>
      ) : (
        difficulties.map(diff => {
          const group = scenarios.filter(s => s.difficulty === diff);
          if (group.length === 0) return null;

          return (
            <div key={diff} className="space-y-4">
              <h2 className="text-xl font-semibold text-slate-200 capitalize flex items-center space-x-2">
                <Badge variant={diff === 'easy' ? 'success' : diff === 'hard' ? 'danger' : 'warning'}>
                  {diff}
                </Badge>
                <span>Scenarios</span>
              </h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {group.map(scenario => (
                  <Card key={scenario.id} className="flex flex-col h-full">
                    <CardHeader className="flex-1 pb-2">
                      <CardTitle className="text-lg">{scenario.persona_name}</CardTitle>
                      <CardDescription className="line-clamp-2 mt-2">{scenario.persona_description}</CardDescription>
                      <div className="mt-4 text-sm text-slate-300">
                        <strong className="text-slate-400 block mb-1">Issue:</strong>
                        <span className="line-clamp-2">{scenario.issue_description}</span>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-4 border-t border-slate-800 flex justify-between items-center">
                      <Badge variant="outline" className="capitalize">{scenario.category?.replace('_', ' ')}</Badge>
                      <Button 
                        size="sm" 
                        onClick={() => handleStartSession(scenario.id)}
                        isLoading={startingScenarioId === scenario.id}
                        disabled={startingScenarioId !== null && startingScenarioId !== scenario.id}
                      >
                        <Play className="h-4 w-4 mr-2" /> Start (1💎)
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
