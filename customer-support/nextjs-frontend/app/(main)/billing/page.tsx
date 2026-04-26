'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { APIClient } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CreditCard, CheckCircle, Diamond, AlertCircle, Loader2 } from 'lucide-react';

export default function BillingPage() {
  const { user, updateUser } = useAuth();
  const searchParams = useSearchParams();
  const [isLoading, setIsLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    if (searchParams.get('success')) {
      setSuccessMessage('Subscription successful! Your credits have been added.');
      // Refresh user to get new credits
      APIClient.get<any>('/api/auth/me').then(updateUser).catch(console.error);
    }
    if (searchParams.get('canceled')) {
      setSuccessMessage('');
    }
  }, [searchParams, updateUser]);

  const handleSubscribe = async () => {
    setIsLoading(true);
    try {
      const { checkout_url } = await APIClient.post<any>('/api/billing/create-checkout-session');
      window.location.href = checkout_url;
    } catch (e: any) {
      alert(e.message || 'Failed to start checkout');
    } finally {
      setIsLoading(false);
    }
  };

  const handleManageSubscription = async () => {
    setIsLoading(true);
    try {
      const { portal_url } = await APIClient.post<any>('/api/billing/portal');
      window.location.href = portal_url;
    } catch (e: any) {
      alert(e.message || 'Failed to open billing portal');
    } finally {
      setIsLoading(false);
    }
  };

  const isSubscribed = user?.subscription_status === 'active';

  return (
    <div className="space-y-8">
      <div className="flex items-center space-x-3 mb-6">
        <CreditCard className="h-8 w-8 text-emerald-500" />
        <div>
          <h1 className="text-3xl font-bold text-slate-50">Billing & Pricing</h1>
          <p className="text-slate-400">Manage your subscription and credits.</p>
        </div>
      </div>

      {successMessage && (
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-3 rounded-lg flex items-center">
          <CheckCircle className="h-5 w-5 mr-2" />
          {successMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Current Status */}
        <Card className="lg:col-span-1 border-emerald-500/30">
          <CardHeader>
            <CardTitle className="text-xl">Current Balance</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between p-4 bg-slate-900/50 rounded-xl border border-slate-800">
              <div className="flex items-center space-x-3">
                <div className="bg-emerald-500/20 p-2 rounded-lg">
                  <Diamond className="h-6 w-6 text-emerald-500" />
                </div>
                <span className="font-medium text-slate-300">Credits</span>
              </div>
              <span className="text-3xl font-bold text-white">{user?.credits?.toFixed(1) || 0}</span>
            </div>

            <div>
              <h4 className="text-sm font-medium text-slate-400 mb-2">Plan Status</h4>
              {isSubscribed ? (
                <div className="space-y-3">
                  <Badge variant="success" className="text-sm px-3 py-1">Pro Tier - Active</Badge>
                  {user?.current_period_end && (
                    <p className="text-sm text-slate-400">
                      Renews on: {new Date(user.current_period_end).toLocaleDateString()}
                    </p>
                  )}
                  <Button variant="outline" className="w-full mt-4" onClick={handleManageSubscription} isLoading={isLoading}>
                    Manage Subscription
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <Badge variant="default" className="text-sm px-3 py-1">Free Tier</Badge>
                  <p className="text-sm text-slate-400">
                    You are currently on the free tier. Upgrade to get 1000 credits per month.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Pricing Tier */}
        <Card className="lg:col-span-2 relative overflow-hidden">
          {!isSubscribed && (
            <div className="absolute top-0 right-0 bg-emerald-500 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
              RECOMMENDED
            </div>
          )}
          <CardHeader>
            <CardTitle className="text-2xl">SupportSim Pro</CardTitle>
            <CardDescription>Everything you need to train your support agents at scale.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-baseline mb-6">
              <span className="text-5xl font-extrabold text-white">$15</span>
              <span className="text-xl text-slate-400 ml-2">/ month</span>
            </div>

            <ul className="space-y-4 mb-8">
              <li className="flex items-start">
                <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0 mr-3" />
                <span className="text-slate-300"><strong className="text-white">1000 Credits</strong> per month (Good for ~1000 training sessions)</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0 mr-3" />
                <span className="text-slate-300">Unlimited Knowledge Base uploads</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0 mr-3" />
                <span className="text-slate-300">Advanced AI Coaching and Performance Analytics</span>
              </li>
              <li className="flex items-start">
                <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0 mr-3" />
                <span className="text-slate-300">Auto-generate scenarios from your docs</span>
              </li>
            </ul>

            <Button 
              size="lg" 
              className="w-full text-lg" 
              onClick={isSubscribed ? handleManageSubscription : handleSubscribe}
              isLoading={isLoading}
              variant={isSubscribed ? "secondary" : "primary"}
            >
              {isSubscribed ? "Manage Plan" : "Upgrade to Pro"}
            </Button>
            
            {!isSubscribed && (
              <p className="text-center text-xs text-slate-500 mt-4 flex items-center justify-center">
                <AlertCircle className="h-3 w-3 mr-1" />
                Secure payment processing by Stripe
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
