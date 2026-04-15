import { useQuery } from "@tanstack/react-query";
import { api, BusinessProfileWithHistory } from "@/lib/api";

type Props = {
  onSelectProfile: (profile: BusinessProfileWithHistory) => void;
  selectedId?: number | null;
};

export function AuditHistory({ onSelectProfile, selectedId }: Props) {
  const { data: history, isLoading } = useQuery({
    queryKey: ["audit-history"],
    queryFn: api.getHistory,
    refetchInterval: 10000, // Refresh historyEvery 10 seconds
  });

  return (
    <div className="flex flex-col h-full bg-black/20 border-r border-white/5 w-64">
      <div className="p-4 border-b border-white/10 glass-panel !rounded-none !border-0 !bg-white/5">
        <h2 className="text-sm font-bold uppercase tracking-widest text-gray-400">History</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {isLoading && (
          <div className="p-8 text-center">
            <div className="loader mx-auto mb-2 w-4 h-4"></div>
            <p className="text-[10px] text-gray-600 uppercase">Loading...</p>
          </div>
        )}

        {!isLoading && history?.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-[10px] text-gray-600 uppercase italic">No audits yet</p>
          </div>
        )}

        <div className="flex flex-col p-2 gap-1">
          {history?.map((profile) => (
            <button
              key={profile.id}
              onClick={() => onSelectProfile(profile)}
              className={`text-left p-3 rounded-lg transition-all border border-transparent hover:bg-white/5 ${
                selectedId === profile.id ? "bg-white/10 border-indigo-500/30" : ""
              }`}
            >
              <p className="text-xs font-bold text-gray-200 truncate">{profile.name}</p>
              <div className="flex justify-between items-center mt-1">
                <p className="text-[9px] text-gray-500 truncate">{profile.location}</p>
                <span className="text-[9px] font-bold text-indigo-400 bg-indigo-400/10 px-1.5 py-0.5 rounded">
                  {profile.latest_audit_score}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
