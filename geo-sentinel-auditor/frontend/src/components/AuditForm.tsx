import { useState, useEffect } from "react";
import { BusinessProfileData } from "@/lib/api";

type Props = {
    onSubmit: (data: BusinessProfileData) => void;
    isLoading: boolean;
    initialData?: BusinessProfileData | null;
};

export function AuditForm({ onSubmit, isLoading, initialData }: Props) {
    const [businessName, setBusinessName] = useState("");
    const [industry, setIndustry] = useState("");
    const [location, setLocation] = useState("");

    useEffect(() => {
        if (initialData) {
            setBusinessName(initialData.name);
            setIndustry(initialData.industry);
            setLocation(initialData.location);
        }
    }, [initialData]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({
            name: businessName,
            industry,
            location
        });
    };

    return (
        <div className="glass-panel p-8">
            <h2 className="text-xl font-bold mb-6 border-b border-gray-700/50 pb-3">Target Profile</h2>
            <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                    <label className="block text-sm text-gray-400 mb-2">Business Name</label>
                    <input 
                        required 
                        type="text" 
                        value={businessName} 
                        onChange={(e) => setBusinessName(e.target.value)} 
                        className="glass-input w-full p-3 rounded-lg text-sm" 
                        placeholder="e.g. Joe's Coffee" 
                    />
                </div>
                <div>
                    <label className="block text-sm text-gray-400 mb-2">Industry</label>
                    <input 
                        required 
                        type="text" 
                        value={industry} 
                        onChange={(e) => setIndustry(e.target.value)} 
                        className="glass-input w-full p-3 rounded-lg text-sm" 
                        placeholder="e.g. Coffee Shop" 
                    />
                </div>
                <div>
                    <label className="block text-sm text-gray-400 mb-2">Location</label>
                    <input 
                        required 
                        type="text" 
                        value={location} 
                        onChange={(e) => setLocation(e.target.value)} 
                        className="glass-input w-full p-3 rounded-lg text-sm" 
                        placeholder="e.g. Austin, TX" 
                    />
                </div>
                <div className="pt-2">
                    <button 
                        disabled={isLoading} 
                        type="submit" 
                        className="btn-primary w-full py-4 rounded-lg font-bold flex items-center justify-center gap-2 text-sm uppercase tracking-wide"
                    >
                        {isLoading ? <div className="loader"></div> : "Start Agentic Audit"}
                    </button>
                </div>
            </form>
        </div>
    );
}
