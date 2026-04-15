export function AuditStatus() {
    return (
        <div className="text-center space-y-5 flex flex-col items-center justify-center h-full">
            <div className="loader shadow-[0_0_20px_rgba(167,139,250,0.4)]" style={{ width: '50px', height: '50px', borderWidth: '4px' }}></div>
            <p className="text-indigo-300 text-sm font-medium animate-pulse tracking-wide uppercase">
                Agents are analyzing local search data...
            </p>
        </div>
    );
}
