"use client";

interface ExportPanelProps {
  jobId: string;
  tables: string[];
  apiBase: string;
  token: string;
}

export default function ExportPanel({
  jobId,
  tables,
  apiBase,
  token,
}: ExportPanelProps) {
  const formats = [
    {
      id: "csv",
      label: "CSV",
      icon: "📄",
      desc: "Comma-separated values — universal compatibility",
      color: "var(--success)",
    },
    {
      id: "sql",
      label: "SQL",
      icon: "🗃️",
      desc: "INSERT statements — ready for any SQL database",
      color: "var(--info)",
    },
    {
      id: "json",
      label: "JSON",
      icon: "{ }",
      desc: "JSON array — perfect for APIs and NoSQL",
      color: "var(--warning)",
    },
  ];

  const handleExport = (format: string, tableName: string) => {
    const url = `${apiBase}/api/export/${jobId}/${format}?table_name=${encodeURIComponent(tableName)}`;
    // Open in new tab to trigger download
    const link = document.createElement("a");
    link.href = url;
    link.target = "_blank";
    // For auth, we'll use fetch + blob
    fetch(url, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => {
        if (!res.ok) throw new Error("Export failed");
        return res.blob();
      })
      .then((blob) => {
        const ext = format === "json" ? "json" : format;
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = `${tableName}.${ext}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
      })
      .catch((err) => {
        console.error("Export error:", err);
        alert("Export failed. Please try again.");
      });
  };

  return (
    <div className="card animate-fade-in">
      <h3 style={{ marginBottom: "1rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
        <span>📦</span> Export Data
      </h3>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "0.75rem",
          marginBottom: "1.25rem",
        }}
      >
        {formats.map((fmt) => (
          <div
            key={fmt.id}
            style={{
              padding: "1rem",
              background: "var(--bg-primary)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-subtle)",
              textAlign: "center",
            }}
          >
            <div
              style={{
                fontSize: "1.5rem",
                marginBottom: "0.375rem",
              }}
            >
              {fmt.icon}
            </div>
            <div
              style={{
                fontWeight: 600,
                fontSize: "0.875rem",
                color: fmt.color,
                marginBottom: "0.25rem",
              }}
            >
              {fmt.label}
            </div>
            <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
              {fmt.desc}
            </div>
          </div>
        ))}
      </div>

      {/* Per-table export buttons */}
      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {tables.map((tableName) => (
          <div
            key={tableName}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "0.75rem 1rem",
              background: "var(--bg-primary)",
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border-subtle)",
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-geist-mono)",
                fontSize: "0.8125rem",
                fontWeight: 500,
              }}
            >
              {tableName}
            </span>
            <div style={{ display: "flex", gap: "0.375rem" }}>
              {formats.map((fmt) => (
                <button
                  key={fmt.id}
                  className="btn-ghost"
                  onClick={() => handleExport(fmt.id, tableName)}
                  style={{
                    fontSize: "0.6875rem",
                    padding: "0.375rem 0.625rem",
                    border: "1px solid var(--border-default)",
                    borderRadius: "var(--radius-sm)",
                  }}
                >
                  {fmt.label}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
