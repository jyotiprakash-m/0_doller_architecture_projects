"use client";

interface GenerationProgressProps {
  status: string;
  rowsGenerated: number;
  totalRows: number;
  tablesCompleted: number;
  totalTables: number;
  currentTable: string | null;
  errorMessage: string | null;
}

export default function GenerationProgress({
  status,
  rowsGenerated,
  totalRows,
  tablesCompleted,
  totalTables,
  currentTable,
  errorMessage,
}: GenerationProgressProps) {
  const progress = totalRows > 0 ? (rowsGenerated / totalRows) * 100 : 0;

  const statusConfig: Record<string, { label: string; color: string; bgColor: string; icon: string }> = {
    pending: { label: "Queued", color: "var(--text-muted)", bgColor: "rgba(107,107,128,0.1)", icon: "⏳" },
    analyzing: { label: "Analyzing Schema", color: "var(--info)", bgColor: "var(--info-bg)", icon: "🔍" },
    generating: { label: "Generating Data", color: "var(--cyan)", bgColor: "var(--cyan-bg)", icon: "⚡" },
    completed: { label: "Completed", color: "var(--success)", bgColor: "var(--success-bg)", icon: "✓" },
    failed: { label: "Failed", color: "var(--error)", bgColor: "var(--error-bg)", icon: "✗" },
  };

  const cfg = statusConfig[status] || statusConfig.pending;

  return (
    <div
      className="card-glow animate-fade-in"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "1.25rem",
      }}
    >
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {status === "generating" || status === "analyzing" ? (
            <div className="spinner" />
          ) : (
            <span style={{ fontSize: "1.25rem" }}>{cfg.icon}</span>
          )}
          <div>
            <h3 style={{ fontSize: "1rem", margin: 0 }}>Generation Progress</h3>
            <p style={{ fontSize: "0.8125rem", margin: 0, color: "var(--text-muted)" }}>
              {currentTable
                ? `Processing: ${currentTable}`
                : status === "completed"
                ? "All tables generated successfully"
                : status === "analyzing"
                ? "AI is analyzing your schema..."
                : "Waiting to start..."}
            </p>
          </div>
        </div>

        <span
          className="badge"
          style={{
            background: cfg.bgColor,
            color: cfg.color,
          }}
        >
          {cfg.label}
        </span>
      </div>

      {/* Progress bar */}
      <div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginBottom: "0.5rem",
            fontSize: "0.75rem",
            color: "var(--text-secondary)",
          }}
        >
          <span>{rowsGenerated.toLocaleString()} rows generated</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-bar-fill"
            style={{
              width: `${Math.min(progress, 100)}%`,
              ...(status === "generating"
                ? { animation: "pulse-glow 2s ease-in-out infinite" }
                : {}),
            }}
          />
        </div>
      </div>

      {/* Stats grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "1rem",
        }}
      >
        <div
          style={{
            padding: "0.75rem",
            background: "var(--bg-primary)",
            borderRadius: "var(--radius-md)",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--accent-primary-hover)",
              fontFamily: "var(--font-geist-mono)",
            }}
          >
            {rowsGenerated.toLocaleString()}
          </div>
          <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            Rows Generated
          </div>
        </div>
        <div
          style={{
            padding: "0.75rem",
            background: "var(--bg-primary)",
            borderRadius: "var(--radius-md)",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--cyan)",
              fontFamily: "var(--font-geist-mono)",
            }}
          >
            {tablesCompleted}/{totalTables}
          </div>
          <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            Tables Done
          </div>
        </div>
        <div
          style={{
            padding: "0.75rem",
            background: "var(--bg-primary)",
            borderRadius: "var(--radius-md)",
            textAlign: "center",
          }}
        >
          <div
            style={{
              fontSize: "1.5rem",
              fontWeight: 700,
              color: "var(--success)",
              fontFamily: "var(--font-geist-mono)",
            }}
          >
            {totalRows > 0
              ? `${(rowsGenerated / totalRows * 100).toFixed(0)}%`
              : "—"}
          </div>
          <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)", marginTop: "0.25rem" }}>
            Progress
          </div>
        </div>
      </div>

      {/* Error display */}
      {errorMessage && (
        <div
          style={{
            padding: "0.75rem 1rem",
            background: "var(--error-bg)",
            border: "1px solid rgba(248,113,113,0.2)",
            borderRadius: "var(--radius-md)",
            color: "var(--error)",
            fontSize: "0.8125rem",
          }}
        >
          <strong>Error:</strong> {errorMessage}
        </div>
      )}
    </div>
  );
}
