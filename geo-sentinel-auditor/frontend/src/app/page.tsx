"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, BusinessProfileData, BusinessProfileWithHistory } from "@/lib/api";
import { AuditForm } from "@/components/AuditForm";
import { AuditStatus } from "@/components/AuditStatus";
import { AuditResults } from "@/components/AuditResults";
import { AuditHistory } from "@/components/AuditHistory";

export default function Home() {
    const queryClient = useQueryClient();
    const [selectedBusiness, setSelectedBusiness] = useState<{ id: number; name: string } | null>(null);
    const [isMutationRunning, setIsMutationRunning] = useState(false);
    const [formInitialData, setFormInitialData] = useState<BusinessProfileData | null>(null);

    // Mutation to create a profile and trigger the audit pipeline
    const auditMutation = useMutation({
        mutationFn: async (data: BusinessProfileData) => {
            setIsMutationRunning(true);
            const profile = await api.createProfile(data);
            await api.triggerAudit(profile.id);
            return { id: profile.id, name: profile.name };
        },
        onSuccess: (data) => {
            setSelectedBusiness(data);
            // Invalidate history to show the new entry (initially with no score)
            queryClient.invalidateQueries({ queryKey: ["audit-history"] });
        },
        onSettled: () => {
            setIsMutationRunning(false);
        }
    });

    // Query to poll for audit results if we have a selected business ID
    const { data: audits } = useQuery({
        queryKey: ["audits", selectedBusiness?.id],
        queryFn: () => api.getAudits(selectedBusiness!.id),
        enabled: !!selectedBusiness?.id,
        refetchInterval: (query) => {
            // Keep polling every 3 seconds if we have no audits yet for this business
            if (query.state.data && query.state.data.length > 0) {
                // Once we have a result, invalidate history one last time to capture the final score
                queryClient.invalidateQueries({ queryKey: ["audit-history"] });
                return false; 
            }
            return 3000;
        }
    });

    const isAuditing = isMutationRunning || (!!selectedBusiness && (!audits || audits.length === 0));
    const report = audits && audits.length > 0 ? audits[0] : null;

    const handleStartAudit = (data: BusinessProfileData) => {
        setSelectedBusiness(null);
        auditMutation.mutate(data);
    };

    const handleSelectHistory = (profile: BusinessProfileWithHistory) => {
        setSelectedBusiness({ id: profile.id, name: profile.name });
        setFormInitialData({
            name: profile.name,
            industry: profile.industry,
            location: profile.location
        });
    };

    return (
        <main className="min-h-screen relative flex overflow-hidden">
            <div className="animated-bg"></div>

            {/* Feature 4: Audit History Sidebar */}
            <AuditHistory 
                onSelectProfile={handleSelectHistory} 
                selectedId={selectedBusiness?.id} 
            />

            <div className="flex-1 flex flex-col items-center justify-start p-6 overflow-y-auto pr-10">
                <header className="mb-10 text-center w-full max-w-5xl mt-8">
                    <h1 className="text-5xl font-extrabold mb-4 tracking-tight">
                        <span className="gradient-text">Geo-Sentinel</span> Auditor
                    </h1>
                    <p className="text-gray-400 text-lg">
                        Hyper-local SEO analysis powered by Agentic AI workflows.
                    </p>
                </header>

                <div className="grid lg:grid-cols-2 gap-10 w-full max-w-5xl">
                    {/* Left: Input Form Component */}
                    <div className="flex flex-col gap-6">
                        <AuditForm 
                            onSubmit={handleStartAudit} 
                            isLoading={isAuditing} 
                            initialData={formInitialData}
                        />
                        
                        <div className="glass-panel p-6">
                            <h3 className="text-xs uppercase tracking-widest text-indigo-400 font-bold mb-3">Live Agents Status</h3>
                            <div className="space-y-3">
                                <div className="flex items-center justify-between text-[10px] uppercase">
                                    <span className="text-gray-400">Data Collector</span>
                                    <span className={isAuditing ? "text-indigo-400 animate-pulse" : "text-green-500/50"}>{isAuditing ? "Searching..." : "Ready"}</span>
                                </div>
                                <div className="flex items-center justify-between text-[10px] uppercase">
                                    <span className="text-gray-400">Social Sentinel</span>
                                    <span className={isAuditing ? "text-accent animate-pulse" : "text-green-500/50"}>{isAuditing ? "Analyzing..." : "Ready"}</span>
                                </div>
                                <div className="flex items-center justify-between text-[10px] uppercase">
                                    <span className="text-gray-400">SEO Strategist</span>
                                    <span className={isAuditing ? "text-gray-600" : "text-green-500/50"}>{isAuditing ? "Waiting..." : "Ready"}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right: Results / Status Area */}
                    <div className="glass-panel p-8 min-h-[500px] flex flex-col max-h-[700px]">
                        {!isAuditing && !report && (
                            <div className="text-center text-gray-500 flex flex-col items-center justify-center h-full">
                                <div className="text-5xl mb-4 opacity-40">📍</div>
                                <p className="text-sm leading-relaxed max-w-[250px]">
                                    Enter your business details or select a previous audit from the history.
                                </p>
                            </div>
                        )}

                        {isAuditing && <AuditStatus />}

                        {!isAuditing && report && (
                            <AuditResults 
                                report={report} 
                                businessName={selectedBusiness?.name || "Business"} 
                            />
                        )}
                        
                        {auditMutation.isError && (
                            <div className="text-red-400 text-center flex flex-col justify-center h-full">
                                <p>Error connecting to the backend Agents.</p>
                                <p className="text-xs opacity-75 mt-2">Make sure `uvicorn main:app` is running!</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </main>
    );
}
