"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import SchemaEditor from "@/components/SchemaEditor";
import GenerationProgress from "@/components/GenerationProgress";
import DataPreview from "@/components/DataPreview";
import ExportPanel from "@/components/ExportPanel";

const API_BASE = "http://localhost:8000";

interface JobData {
  id: string;
  status: string;
  rows_generated: number;
  row_count: number;
  table_count: number;
  tables_completed: number;
  current_table: string | null;
  error_message: string | null;
}

interface TablePreview {
  name: string;
  columns: string[];
  rows: (string | null)[][];
  totalRows: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export default function GeneratePage() {
  const router = useRouter();

  // Auth
  const [token, setToken] = useState("");

  // Schema & Project
  const [schemaSQL, setSchemaSQL] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");

  // Generation config
  const [rowCount, setRowCount] = useState(1000);
  const [locale, setLocale] = useState("en_US");

  // State machine: idle → creating → generating → completed
  const [step, setStep] = useState<
    "idle" | "creating" | "generating" | "completed"
  >("idle");

  // Job tracking
  const [currentJob, setCurrentJob] = useState<JobData | null>(null);
  const [schemaProjectId, setSchemaProjectId] = useState<string | null>(null);

  // Data preview
  const [previewTables, setPreviewTables] = useState<TablePreview[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Tables list
  const [generatedTables, setGeneratedTables] = useState<string[]>([]);

  // Error
  const [error, setError] = useState("");

  useEffect(() => {
    const t = localStorage.getItem("token");
    if (!t) {
      router.push("/");
      return;
    }
    setToken(t);
  }, [router]);

  // Poll job status
  useEffect(() => {
    if (!currentJob || !token) return;
    if (
      currentJob.status === "completed" ||
      currentJob.status === "failed"
    )
      return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(
          `${API_BASE}/api/generate/${currentJob.id}/status`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (res.ok) {
          const job: JobData = await res.json();
          setCurrentJob(job);

          if (job.status === "completed") {
            setStep("completed");
            clearInterval(interval);
            loadPreview(job.id);
          } else if (job.status === "failed") {
            clearInterval(interval);
          }
        }
      } catch (err) {
        console.error("Status poll error:", err);
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [currentJob, token]);

  const loadPreview = async (jobId: string) => {
    setPreviewLoading(true);
    try {
      // Get tables
      const tablesRes = await fetch(
        `${API_BASE}/api/generate/${jobId}/tables`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (!tablesRes.ok) return;
      const tablesData = await tablesRes.json();
      const tableNames = tablesData.tables.map((t: any) => t.name);
      setGeneratedTables(tableNames);

      // Load preview for each table
      const previews: TablePreview[] = [];
      for (const table of tablesData.tables) {
        const previewRes = await fetch(
          `${API_BASE}/api/generate/${jobId}/preview?table_name=${encodeURIComponent(
            table.name
          )}&page=1&page_size=50`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (previewRes.ok) {
          const pd = await previewRes.json();
          previews.push({
            name: pd.table_name,
            columns: pd.columns,
            rows: pd.rows,
            totalRows: pd.total_rows,
            page: pd.page,
            pageSize: pd.page_size,
            totalPages: pd.total_pages,
          });
        }
      }
      setPreviewTables(previews);
    } catch (err) {
      console.error("Preview load error:", err);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handlePageChange = async (tableName: string, page: number) => {
    if (!currentJob) return;
    setPreviewLoading(true);
    try {
      const res = await fetch(
        `${API_BASE}/api/generate/${currentJob.id}/preview?table_name=${encodeURIComponent(
          tableName
        )}&page=${page}&page_size=50`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      if (res.ok) {
        const pd = await res.json();
        setPreviewTables((prev) =>
          prev.map((t) =>
            t.name === tableName
              ? {
                  ...t,
                  rows: pd.rows,
                  page: pd.page,
                  totalPages: pd.total_pages,
                }
              : t
          )
        );
      }
    } catch (err) {
      console.error("Page change error:", err);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleGenerate = async () => {
    setError("");

    if (!schemaSQL.trim()) {
      setError("Please provide a SQL schema");
      return;
    }
    if (!projectName.trim()) {
      setError("Please provide a project name");
      return;
    }

    setStep("creating");

    try {
      // Step 1: Create schema project
      const schemaRes = await fetch(`${API_BASE}/api/schemas`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: projectName,
          description: projectDescription,
          sql_ddl: schemaSQL,
        }),
      });

      if (!schemaRes.ok) {
        const d = await schemaRes.json();
        throw new Error(d.detail || "Failed to create schema project");
      }

      const schemaProject = await schemaRes.json();
      setSchemaProjectId(schemaProject.id);

      // Step 2: Trigger generation
      setStep("generating");
      const genRes = await fetch(
        `${API_BASE}/api/generate/${schemaProject.id}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            row_count: rowCount,
            locale: locale,
          }),
        }
      );

      if (!genRes.ok) {
        const d = await genRes.json();
        throw new Error(d.detail || "Failed to start generation");
      }

      const job: JobData = await genRes.json();
      setCurrentJob(job);
    } catch (err: any) {
      setError(err.message);
      setStep("idle");
    }
  };

  const handleReset = () => {
    setStep("idle");
    setCurrentJob(null);
    setPreviewTables([]);
    setGeneratedTables([]);
    setError("");
    setSchemaSQL("");
    setProjectName("");
    setProjectDescription("");
  };

  const rowPresets = [100, 1000, 10000, 50000, 100000, 500000];

  return (
    <>
      <Navbar />
      <main
        style={{
          flex: 1,
          maxWidth: "1100px",
          margin: "0 auto",
          padding: "2rem 1.5rem",
          width: "100%",
        }}
      >
        {/* Header */}
        <div className="animate-fade-in" style={{ marginBottom: "2rem" }}>
          <h1 style={{ marginBottom: "0.25rem" }}>
            <span style={{ color: "var(--accent-primary)" }}>⚡</span> Generate
            Synthetic Data
          </h1>
          <p style={{ fontSize: "0.9375rem" }}>
            Paste your SQL DDL, configure row counts, and generate
            GDPR/CCPA-safe synthetic datasets in seconds.
          </p>
        </div>

        {step === "idle" && (
          <div
            className="animate-slide-up"
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "1.5rem",
            }}
          >
            {/* Project info */}
            <div className="card">
              <h3
                style={{
                  marginBottom: "1rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span>📋</span> Project Info
              </h3>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "1rem",
                }}
              >
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                      marginBottom: "0.375rem",
                      fontWeight: 500,
                    }}
                  >
                    Project Name *
                  </label>
                  <input
                    className="input"
                    placeholder="e.g., E-Commerce Test Data"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                  />
                </div>
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                      marginBottom: "0.375rem",
                      fontWeight: 500,
                    }}
                  >
                    Description
                  </label>
                  <input
                    className="input"
                    placeholder="Optional description..."
                    value={projectDescription}
                    onChange={(e) => setProjectDescription(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Schema editor */}
            <div className="card">
              <h3
                style={{
                  marginBottom: "1rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span>🗃️</span> Database Schema
              </h3>
              <SchemaEditor value={schemaSQL} onChange={setSchemaSQL} />
            </div>

            {/* Generation config */}
            <div className="card">
              <h3
                style={{
                  marginBottom: "1rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span>⚙️</span> Generation Config
              </h3>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "1rem",
                }}
              >
                {/* Row count */}
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                      marginBottom: "0.5rem",
                      fontWeight: 500,
                    }}
                  >
                    Rows per table
                  </label>
                  <div
                    style={{
                      display: "flex",
                      gap: "0.5rem",
                      flexWrap: "wrap",
                      alignItems: "center",
                    }}
                  >
                    {rowPresets.map((preset) => (
                      <button
                        key={preset}
                        onClick={() => setRowCount(preset)}
                        style={{
                          padding: "0.5rem 1rem",
                          fontSize: "0.8125rem",
                          fontWeight: 600,
                          fontFamily: "var(--font-geist-mono)",
                          borderRadius: "var(--radius-md)",
                          border:
                            rowCount === preset
                              ? "1px solid var(--accent-primary)"
                              : "1px solid var(--border-default)",
                          background:
                            rowCount === preset
                              ? "var(--accent-glow)"
                              : "var(--bg-primary)",
                          color:
                            rowCount === preset
                              ? "var(--accent-primary-hover)"
                              : "var(--text-secondary)",
                          cursor: "pointer",
                          transition: "all 150ms ease",
                        }}
                      >
                        {preset >= 1000
                          ? `${preset / 1000}K`
                          : preset.toString()}
                      </button>
                    ))}
                    <input
                      className="input"
                      type="number"
                      min={1}
                      max={1000000}
                      value={rowCount}
                      onChange={(e) =>
                        setRowCount(
                          Math.min(1000000, Math.max(1, parseInt(e.target.value) || 1))
                        )
                      }
                      style={{ width: "140px" }}
                      placeholder="Custom..."
                    />
                  </div>
                </div>

                {/* Locale */}
                <div>
                  <label
                    style={{
                      display: "block",
                      fontSize: "0.75rem",
                      color: "var(--text-muted)",
                      marginBottom: "0.375rem",
                      fontWeight: 500,
                    }}
                  >
                    Data Locale
                  </label>
                  <select
                    className="input"
                    value={locale}
                    onChange={(e) => setLocale(e.target.value)}
                    style={{ maxWidth: "220px", cursor: "pointer" }}
                  >
                    <option value="en_US">🇺🇸 English (US)</option>
                    <option value="en_GB">🇬🇧 English (UK)</option>
                    <option value="de_DE">🇩🇪 German</option>
                    <option value="fr_FR">🇫🇷 French</option>
                    <option value="ja_JP">🇯🇵 Japanese</option>
                    <option value="ko_KR">🇰🇷 Korean</option>
                    <option value="zh_CN">🇨🇳 Chinese</option>
                    <option value="hi_IN">🇮🇳 Hindi</option>
                    <option value="es_ES">🇪🇸 Spanish</option>
                    <option value="pt_BR">🇧🇷 Portuguese (BR)</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Error */}
            {error && (
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
                {error}
              </div>
            )}

            {/* Generate button */}
            <button
              className="btn-primary"
              onClick={handleGenerate}
              style={{
                width: "100%",
                padding: "1rem",
                fontSize: "1rem",
              }}
            >
              <span>⚡</span> Generate {rowCount.toLocaleString()} Rows Per
              Table
            </button>
          </div>
        )}

        {/* Creating / Generating state */}
        {(step === "creating" || step === "generating") && currentJob && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "1.5rem",
            }}
          >
            <GenerationProgress
              status={currentJob.status}
              rowsGenerated={currentJob.rows_generated}
              totalRows={currentJob.row_count * (currentJob.table_count || 1)}
              tablesCompleted={currentJob.tables_completed}
              totalTables={currentJob.table_count}
              currentTable={currentJob.current_table}
              errorMessage={currentJob.error_message}
            />
          </div>
        )}

        {step === "creating" && !currentJob && (
          <div
            className="card-glow"
            style={{
              textAlign: "center",
              padding: "3rem",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "1rem",
            }}
          >
            <div className="spinner" style={{ width: "32px", height: "32px" }} />
            <div>
              <h3>Creating Schema Project...</h3>
              <p style={{ fontSize: "0.875rem" }}>
                AI is analyzing your database schema...
              </p>
            </div>
          </div>
        )}

        {/* Completed state */}
        {step === "completed" && currentJob && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "1.5rem",
            }}
          >
            {/* Final progress (completed) */}
            <GenerationProgress
              status={currentJob.status}
              rowsGenerated={currentJob.rows_generated}
              totalRows={currentJob.row_count * (currentJob.table_count || 1)}
              tablesCompleted={currentJob.tables_completed}
              totalTables={currentJob.table_count}
              currentTable={currentJob.current_table}
              errorMessage={currentJob.error_message}
            />

            {/* Data preview */}
            <div className="card">
              <h3
                style={{
                  marginBottom: "1rem",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                }}
              >
                <span>📊</span> Data Preview
              </h3>
              <DataPreview
                tables={previewTables}
                onPageChange={handlePageChange}
                loading={previewLoading}
              />
            </div>

            {/* Export panel */}
            <ExportPanel
              jobId={currentJob.id}
              tables={generatedTables}
              apiBase={API_BASE}
              token={token}
            />

            {/* Reset button */}
            <button
              className="btn-secondary"
              onClick={handleReset}
              style={{ width: "100%", padding: "0.875rem" }}
            >
              ← Generate Another Dataset
            </button>
          </div>
        )}
      </main>
    </>
  );
}
