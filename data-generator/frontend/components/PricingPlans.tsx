"use client";

import { useState } from "react";

const API_BASE = "http://localhost:8000";

interface Plan {
  id: string;
  name: string;
  credits: number;
  price_usd: number;
  description: string;
  badge: string | null;
}

interface PricingPlansProps {
  plans: Plan[];
  token: string;
  currentCredits: number;
  onSuccess?: () => void;
}

export default function PricingPlans({
  plans,
  token,
  currentCredits,
  onSuccess,
}: PricingPlansProps) {
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState("");

  const handleCheckout = async (planId: string) => {
    if (!token) {
      setError("Please sign in to purchase credits.");
      return;
    }
    setLoading(planId);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/api/payments/create-checkout-session`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ plan_id: planId }),
      });

      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.detail || "Checkout failed");
      }

      const { url } = await res.json();
      window.location.href = url; // redirect to Stripe Checkout
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(null);
    }
  };

  const highlightedPlan = "pro";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      {/* Current balance */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0.875rem 1.25rem",
          background: "var(--bg-tertiary)",
          borderRadius: "var(--radius-md)",
          border: "1px solid var(--border-default)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
          <span style={{ fontSize: "1.125rem" }}>💎</span>
          <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)" }}>
            Current balance
          </span>
        </div>
        <span
          style={{
            fontSize: "1.25rem",
            fontWeight: 700,
            color:
              currentCredits === 0
                ? "var(--error)"
                : currentCredits <= 5
                ? "var(--warning)"
                : "var(--success)",
            fontFamily: "var(--font-geist-mono)",
          }}
        >
          {currentCredits} credits
        </span>
      </div>

      {/* What a credit buys */}
      <p
        style={{
          fontSize: "0.8125rem",
          color: "var(--text-muted)",
          textAlign: "center",
        }}
      >
        1 credit = 1 generation job (any row count, any number of tables)
      </p>

      {/* Plans grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "1rem",
        }}
      >
        {plans.map((plan) => {
          const isHighlighted = plan.id === highlightedPlan;
          const isLoading = loading === plan.id;
          const pricePerCredit = (plan.price_usd / plan.credits).toFixed(3);

          return (
            <div
              key={plan.id}
              style={{
                display: "flex",
                flexDirection: "column",
                padding: "1.5rem",
                background: isHighlighted ? "var(--bg-elevated)" : "var(--bg-card)",
                border: isHighlighted
                  ? "1px solid var(--accent-primary)"
                  : "1px solid var(--border-subtle)",
                borderRadius: "var(--radius-lg)",
                boxShadow: isHighlighted ? "var(--shadow-glow)" : "none",
                position: "relative",
                transition: "all var(--transition-base)",
                gap: "1rem",
              }}
            >
              {/* Badge */}
              {plan.badge && (
                <div
                  style={{
                    position: "absolute",
                    top: "-12px",
                    left: "50%",
                    transform: "translateX(-50%)",
                    background: "var(--accent-gradient)",
                    color: "white",
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    padding: "0.25rem 0.75rem",
                    borderRadius: "9999px",
                    whiteSpace: "nowrap",
                    letterSpacing: "0.04em",
                  }}
                >
                  {plan.badge}
                </div>
              )}

              {/* Plan name & price */}
              <div>
                <h3
                  style={{
                    fontSize: "1rem",
                    marginBottom: "0.375rem",
                    color: isHighlighted
                      ? "var(--accent-primary-hover)"
                      : "var(--text-primary)",
                  }}
                >
                  {plan.name}
                </h3>
                <div
                  style={{
                    display: "flex",
                    alignItems: "baseline",
                    gap: "0.25rem",
                    marginBottom: "0.25rem",
                  }}
                >
                  <span
                    style={{
                      fontSize: "2rem",
                      fontWeight: 800,
                      color: "var(--text-primary)",
                      fontFamily: "var(--font-geist-mono)",
                    }}
                  >
                    ${plan.price_usd}
                  </span>
                  <span
                    style={{ fontSize: "0.8125rem", color: "var(--text-muted)" }}
                  >
                    one-time
                  </span>
                </div>
                <p
                  style={{
                    fontSize: "0.75rem",
                    color: "var(--text-muted)",
                    margin: 0,
                  }}
                >
                  {plan.description}
                </p>
              </div>

              {/* Credits & per-credit price */}
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
                  {plan.credits}
                </div>
                <div
                  style={{
                    fontSize: "0.6875rem",
                    color: "var(--text-muted)",
                    marginTop: "0.125rem",
                  }}
                >
                  generation credits
                </div>
                <div
                  style={{
                    fontSize: "0.6875rem",
                    color: "var(--text-muted)",
                    marginTop: "0.25rem",
                  }}
                >
                  ${pricePerCredit} / credit
                </div>
              </div>

              {/* Feature list */}
              <ul
                style={{
                  listStyle: "none",
                  margin: 0,
                  padding: 0,
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.375rem",
                  flex: 1,
                }}
              >
                {[
                  "Unlimited rows per job",
                  "All export formats (CSV, SQL, JSON)",
                  "AI schema analysis (Ollama)",
                  "FK referential integrity",
                  `${plan.credits} schema projects`,
                ].map((feature) => (
                  <li
                    key={feature}
                    style={{
                      fontSize: "0.75rem",
                      color: "var(--text-secondary)",
                      display: "flex",
                      alignItems: "center",
                      gap: "0.5rem",
                    }}
                  >
                    <span style={{ color: "var(--success)", flexShrink: 0 }}>
                      ✓
                    </span>
                    {feature}
                  </li>
                ))}
              </ul>

              {/* CTA button */}
              <button
                className={isHighlighted ? "btn-primary" : "btn-secondary"}
                onClick={() => handleCheckout(plan.id)}
                disabled={isLoading}
                style={{ width: "100%", marginTop: "0.25rem" }}
              >
                {isLoading ? (
                  <div className="spinner" />
                ) : (
                  `Get ${plan.credits} Credits`
                )}
              </button>
            </div>
          );
        })}
      </div>

      {error && (
        <div
          style={{
            padding: "0.75rem 1rem",
            background: "var(--error-bg)",
            border: "1px solid rgba(248,113,113,0.2)",
            borderRadius: "var(--radius-md)",
            color: "var(--error)",
            fontSize: "0.8125rem",
            textAlign: "center",
          }}
        >
          {error}
        </div>
      )}

      {/* Trust badges */}
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          gap: "1.5rem",
          fontSize: "0.6875rem",
          color: "var(--text-muted)",
        }}
      >
        {["🔒 Secure via Stripe", "⚡ Instant Credits", "🔁 No Subscription", "🛡️ GDPR Safe"].map(
          (item) => (
            <span key={item}>{item}</span>
          )
        )}
      </div>
    </div>
  );
}
