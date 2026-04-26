'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, BookOpen, MessageSquare, LineChart, Target, LogOut, CreditCard } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/knowledge-base', label: 'Knowledge Base', icon: BookOpen },
    { href: '/scenarios', label: 'Scenarios', icon: Target },
    { href: '/training', label: 'Training', icon: MessageSquare },
    { href: '/review', label: 'Review', icon: LineChart },
    { href: '/billing', label: 'Billing', icon: CreditCard },
  ];

  return (
    <div className="w-64 border-r border-slate-800 bg-slate-900/50 backdrop-blur-md flex flex-col h-screen sticky top-0">
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Target className="h-6 w-6 text-emerald-500" />
          <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent">
            SupportSim AI
          </h1>
        </div>
        <p className="text-xs text-slate-500 mt-1">Agent Training Platform</p>
      </div>

      <div className="p-4 border-b border-slate-800">
        <div className="flex items-center justify-between">
          <div className="overflow-hidden">
            <p className="text-sm font-medium text-slate-200 truncate">
              {user?.full_name || user?.email?.split('@')[0]}
            </p>
            <p className="text-xs text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
        <div className="mt-3 inline-flex items-center rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
          💎 {user?.credits?.toFixed(1) || 0} Credits
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto p-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-emerald-600/10 text-emerald-400'
                  : 'text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button
          onClick={logout}
          className="flex w-full items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-400 hover:bg-red-500/10 hover:text-red-400 transition-colors"
        >
          <LogOut className="h-5 w-5" />
          <span>Logout</span>
        </button>
      </div>
    </div>
  );
}
