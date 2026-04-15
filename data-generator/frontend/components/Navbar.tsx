"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    { href: "/", label: "Dashboard", icon: "⬡" },
    { href: "/generate", label: "Generate", icon: "⚡" },
    { href: "/pricing", label: "Pricing", icon: "💎" },
  ];

  return (
    <nav
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(10, 10, 15, 0.8)",
        backdropFilter: "blur(16px) saturate(180%)",
        borderBottom: "1px solid var(--border-subtle)",
      }}
    >
      <div
        style={{
          maxWidth: "1280px",
          margin: "0 auto",
          padding: "0 1.5rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          height: "64px",
        }}
      >
        {/* Logo */}
        <Link
          href="/"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.625rem",
            textDecoration: "none",
          }}
        >
          <div
            style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "var(--accent-gradient)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1rem",
              fontWeight: 700,
              color: "white",
              boxShadow: "0 2px 8px rgba(99, 102, 241, 0.3)",
            }}
          >
            S
          </div>
          <span
            style={{
              fontSize: "1.125rem",
              fontWeight: 700,
              letterSpacing: "-0.03em",
              color: "var(--text-primary)",
            }}
          >
            Synth<span style={{ color: "var(--accent-primary)" }}>Forge</span>
          </span>
          <span
            className="badge badge-accent"
            style={{ fontSize: "0.625rem", marginLeft: "0.25rem" }}
          >
            $0 AI
          </span>
        </Link>

        {/* Nav links */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.375rem",
                  padding: "0.5rem 1rem",
                  borderRadius: "var(--radius-md)",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  color: isActive
                    ? "var(--text-primary)"
                    : "var(--text-secondary)",
                  background: isActive
                    ? "var(--accent-glow)"
                    : "transparent",
                  border: isActive
                    ? "1px solid var(--border-accent)"
                    : "1px solid transparent",
                  transition: "all 150ms ease",
                  textDecoration: "none",
                }}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </div>

        {/* Status indicator */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.5rem",
            fontSize: "0.75rem",
            color: "var(--text-muted)",
          }}
        >
          <div
            style={{
              width: "7px",
              height: "7px",
              borderRadius: "50%",
              background: "var(--success)",
              boxShadow: "0 0 6px var(--success)",
            }}
          />
          Local AI
        </div>
      </div>
    </nav>
  );
}
