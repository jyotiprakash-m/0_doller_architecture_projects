'use client';

import React, { useEffect, useState, use } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { APIClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ArrowLeft, Target, Award, BrainCircuit, CheckCircle, MessageSquare } from 'lucide-react';

export default function ReviewDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const sessionId = resolvedParams.id;
  
  const [evaluation, setEvaluation] = useState<any>(null);
  const [feedback, setFeedback] = useState<any>(null);
  const [session, setSession] = useState<any>(null);
  const [scenario, setScenario] = useState<any>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      APIClient.get<any>(`/api/evaluation/${sessionId}`).catch(() => null),
      APIClient.get<any>(`/api/evaluation/${sessionId}/feedback`).catch(() => null),
      APIClient.get<any>(`/api/simulation/sessions/${sessionId}`).catch(() => null)
    ]).then(([evalData, feedData, sessData]) => {
      setEvaluation(evalData);
      if (feedData) setFeedback(feedData.feedback);
      if (sessData) {
        setSession(sessData.session);
        setScenario(sessData.scenario);
        setMessages(sessData.messages);
      }
    }).finally(() => setIsLoading(false));
  }, [sessionId]);

  const handleRunEvaluation = async () => {
    setIsLoading(true);
    try {
      await APIClient.post(`/api/evaluation/${sessionId}`);
      window.location.reload();
    } catch (e: any) {
      alert(e.message || 'Failed to run evaluation');
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto mt-20"></div>;
  }

  if (!session) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Session not found.</p>
        <Link href="/review"><Button className="mt-4">Back to Reviews</Button></Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-4">
        <Link href="/review" className="text-slate-400 hover:text-white transition-colors">
          <ArrowLeft className="h-6 w-6" />
        </Link>
        <div>
          <h1 className="text-3xl font-bold text-slate-50 flex items-center space-x-2">
            <span>Session Report:</span>
            <span className="text-emerald-400">{scenario?.persona_name || 'Unknown'}</span>
          </h1>
          <div className="flex items-center space-x-2 text-sm text-slate-400 mt-1">
            <span>{new Date(session.created_at).toLocaleString()}</span>
            <span>·</span>
            <Badge variant={session.status === 'completed' ? 'success' : 'warning'}>{session.status}</Badge>
          </div>
        </div>
      </div>

      {!evaluation ? (
        <Card className="text-center py-12">
          <CardContent>
            <BrainCircuit className="h-12 w-12 text-emerald-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-slate-50 mb-2">Evaluation Pending</h3>
            <p className="text-slate-400 mb-6 max-w-md mx-auto">
              This session hasn't been evaluated yet. Run the AI evaluator to analyze your performance and generate coaching feedback.
            </p>
            <Button size="lg" onClick={handleRunEvaluation}>
              Run AI Evaluation (Cost: 1💎)
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Scores & Feedback */}
          <div className="lg:col-span-2 space-y-8">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Award className="h-5 w-5 text-emerald-400" />
                  <span>Performance Scorecard</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between mb-8 p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl">
                  <span className="text-lg font-medium text-emerald-100">Overall Rating</span>
                  <div className="flex items-baseline space-x-1">
                    <span className="text-4xl font-extrabold text-emerald-400">{evaluation.overall_score.toFixed(0)}</span>
                    <span className="text-lg text-emerald-600">/100</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <ScoreBar label="Empathy" score={evaluation.empathy_score} color="bg-rose-500" />
                  <ScoreBar label="Accuracy" score={evaluation.accuracy_score} color="bg-blue-500" />
                  <ScoreBar label="Resolution" score={evaluation.resolution_score} color="bg-emerald-500" />
                  <ScoreBar label="Communication" score={evaluation.communication_score} color="bg-amber-500" />
                </div>
              </CardContent>
            </Card>

            {feedback && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <BrainCircuit className="h-5 w-5 text-teal-400" />
                    <span>AI Coaching Feedback</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Key Strengths</h3>
                    <ul className="space-y-2">
                      {feedback.strengths?.map((s: string, i: number) => (
                        <li key={i} className="flex items-start space-x-2">
                          <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
                          <span className="text-slate-300">{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-800">
                    <h3 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Suggested Improvements</h3>
                    <ul className="space-y-4">
                      {feedback.improvements?.map((imp: any, i: number) => (
                        <li key={i} className="space-y-1">
                          <p className="font-medium text-slate-200">{imp.area}</p>
                          <p className="text-sm text-slate-400">{imp.suggestion}</p>
                          {imp.example_rephrase && (
                            <div className="mt-2 bg-slate-800 p-3 rounded-md text-sm italic text-emerald-300 border-l-2 border-emerald-500">
                              " {imp.example_rephrase} "
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Column: Transcript */}
          <div className="lg:col-span-1">
            <Card className="h-full max-h-[800px] flex flex-col">
              <CardHeader className="flex-shrink-0">
                <CardTitle className="flex items-center space-x-2 text-base">
                  <MessageSquare className="h-4 w-4 text-slate-400" />
                  <span>Session Transcript</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto space-y-4 pr-2">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex flex-col ${msg.role === 'agent' ? 'items-end' : 'items-start'}`}>
                    <span className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 px-1">
                      {msg.role}
                    </span>
                    <div className={`text-sm p-3 rounded-xl max-w-[90%] ${
                      msg.role === 'agent' 
                        ? 'bg-slate-800 text-slate-200 rounded-tr-sm border border-slate-700' 
                        : 'bg-slate-900 text-slate-300 rounded-tl-sm border border-slate-800'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}

function ScoreBar({ label, score, color }: { label: string; score: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-slate-300">{label}</span>
        <span className="text-sm font-bold text-white">{score}/100</span>
      </div>
      <div className="w-full bg-slate-800 rounded-full h-2">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${score}%` }}
          transition={{ duration: 1 }}
          className={`h-2 rounded-full ${color}`}
        ></motion.div>
      </div>
    </div>
  );
}
