'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { APIClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LineChart, Clock, Target, Star } from 'lucide-react';

export default function ReviewIndexPage() {
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    APIClient.get<any[]>('/api/evaluation/history/all')
      .then(setHistory)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto mt-20"></div>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3 mb-6">
        <LineChart className="h-8 w-8 text-emerald-500" />
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Review & Coaching</h1>
          <p className="text-slate-400">Review your past sessions, read AI evaluations, and get actionable coaching feedback.</p>
        </div>
      </div>

      {history.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <p className="text-slate-400 mb-4">You haven't completed any training sessions yet.</p>
            <Link href="/training">
              <Button>Start Training</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {history.map(session => (
            <Card key={session.id} className="flex flex-col">
              <CardHeader className="pb-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center space-x-2 text-sm text-slate-400">
                    <Clock className="h-4 w-4" />
                    <span>{new Date(session.created_at).toLocaleDateString()}</span>
                  </div>
                  <Badge variant={session.status === 'completed' ? 'success' : 'warning'}>
                    {session.status}
                  </Badge>
                </div>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-emerald-400" />
                  <span>{session.persona_name || 'Training Session'}</span>
                </CardTitle>
                <CardDescription className="capitalize mt-1">
                  {session.category?.replace('_', ' ') || 'General'}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0 mt-auto">
                <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-800 mb-4">
                  <div className="flex items-center space-x-2 text-slate-300">
                    <Star className="h-4 w-4 text-amber-400" />
                    <span className="text-sm font-medium">Overall Score</span>
                  </div>
                  <span className="text-lg font-bold text-white">
                    {session.overall_score ? session.overall_score.toFixed(0) : '—'}<span className="text-sm text-slate-500 font-normal">/100</span>
                  </span>
                </div>
                <Link href={`/review/${session.session_id}`} className="block w-full">
                  <Button variant="secondary" className="w-full">
                    View Full Report
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
