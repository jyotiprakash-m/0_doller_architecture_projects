'use client';

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Target, Shield, Zap, BrainCircuit } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-900 flex flex-col relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-emerald-600/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-teal-600/20 blur-[120px] pointer-events-none" />

      <header className="container mx-auto px-6 py-6 flex items-center justify-between relative z-10">
        <div className="flex items-center space-x-2">
          <Target className="h-8 w-8 text-emerald-500" />
          <span className="text-2xl font-bold text-white">SupportSim AI</span>
        </div>
        <div className="space-x-4">
          <Link href="/login">
            <Button variant="ghost">Log In</Button>
          </Link>
          <Link href="/register">
            <Button variant="primary">Get Started</Button>
          </Link>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center container mx-auto px-6 py-20 relative z-10 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-4xl"
        >
          <h1 className="text-5xl md:text-7xl font-extrabold text-white tracking-tight mb-8">
            Train Smarter.<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-teal-400">
              Support Better.
            </span>
          </h1>
          <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto leading-relaxed">
            AI-powered customer support training platform. Simulate realistic customer interactions, get evaluated, and receive personalized coaching—all powered by local LLMs at $0 inference cost.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-6">
            <Link href="/register">
              <Button size="lg" className="w-full sm:w-auto text-lg px-8">
                Start Training Now
              </Button>
            </Link>
            <Link href="/login">
              <Button variant="outline" size="lg" className="w-full sm:w-auto text-lg px-8">
                Sign In
              </Button>
            </Link>
          </div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-24 max-w-5xl"
        >
          <div className="glass-card p-6 rounded-2xl text-left">
            <div className="bg-emerald-500/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <BrainCircuit className="h-6 w-6 text-emerald-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Agentic Scenarios</h3>
            <p className="text-slate-400">Interact with AI personas that maintain emotional states and react dynamically to your responses.</p>
          </div>
          <div className="glass-card p-6 rounded-2xl text-left">
            <div className="bg-teal-500/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Shield className="h-6 w-6 text-teal-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">100% Private</h3>
            <p className="text-slate-400">Powered by Ollama and LlamaIndex. Your company knowledge base never leaves your machine.</p>
          </div>
          <div className="glass-card p-6 rounded-2xl text-left">
            <div className="bg-blue-500/20 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <Zap className="h-6 w-6 text-blue-400" />
            </div>
            <h3 className="text-xl font-bold text-white mb-2">Instant Feedback</h3>
            <p className="text-slate-400">Get detailed evaluations on empathy, accuracy, and communication immediately after every session.</p>
          </div>
        </motion.div>
      </main>
    </div>
  );
}
