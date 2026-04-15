"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import PricingPlans from "@/components/PricingPlans";

const API_BASE = "http://localhost:8000";

interface Plan {
  id: string;
  name: string;
  credits: number;
  price_usd: number;
  description: string;
  badge: string | null;
}

export default function PricingPage() {
  const router = useRouter();
  const [plans, setPlans] = useState<Plan[]>([]);
  const [token, setToken] = useState("");
  const [credits, setCredits] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const t = localStorage.getItem("token");
    if (t) setToken(t);

    // Fetch plans (no auth needed)
    fetch(`${API_BASE}/api/payments/plans`)
      .then((r) => r.json())
      .then((d) => setPlans(d.plans || []))
      .catch(console.error)
      .finally(() => setLoading(false));

    // Fetch credits if logged in
    if (t) {
      fetch(`${API_BASE}/api/payments/credits`, {
        headers: { Authorization: `Bearer ${t}` },
      })
        .then((r) => r.json())
        .then((d) => setCredits(d.credits ?? 0))
        .catch(console.error);
    }
  }, []);

  return (
    <>
      <Navbar />
      <main
        style={{
          flex: 1,
          maxWidth: "960px",
          margin: "0 auto",
          padding: "3rem 1.5rem",
          width: "100%",
        }}
      >
        {/* Hero */}
        <div
          className="animate-fade-in"
          style={{ textAlign: "center", marginBottom: "3rem" }}
        >
          <span
            className="badge badge-accent"
            style={{ marginBottom: "1rem", display: "inline-block" }}
          >
            Simple, transparent pricing
          </span>
          <h1 style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>
            Generate data at{" "}
            <span
              style={{
                background: "var(--accent-gradient)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
              }}
            >
              any scale
            </span>
          </h1>
          <p
            style={{
              fontSize: "1.0625rem",
              maxWidth: "540px",
              margin: "0 auto",
            }}
          >
            Pay once, use whenever. No subscriptions. Credits never expire.
            Each credit = one full data generation job — any row count, any schema.
          </p>
        </div>

        {/* Free tier notice */}
        <div
          className="card"
          style={{
            marginBottom: "2rem",
            display: "flex",
            alignItems: "center",
            gap: "1rem",
            background: "var(--success-bg)",
            border: "1px solid rgba(52,211,153,0.2)",
          }}
        >
          <span style={{ fontSize: "1.5rem" }}>🎁</span>
          <div>
            <div
              style={{ fontWeight: 600, fontSize: "0.9375rem", color: "var(--success)" }}
            >
              Start free — 3 credits on signup
            </div>
            <p style={{ margin: 0, fontSize: "0.8125rem" }}>
              New accounts get 3 free generation jobs so you can evaluate before
              purchasing.
            </p>
          </div>
        </div>

        {/* Plans */}
        {loading ? (
          <div
            style={{
              textAlign: "center",
              padding: "3rem",
              color: "var(--text-muted)",
            }}
          >
            <div
              className="spinner"
              style={{ margin: "0 auto 1rem", width: "28px", height: "28px" }}
            />
            Loading plans...
          </div>
        ) : (
          <PricingPlans
            plans={plans}
            token={token}
            currentCredits={credits}
            onSuccess={() => router.push("/?payment=success")}
          />
        )}

        {/* FAQ */}
        <div
          className="animate-slide-up"
          style={{ marginTop: "3.5rem" }}
        >
          <h2
            style={{
              textAlign: "center",
              marginBottom: "1.5rem",
              fontSize: "1.25rem",
            }}
          >
            Frequently Asked Questions
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "1rem",
            }}
          >
            {[
              {
                q: "What is a generation credit?",
                a: "One credit = one data generation job. A job generates data for all tables in your schema at the row count you specify. Credits are shared across all your projects.",
              },
              {
                q: "Do credits expire?",
                a: "No. Credits never expire. Buy once and use them whenever you need. There are no monthly fees or subscriptions.",
              },
              {
                q: "Is the generated data safe to use?",
                a: "Yes — all data is 100% synthetic. No real user data is ever used or stored. Fully GDPR/CCPA compliant by design.",
              },
              {
                q: "What AI model is used?",
                a: "We use Ollama running locally on your machine (llama3.2:3b). All AI processing happens on your hardware. Zero data sent to any cloud.",
              },
              {
                q: "What export formats are supported?",
                a: "CSV, SQL INSERT statements, and JSON. Each table can be exported independently in any format.",
              },
              {
                q: "Can I generate millions of rows?",
                a: "Yes — up to 1,000,000 rows per table per job. The Faker engine generates data in batches for high performance.",
              },
            ].map((item) => (
              <div
                key={item.q}
                className="card"
                style={{ gap: "0.5rem" }}
              >
                <h3
                  style={{
                    fontSize: "0.9375rem",
                    marginBottom: "0.5rem",
                  }}
                >
                  {item.q}
                </h3>
                <p style={{ fontSize: "0.8125rem", margin: 0 }}>{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}
