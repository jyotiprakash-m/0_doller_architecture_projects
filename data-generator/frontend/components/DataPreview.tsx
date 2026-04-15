"use client";

import { useState } from "react";

interface DataPreviewProps {
  tables: {
    name: string;
    columns: string[];
    rows: (string | null)[][];
    totalRows: number;
    page: number;
    pageSize: number;
    totalPages: number;
  }[];
  onPageChange: (tableName: string, page: number) => void;
  loading?: boolean;
}

export default function DataPreview({
  tables,
  onPageChange,
  loading = false,
}: DataPreviewProps) {
  const [activeTable, setActiveTable] = useState(0);

  if (tables.length === 0) {
    return (
      <div
        className="card"
        style={{
          textAlign: "center",
          padding: "3rem",
          color: "var(--text-muted)",
        }}
      >
        <div style={{ fontSize: "2rem", marginBottom: "0.5rem" }}>📊</div>
        <p>No data to preview yet. Generate data first.</p>
      </div>
    );
  }

  const table = tables[activeTable];

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      {/* Table tabs */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.25rem",
          borderBottom: "1px solid var(--border-subtle)",
          paddingBottom: "0",
          overflowX: "auto",
        }}
      >
        {tables.map((t, idx) => (
          <button
            key={t.name}
            onClick={() => setActiveTable(idx)}
            style={{
              padding: "0.625rem 1rem",
              fontSize: "0.8125rem",
              fontWeight: activeTable === idx ? 600 : 500,
              color:
                activeTable === idx
                  ? "var(--accent-primary-hover)"
                  : "var(--text-secondary)",
              background: "transparent",
              border: "none",
              borderBottom:
                activeTable === idx
                  ? "2px solid var(--accent-primary)"
                  : "2px solid transparent",
              cursor: "pointer",
              transition: "all 150ms ease",
              whiteSpace: "nowrap",
              fontFamily: "var(--font-geist-mono)",
            }}
          >
            {t.name}
            <span
              style={{
                marginLeft: "0.375rem",
                fontSize: "0.6875rem",
                color: "var(--text-muted)",
              }}
            >
              ({t.totalRows.toLocaleString()})
            </span>
          </button>
        ))}
      </div>

      {/* Data table */}
      <div
        style={{
          border: "1px solid var(--border-subtle)",
          borderRadius: "var(--radius-lg)",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            maxHeight: "420px",
            overflowY: "auto",
            overflowX: "auto",
          }}
        >
          {loading ? (
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "3rem",
                gap: "0.75rem",
                color: "var(--text-muted)",
              }}
            >
              <div className="spinner" />
              Loading data...
            </div>
          ) : (
            <table className="data-table">
              <thead>
                <tr>
                  <th
                    style={{
                      width: "48px",
                      textAlign: "center",
                      color: "var(--text-muted)",
                    }}
                  >
                    #
                  </th>
                  {table.columns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {table.rows.map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    <td
                      style={{
                        textAlign: "center",
                        color: "var(--text-muted)",
                        fontSize: "0.75rem",
                      }}
                    >
                      {(table.page - 1) * table.pageSize + rowIdx + 1}
                    </td>
                    {row.map((cell, cellIdx) => (
                      <td key={cellIdx}>
                        {cell === null ? (
                          <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>
                            NULL
                          </span>
                        ) : (
                          cell
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Pagination */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: "0.8125rem",
          color: "var(--text-secondary)",
        }}
      >
        <span>
          Showing {((table.page - 1) * table.pageSize + 1).toLocaleString()}–
          {Math.min(table.page * table.pageSize, table.totalRows).toLocaleString()}{" "}
          of {table.totalRows.toLocaleString()} rows
        </span>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <button
            className="btn-ghost"
            disabled={table.page <= 1}
            onClick={() => onPageChange(table.name, table.page - 1)}
            style={{
              opacity: table.page <= 1 ? 0.4 : 1,
              cursor: table.page <= 1 ? "not-allowed" : "pointer",
            }}
          >
            ← Prev
          </button>
          <span
            style={{
              display: "flex",
              alignItems: "center",
              padding: "0 0.5rem",
              fontSize: "0.75rem",
              color: "var(--text-muted)",
            }}
          >
            Page {table.page} of {table.totalPages}
          </span>
          <button
            className="btn-ghost"
            disabled={table.page >= table.totalPages}
            onClick={() => onPageChange(table.name, table.page + 1)}
            style={{
              opacity: table.page >= table.totalPages ? 0.4 : 1,
              cursor:
                table.page >= table.totalPages ? "not-allowed" : "pointer",
            }}
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
}
