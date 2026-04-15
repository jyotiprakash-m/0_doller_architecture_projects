# SynthForge — Synthetic Data Generator

A privacy-first platform that generates realistic, statistically accurate, synthetic datasets for development and testing. Addresses GDPR/CCPA concerns by eliminating the need for real production data. All AI runs locally via Ollama — $0 cost.

It features a hybrid generation engine: AI analyzes your schemas (via Ollama), while Faker bulk-generates the data, maintaining referential integrity using an automated topological sort, saving outputs to a fast DuckDB instance.

It also includes a SaaS model using Stripe for purchasing "data generation credits."

## Architecture Stack

| Component | Technology | Description |
|-----------|-----------|-------------|
| **Frontend** | Next.js 16 + Tailwind v4 | Dashboard, schema input, live generation progress, export (CSV/SQL/JSON). |
| **API** | FastAPI | REST API layer handling auth, schema management, stripe webhooks. |
| **AI Engine** | Ollama (llama3.2:3b) | Locally runs inference to analyze SQL DDL and determine Faker strategies. |
| **Bulk Gen** | Python Faker | Generates millions of rows programmatically following the LLM's plan. |
| **Data Store** | DuckDB (per job) | Extremely fast analytical database used as temporary data storage for preview and export. |
| **Metadata** | SQLite | Users, projects, generation jobs tracking. |

## Quick Start

### Prerequisites
1. **Node.js** (v18+)
2. **Python** (v3.10+)
3. **Ollama** installed locally (running `llama3.2:3b`)
   - Run: `ollama run llama3.2:3b`

---

### Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
   *(Note: If integrating with an existing `$0 Architecture` project like `legal-auditor`, you can share its virtual environment).*

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Update `.env` with your desired JWT secret and Stripe API keys (optional, but needed for checkout to work).

4. Run the API Server:
   ```bash
   python main.py
   ```
   The backend will be available at `http://localhost:8000`. Swagger docs at `http://localhost:8000/docs`.

---

### Frontend Setup (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at `http://localhost:3000`.

---

## Testing the Application

1. Open `http://localhost:3000` in your browser.
2. Sign up for a new account (you get 3 free credits!).
3. Go to the **Generate** page.
4. Try pasting the following sample SQL DDL to test:
   ```sql
   CREATE TABLE customers (
     id INTEGER PRIMARY KEY,
     first_name VARCHAR NOT NULL,
     last_name VARCHAR NOT NULL,
     email VARCHAR UNIQUE NOT NULL,
     city VARCHAR,
     country VARCHAR,
     created_at TIMESTAMP NOT NULL
   );

   CREATE TABLE orders (
     id INTEGER PRIMARY KEY,
     customer_id INTEGER NOT NULL REFERENCES customers(id),
     total_amount FLOAT NOT NULL,
     status VARCHAR DEFAULT 'pending',
     order_date TIMESTAMP NOT NULL
   );
   ```
5. Choose 1,000 rows per table and click **Generate**.
6. Watch the real-time progress as data is created.
7. Preview the data and export it as CSV, JSON, or SQL!
