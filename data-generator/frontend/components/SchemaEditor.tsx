"use client";

import { useState } from "react";

interface SchemaEditorProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

const SAMPLE_SCHEMAS = {
  "E-Commerce": `CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  first_name VARCHAR NOT NULL,
  last_name VARCHAR NOT NULL,
  email VARCHAR UNIQUE NOT NULL,
  phone VARCHAR,
  city VARCHAR,
  country VARCHAR,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name VARCHAR NOT NULL,
  description TEXT,
  price FLOAT NOT NULL,
  category VARCHAR,
  sku VARCHAR UNIQUE,
  stock_quantity INTEGER DEFAULT 0,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  order_date TIMESTAMP NOT NULL,
  total_amount FLOAT NOT NULL,
  status VARCHAR DEFAULT 'pending',
  shipping_address TEXT
);

CREATE TABLE order_items (
  id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  product_id INTEGER NOT NULL REFERENCES products(id),
  quantity INTEGER NOT NULL,
  unit_price FLOAT NOT NULL
);`,

  "SaaS Users": `CREATE TABLE organizations (
  id INTEGER PRIMARY KEY,
  name VARCHAR NOT NULL,
  domain VARCHAR UNIQUE,
  plan VARCHAR DEFAULT 'free',
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL REFERENCES organizations(id),
  email VARCHAR UNIQUE NOT NULL,
  username VARCHAR UNIQUE NOT NULL,
  full_name VARCHAR NOT NULL,
  role VARCHAR DEFAULT 'member',
  last_login TIMESTAMP,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE projects (
  id INTEGER PRIMARY KEY,
  org_id INTEGER NOT NULL REFERENCES organizations(id),
  name VARCHAR NOT NULL,
  description TEXT,
  status VARCHAR DEFAULT 'active',
  created_by INTEGER REFERENCES users(id),
  created_at TIMESTAMP NOT NULL
);`,

  "Blog Platform": `CREATE TABLE authors (
  id INTEGER PRIMARY KEY,
  name VARCHAR NOT NULL,
  email VARCHAR UNIQUE NOT NULL,
  bio TEXT,
  avatar_url VARCHAR,
  joined_at TIMESTAMP NOT NULL
);

CREATE TABLE categories (
  id INTEGER PRIMARY KEY,
  name VARCHAR UNIQUE NOT NULL,
  slug VARCHAR UNIQUE NOT NULL,
  description TEXT
);

CREATE TABLE posts (
  id INTEGER PRIMARY KEY,
  author_id INTEGER NOT NULL REFERENCES authors(id),
  category_id INTEGER REFERENCES categories(id),
  title VARCHAR NOT NULL,
  slug VARCHAR UNIQUE NOT NULL,
  content TEXT NOT NULL,
  status VARCHAR DEFAULT 'draft',
  views INTEGER DEFAULT 0,
  published_at TIMESTAMP,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE comments (
  id INTEGER PRIMARY KEY,
  post_id INTEGER NOT NULL REFERENCES posts(id),
  author_name VARCHAR NOT NULL,
  email VARCHAR NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);`,
};

export default function SchemaEditor({
  value,
  onChange,
  placeholder,
}: SchemaEditorProps) {
  const [activeTemplate, setActiveTemplate] = useState<string | null>(null);

  const handleTemplateClick = (name: string) => {
    setActiveTemplate(name);
    onChange(SAMPLE_SCHEMAS[name as keyof typeof SAMPLE_SCHEMAS]);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
      {/* Template selector */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          flexWrap: "wrap",
        }}
      >
        <span
          style={{
            fontSize: "0.75rem",
            color: "var(--text-muted)",
            fontWeight: 500,
          }}
        >
          Templates:
        </span>
        {Object.keys(SAMPLE_SCHEMAS).map((name) => (
          <button
            key={name}
            onClick={() => handleTemplateClick(name)}
            style={{
              padding: "0.25rem 0.75rem",
              fontSize: "0.75rem",
              fontWeight: 500,
              borderRadius: "9999px",
              border:
                activeTemplate === name
                  ? "1px solid var(--accent-primary)"
                  : "1px solid var(--border-default)",
              background:
                activeTemplate === name ? "var(--accent-glow)" : "transparent",
              color:
                activeTemplate === name
                  ? "var(--accent-primary-hover)"
                  : "var(--text-secondary)",
              cursor: "pointer",
              transition: "all 150ms ease",
            }}
          >
            {name}
          </button>
        ))}
      </div>

      {/* Editor */}
      <div style={{ position: "relative" }}>
        <textarea
          className="code-editor"
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setActiveTemplate(null);
          }}
          placeholder={
            placeholder ||
            "Paste your SQL CREATE TABLE statements here...\n\nExample:\nCREATE TABLE users (\n  id INTEGER PRIMARY KEY,\n  name VARCHAR NOT NULL,\n  email VARCHAR UNIQUE\n);"
          }
          spellCheck={false}
          style={{ minHeight: "320px" }}
        />

        {/* Line count indicator */}
        <div
          style={{
            position: "absolute",
            bottom: "0.75rem",
            right: "0.75rem",
            display: "flex",
            gap: "0.75rem",
            fontSize: "0.6875rem",
            color: "var(--text-muted)",
          }}
        >
          <span>{value.split("\n").length} lines</span>
          <span>{value.length} chars</span>
        </div>
      </div>
    </div>
  );
}
