"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import Navbar from "@/components/Navbar";

const API_BASE = "http://localhost:8000";

interface DashboardStats {
  total_projects: number;
  total_jobs: number;
  total_rows_generated: number;
  completed_jobs: number;
  user_credits: number;
  recent_projects: any[];
  recent_jobs: any[];
}

export default function Home() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [isRegistering, setIsRegistering] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; msg: string } | null>(null);
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      setIsLoggedIn(true);
      fetchDashboard(token);
    }
    // Handle Stripe redirect callbacks
    const payment = searchParams.get("payment");
    if (payment === "success") {
      setToast({ type: "success", msg: "🎉 Payment successful! Credits have been added to your account." });
      setTimeout(() => setToast(null), 6000);
    } else if (payment === "cancel") {
      setToast({ type: "error", msg: "Payment was cancelled. No charge was made." });
      setTimeout(() => setToast(null), 4000);
    }
  }, [searchParams]);

  const fetchDashboard = async (token: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/dashboard`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      } else if (res.status === 401) {
        localStorage.removeItem("token");
        setIsLoggedIn(false);
      }
    } catch (err) {
      console.error("Dashboard fetch failed:", err);
    }
  };

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegistering) {
        // Register first
        const regRes = await fetch(`${API_BASE}/api/auth/register`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(loginForm),
        });
        if (!regRes.ok) {
          const d = await regRes.json();
          throw new Error(d.detail || "Registration failed");
        }
      }

      // Login
      const formData = new URLSearchParams();
      formData.append("username", loginForm.email);
      formData.append("password", loginForm.password);

      const loginRes = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData.toString(),
      });

      if (!loginRes.ok) {
        const d = await loginRes.json();
        throw new Error(d.detail || "Login failed");
      }

      const data = await loginRes.json();
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("userId", data.user_id);
      setIsLoggedIn(true);
      fetchDashboard(data.access_token);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ---- Auth Screen ----
  if (!isLoggedIn) {
    return (
      <>
        <Navbar />
        <main
          style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "2rem",
          }}
        >
          <div
            className="animate-slide-up"
            style={{
              width: "100%",
              maxWidth: "420px",
              display: "flex",
              flexDirection: "column",
              gap: "2rem",
            }}
          >
            {/* Hero text */}
            <div style={{ textAlign: "center" }}>
              <div
                style={{
                  width: "56px",
                  height: "56px",
                  borderRadius: "16px",
                  background: "var(--accent-gradient)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1.5rem",
                  fontWeight: 800,
                  color: "white",
                  margin: "0 auto 1rem",
                  boxShadow: "0 4px 20px rgba(99,102,241,0.4)",
                }}
              >
                S
              </div>
              <h1 style={{ marginBottom: "0.5rem" }}>
                Synth<span style={{ color: "var(--accent-primary)" }}>Forge</span>
              </h1>
              <p style={{ fontSize: "0.9375rem" }}>
                Generate realistic synthetic datasets for development & testing.
                <br />
                <span style={{ color: "var(--text-muted)" }}>
                  Privacy-first. Local AI. $0 cost.
                </span>
              </p>
            </div>

            {/* Auth form */}
            <form
              onSubmit={handleAuth}
              className="card"
              style={{ display: "flex", flexDirection: "column", gap: "1rem" }}
            >
              <h3 style={{ textAlign: "center" }}>
                {isRegistering ? "Create Account" : "Sign In"}
              </h3>

              <input
                className="input"
                type="email"
                placeholder="Email address"
                value={loginForm.email}
                onChange={(e) =>
                  setLoginForm({ ...loginForm, email: e.target.value })
                }
                required
              />

              <input
                className="input"
                type="password"
                placeholder="Password"
                value={loginForm.password}
                onChange={(e) =>
                  setLoginForm({ ...loginForm, password: e.target.value })
                }
                required
              />

              {error && (
                <div
                  style={{
                    padding: "0.5rem 0.75rem",
                    background: "var(--error-bg)",
                    borderRadius: "var(--radius-sm)",
                    color: "var(--error)",
                    fontSize: "0.8125rem",
                  }}
                >
                  {error}
                </div>
              )}

              <button
                className="btn-primary"
                type="submit"
                disabled={loading}
                style={{ width: "100%", padding: "0.875rem" }}
              >
                {loading ? (
                  <div className="spinner" />
                ) : isRegistering ? (
                  "Create Account"
                ) : (
                  "Sign In"
                )}
              </button>

              <button
                type="button"
                className="btn-ghost"
                onClick={() => {
                  setIsRegistering(!isRegistering);
                  setError("");
                }}
                style={{ width: "100%", fontSize: "0.8125rem" }}
              >
                {isRegistering
                  ? "Already have an account? Sign in"
                  : "Need an account? Register"}
              </button>
            </form>

            {/* Feature badges */}
            <div
              style={{
                display: "flex",
                justifyContent: "center",
                gap: "0.5rem",
                flexWrap: "wrap",
              }}
            >
              {["GDPR Safe", "Local AI", "DuckDB", "Faker Engine", "$0 Cost"].map(
                (tag) => (
                  <span
                    key={tag}
                    className="badge badge-accent"
                    style={{ fontSize: "0.625rem" }}
                  >
                    {tag}
                  </span>
                )
              )}
            </div>
          </div>
        </main>
      </>
    );
  }

  // ---- Dashboard ----
  const statCards = [
    {
      label: "Schema Projects",
      value: stats?.total_projects ?? 0,
      icon: "🗂️",
      color: "var(--accent-primary-hover)",
    },
    {
      label: "Generation Jobs",
      value: stats?.total_jobs ?? 0,
      icon: "⚡",
      color: "var(--cyan)",
    },
    {
      label: "Rows Generated",
      value: stats?.total_rows_generated?.toLocaleString() ?? "0",
      icon: "📊",
      color: "var(--success)",
    },
    {
      label: "Credits Left",
      value: stats?.user_credits ?? 0,
      icon: "💎",
      color: "var(--warning)",
    },
  ];

  return (
    <>
      <Navbar />
      <main
        style={{
          flex: 1,
          maxWidth: "1280px",
          margin: "0 auto",
          padding: "2rem 1.5rem",
          width: "100%",
        }}
      >
        {/* Header */}
        <div
          className="animate-fade-in"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "2rem",
          }}
        >
          <div>
            <h1 style={{ marginBottom: "0.25rem" }}>Dashboard</h1>
            <p style={{ fontSize: "0.875rem" }}>
              Generate privacy-compliant synthetic datasets with local AI.
            </p>
          </div>
          <Link href="/generate" className="btn-primary">
            <span>⚡</span> New Generation
          </Link>
        </div>

        {/* Stats grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(4, 1fr)",
            gap: "1rem",
            marginBottom: "2rem",
          }}
        >
          {statCards.map((card, idx) => (
            <div
              key={card.label}
              className="card animate-slide-up"
              style={{
                animationDelay: `${idx * 80}ms`,
                animationFillMode: "backwards",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "0.75rem",
                }}
              >
                <span style={{ fontSize: "1.25rem" }}>{card.icon}</span>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    color: "var(--text-muted)",
                    fontWeight: 500,
                  }}
                >
                  {card.label}
                </span>
              </div>
              <div
                style={{
                  fontSize: "1.75rem",
                  fontWeight: 700,
                  color: card.color,
                  fontFamily: "var(--font-geist-mono)",
                }}
              >
                {card.value}
              </div>
            </div>
          ))}
        </div>

        {/* Recent activity */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: "1.5rem",
          }}
        >
          {/* Recent Projects */}
          <div className="card animate-fade-in">
            <h3
              style={{
                marginBottom: "1rem",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <span>🗂️</span> Recent Projects
            </h3>
            {stats?.recent_projects?.length ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                {stats.recent_projects.map((p: any) => (
                  <div
                    key={p.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "0.625rem 0.75rem",
                      background: "var(--bg-primary)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div>
                      <div
                        style={{
                          fontWeight: 500,
                          fontSize: "0.875rem",
                        }}
                      >
                        {p.name}
                      </div>
                      <div
                        style={{
                          fontSize: "0.6875rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        {p.table_count} tables
                      </div>
                    </div>
                    <span className="badge badge-accent">{p.table_count}T</span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", textAlign: "center", padding: "2rem 0" }}>
                No projects yet. Start by creating a schema!
              </p>
            )}
          </div>

          {/* Recent Jobs */}
          <div className="card animate-fade-in">
            <h3
              style={{
                marginBottom: "1rem",
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
              }}
            >
              <span>⚡</span> Recent Jobs
            </h3>
            {stats?.recent_jobs?.length ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.5rem",
                }}
              >
                {stats.recent_jobs.map((j: any) => (
                  <div
                    key={j.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "0.625rem 0.75rem",
                      background: "var(--bg-primary)",
                      borderRadius: "var(--radius-md)",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div>
                      <div
                        style={{ fontWeight: 500, fontSize: "0.875rem" }}
                      >
                        {j.project_name || `Job ${j.id}`}
                      </div>
                      <div
                        style={{
                          fontSize: "0.6875rem",
                          color: "var(--text-muted)",
                        }}
                      >
                        {j.rows_generated?.toLocaleString()} rows
                      </div>
                    </div>
                    <span
                      className={`badge ${
                        j.status === "completed"
                          ? "badge-success"
                          : j.status === "failed"
                          ? "badge-error"
                          : "badge-info"
                      }`}
                    >
                      {j.status}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", textAlign: "center", padding: "2rem 0" }}>
                No generation jobs yet. Generate your first dataset!
              </p>
            )}
          </div>
        </div>

        {/* Quick start */}
        <div
          className="card-glow animate-slide-up"
          style={{
            marginTop: "2rem",
            textAlign: "center",
            padding: "2.5rem",
          }}
        >
          <div style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>🚀</div>
          <h2 style={{ marginBottom: "0.5rem" }}>Ready to Generate?</h2>
          <p
            style={{
              maxWidth: "500px",
              margin: "0 auto 1.5rem",
              fontSize: "0.9375rem",
            }}
          >
            Paste your SQL schema, choose your row count, and let AI generate
            realistic, privacy-compliant synthetic data in seconds.
          </p>
          <Link href="/generate" className="btn-primary">
            <span>⚡</span> Start Generating
          </Link>
        </div>
      </main>
    </>
  );
}
