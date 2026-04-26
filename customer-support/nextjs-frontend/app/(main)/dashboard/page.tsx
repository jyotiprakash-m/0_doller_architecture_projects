'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { APIClient } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Target, Star, BookOpen, Diamond, TrendingUp, Award, Clock } from 'lucide-react';

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    APIClient.get('/api/analytics/dashboard')
      .then((data) => {
        setStats(data);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Failed to load dashboard data.</p>
      </div>
    );
  }

  const scores = [
    { name: 'Empathy', score: stats.avg_empathy_score || 0, color: 'bg-rose-500' },
    { name: 'Accuracy', score: stats.avg_accuracy_score || 0, color: 'bg-blue-500' },
    { name: 'Resolution', score: stats.avg_resolution_score || 0, color: 'bg-emerald-500' },
    { name: 'Communication', score: stats.avg_communication_score || 0, color: 'bg-amber-500' },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-slate-50">Dashboard</h1>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <MetricCard title="Sessions" value={stats.completed_sessions || 0} icon={<Target className="h-5 w-5 text-emerald-400" />} />
        <MetricCard title="Avg Score" value={`${(stats.avg_overall_score || 0).toFixed(0)}/100`} icon={<Star className="h-5 w-5 text-amber-400" />} />
        <MetricCard title="Knowledge Bases" value={stats.total_knowledge_bases || 0} icon={<BookOpen className="h-5 w-5 text-blue-400" />} />
        <MetricCard title="Scenarios" value={stats.total_scenarios || 0} icon={<Award className="h-5 w-5 text-purple-400" />} />
        <MetricCard title="Credits" value={(stats.user_credits || 0).toFixed(1)} icon={<Diamond className="h-5 w-5 text-cyan-400" />} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Score Breakdown */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5 text-emerald-500" />
              <span>Score Breakdown</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 pt-4">
            {scores.map((s, i) => (
              <div key={i}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-slate-300">{s.name}</span>
                  <span className="text-sm font-medium text-slate-400">{s.score.toFixed(0)}</span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2.5">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(s.score, 100)}%` }}
                    transition={{ duration: 1, delay: i * 0.1 }}
                    className={`h-2.5 rounded-full ${s.color}`}
                  ></motion.div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Best Category */}
        <Card className="flex flex-col items-center justify-center text-center">
          <div className="bg-emerald-500/10 p-4 rounded-full mb-4">
            <Award className="h-10 w-10 text-emerald-500" />
          </div>
          <h3 className="text-lg font-medium text-slate-300 mb-1">Best Category</h3>
          {stats.best_category ? (
            <>
              <p className="text-2xl font-bold text-slate-50 capitalize mb-2">
                {stats.best_category.category.replace('_', ' ')}
              </p>
              <Badge variant="success" className="text-lg px-4 py-1">
                {stats.best_category.avg_score.toFixed(0)}/100
              </Badge>
            </>
          ) : (
            <p className="text-slate-500">Not enough data</p>
          )}
        </Card>
      </div>

      {/* Recent Sessions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5 text-emerald-500" />
            <span>Recent Sessions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {stats.recent_sessions && stats.recent_sessions.length > 0 ? (
            <div className="divide-y divide-slate-800">
              {stats.recent_sessions.map((session: any) => (
                <div key={session.id} className="py-4 flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-200">{session.persona_name || 'Unknown'}</p>
                    <p className="text-sm text-slate-500 capitalize">{session.category?.replace('_', ' ')}</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    {session.status === 'completed' ? (
                      <Badge variant="success">Completed</Badge>
                    ) : (
                      <Badge variant="warning">Active</Badge>
                    )}
                    {session.overall_score ? (
                      <span className="font-bold text-emerald-400">{session.overall_score.toFixed(0)}/100</span>
                    ) : (
                      <span className="text-slate-500">—</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 text-center py-6">No sessions yet. Head to the Training page to start!</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function MetricCard({ title, value, icon }: { title: string; value: React.ReactNode; icon: React.ReactNode }) {
  return (
    <Card className="p-4 flex flex-col justify-between">
      <div className="flex justify-between items-start mb-4">
        <p className="text-sm font-medium text-slate-400">{title}</p>
        <div className="p-2 bg-slate-800 rounded-lg">{icon}</div>
      </div>
      <p className="text-2xl font-bold text-slate-50">{value}</p>
    </Card>
  );
}
