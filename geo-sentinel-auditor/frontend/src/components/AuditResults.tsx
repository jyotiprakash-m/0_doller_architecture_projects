import { AuditReportResponse, api } from "@/lib/api";
import { SEORadarChart } from "./SEORadarChart";
import { useState } from "react";

type Props = {
    report: AuditReportResponse;
    businessName: string;
};

export function AuditResults({ report, businessName }: Props) {
    const [isDownloading, setIsDownloading] = useState(false);
    const steps = report.actionable_steps.split('\n').filter(s => s.trim().length > 0);

    const handleDownload = async () => {
        setIsDownloading(true);
        try {
            await api.downloadReport(report.id, businessName);
        } catch (error) {
            console.error(error);
            alert("Failed to download report.");
        } finally {
            setIsDownloading(false);
        }
    };

    return (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 h-full overflow-y-auto pr-2 custom-scrollbar">
            <div className="flex items-center justify-between mb-2 border-b border-gray-700/50 pb-4">
                <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-100 to-gray-400">
                    Audit Results
                </h2>
                <div className="flex items-center justify-center w-14 h-14 rounded-full border-2 border-indigo-500/50 text-xl font-bold bg-indigo-500/10 text-indigo-300 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                    {report.overall_score}
                </div>
            </div>

            <SEORadarChart data={{
                overall: report.overall_score,
                google: report.google_presence_score,
                content: report.content_score,
                social: report.social_score
            }} />

            <div className="flex justify-end mb-8">
                <button 
                    onClick={handleDownload}
                    disabled={isDownloading}
                    className="btn-primary px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider flex items-center gap-2"
                >
                    {isDownloading ? <div className="loader w-3 h-3"></div> : "📥 Download PDF report"}
                </button>
            </div>

            <div className="mb-8">
                <h3 className="text-xs uppercase tracking-wider text-indigo-400 mb-3 font-bold">Competitor Strategy</h3>
                <p className="text-gray-300 text-sm leading-relaxed bg-black/20 p-4 rounded-lg border border-white/5">
                    {report.competitor_analysis}
                </p>
            </div>

            <div className="mb-8">
                <h3 className="text-xs uppercase tracking-wider text-accent mb-3 font-bold">Social & Reputation</h3>
                <p className="text-gray-300 text-sm leading-relaxed bg-black/20 p-4 rounded-lg border border-white/5">
                    {report.social_analysis}
                </p>
            </div>

            <div className="mb-4">
                <h3 className="text-xs uppercase tracking-wider text-indigo-400 mb-4 font-bold">Action Plan</h3>
                <ul className="space-y-3">
                    {steps.map((step, i) => (
                        <li key={i} className="flex gap-3 items-start text-sm text-gray-200 bg-white/5 p-4 rounded-lg border border-white/5 shadow-sm">
                            <span className="text-indigo-400 mt-0.5">⚡</span>
                            <span className="leading-snug">{step.replace(/^[-*]\s*/, '')}</span>
                        </li>
                    ))}
                </ul>
            </div>
        </div>
    );
}
