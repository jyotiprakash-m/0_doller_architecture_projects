# 🛡️ LegalShield AI

**Privacy-First, AI-Powered Legal Document Auditor — SaaS Platform**

A production-grade SaaS application that audits legal documents using AI — with **100% local inference**. Your documents never leave your machine. Powered by Ollama, LlamaIndex, ChromaDB, and Stripe.

---

## ✨ Key Features

- **🔒 Zero Data Leakage** — All AI models, embeddings, and databases run 100% locally
- **📄 Intelligent Auditing** — Upload contracts/policies and get comprehensive risk analysis with compliance scores
- **💬 Document Chat** — Ask questions about any specific document via a slide-out chat drawer
- **👥 Multi-Tenant** — JWT authentication with user-isolated data (each user sees only their own documents)
- **💳 Credit System** — Stripe-powered monetization (1 credit = 1 audit, 0.1 credit = 1 chat query)
- **🎨 Premium UI** — Dark-mode glassmorphism design with micro-animations

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML, CSS, JavaScript (Vanilla SPA) |
| Backend | Python 3, FastAPI, Uvicorn |
| AI / LLM | Ollama, LLaMA 3.2B |
| Embeddings | Nomic-Embed-Text |
| RAG Framework | LlamaIndex |
| Vector DB | ChromaDB (persistent, local) |
| Database | SQLite |
| Auth | JWT + bcrypt |
| Payments | Stripe |

---

## 🏗️ System Architecture

![System Architecture](./architecture.png)

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#E3F2FD,stroke:#1565C0,stroke-width:2px,color:#000;
    classDef backend fill:#E8F5E9,stroke:#2E7D32,stroke-width:2px,color:#000;
    classDef ai fill:#FFF3E0,stroke:#EF6C00,stroke-width:2px,color:#000;
    classDef db fill:#F3E5F5,stroke:#6A1B9A,stroke-width:2px,color:#000;

    %% Components
    subgraph Frontend [Frontend Dashboard Client]
        UI[Web UI - HTML/JS/CSS]
    end

    subgraph BackendAPI [FastAPI Backend Server]
        R_Docs[Documents Router]
        R_Audit[Audit Router]
        R_Chat[Chat Router]
        DocProc[Document Processor]
        RAG[RAG Engine - LlamaIndex]
    end

    subgraph Databases [Local Storage]
        SQLite[(SQLite DB)]
        ChromaDB[(ChromaDB Vector Store)]
    end

    subgraph LocalAI [Ollama Local AI Engine]
        EmbedModel[Nomic-Embed-Text Model]
        LLM[Mistral LLM Model]
    end

    %% Frontend to Backend Connections
    UI -- "POST /api/documents/upload" --> R_Docs
    UI -- "GET /api/audit/{id}" --> R_Audit
    UI -- "POST /api/chat" --> R_Chat

    %% Internal Backend Flow (Document Upload)
    R_Docs -- "Extracts & Chunks" --> DocProc
    DocProc -- "Saves metadata" --> SQLite
    DocProc -- "Passes chunks" --> RAG

    %% RAG Engine to AI Models & DBs
    RAG -- "Generates Embeddings" --> EmbedModel
    RAG -- "Stores Vectors" --> ChromaDB
    
    %% Internal Backend Flow (Audit / Chat)
    R_Audit & R_Chat -- "Queries context" --> RAG
    RAG -- "Fetches similar chunks" --> ChromaDB
    RAG -- "Injects prompt & context" --> LLM
    LLM -- "Generates Response" --> R_Audit
    LLM -- "Generates Response" --> R_Chat

    %% Apply Styles
    class UI frontend;
    class R_Docs,R_Audit,R_Chat,DocProc,RAG backend;
    class SQLite,ChromaDB db;
    class EmbedModel,LLM ai;
```

---

## 📊 Database ERD

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryTextColor': '#000', 'lineColor': '#333'}}}%%
erDiagram
    USERS {
        text id PK
        text email
        text hashed_password
        integer credits
        text created_at
    }

    DOCUMENTS {
        text id PK
        text user_id FK
        text filename
        text file_type
        integer file_size
        text file_path
        text status
        integer page_count
        integer chunk_count
        text uploaded_at
        text updated_at
    }

    AUDIT_REPORTS {
        text id PK
        text document_id FK
        text user_id FK
        text audit_type
        text status
        text executive_summary
        text overall_risk_score
        real compliance_score
        text findings_json
        text key_clauses_json
        text created_at
        text completed_at
    }

    CHAT_HISTORY {
        text id PK
        text user_id FK
        text role
        text content
        text sources_json
        text document_ids_json
        text created_at
    }

    USERS ||--o{ DOCUMENTS : "uploads"
    USERS ||--o{ AUDIT_REPORTS : "owns"
    USERS ||--o{ CHAT_HISTORY : "participates"
    DOCUMENTS ||--o{ AUDIT_REPORTS : "analyzed_in"
```

---

## 📋 Prerequisites

Before you begin, make sure you have the following installed:

- **Python 3.10+** — [python.org](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Ollama** — [ollama.com](https://ollama.com/)
- **Stripe Account (Test Mode)** — [stripe.com](https://dashboard.stripe.com/test/apikeys)

---

## 🚀 Setup Guide

### Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd legal-auditor
```

### Step 2: Install & Pull AI Models (Ollama)

```bash
# Start Ollama (if not running)
ollama serve

# Pull required models (one-time download)
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

> **Note:** `llama3.2:3b` is ~2GB and `nomic-embed-text` is ~270MB. These download once and run locally forever.

### Step 3: Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate      # macOS/Linux
# venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Now edit `backend/.env` with your actual keys:

```env
# Required — Get from https://dashboard.stripe.com/test/apikeys
STRIPE_API_KEY=sk_test_YOUR_KEY
STRIPE_WEBHOOK_SECRET=whsec_YOUR_SECRET
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY

# Recommended — Change to a random string
JWT_SECRET_KEY=your-random-secret-key-here
```

### Step 4: Setup Frontend

```bash
cd ../frontend

# Install dependencies
npm install
```

### Step 5: Run the Application

Open **three terminal windows**:

**Terminal 1 — Ollama (AI Engine):**
```bash
ollama serve
```

**Terminal 2 — Backend (API Server):**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```
> Backend runs at: `http://localhost:8000`

**Terminal 3 — Frontend (Web Server):**
```bash
cd frontend
npm start
```
> Frontend runs at: `http://localhost:3000`

### Step 6: Open the App

Navigate to **http://localhost:3000** in your browser.

1. **Register** a new account
2. **Upload** a legal document (PDF, DOCX, or TXT)
3. **Audit** — Click "Audit" to run AI analysis
4. **Chat** — Click "Chat" to ask questions about the document
5. **Buy Credits** — Click "Buy Credits" when you need more

---

## 💳 Stripe Setup (for Payments)

### Test Mode (Development)

1. Go to [Stripe Dashboard → API Keys](https://dashboard.stripe.com/test/apikeys)
2. Copy your **Publishable key** (`pk_test_...`) and **Secret key** (`sk_test_...`)
3. Paste them into `backend/.env`

### Webhook (Local Development)

For local webhook testing, use the Stripe CLI:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to your Stripe account
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:8000/api/payments/webhook
```

Copy the `whsec_...` signing secret from the CLI output and paste it into `backend/.env` as `STRIPE_WEBHOOK_SECRET`.

---

## 📁 Project Structure

```
legal-auditor/
├── backend/
│   ├── .env                    # Secret keys (git-ignored)
│   ├── .env.example            # Template for new developers
│   ├── config.py               # Loads .env, defines all settings
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt        # Python dependencies
│   ├── routers/
│   │   ├── auth.py             # Login, Register, JWT, /me
│   │   ├── audit.py            # AI audit execution & reports
│   │   ├── chat.py             # RAG-powered document Q&A
│   │   ├── documents.py        # Upload, list, delete documents
│   │   └── payments.py         # Stripe checkout & webhooks
│   └── services/
│       ├── auth_utils.py       # JWT helpers & dependencies
│       ├── db.py               # SQLite operations
│       ├── doc_processor.py    # PDF/DOCX text extraction
│       └── rag_engine.py       # LlamaIndex + ChromaDB + Ollama
├── frontend/
│   ├── index.html              # SPA shell with sidebar & drawer
│   ├── style.css               # Premium dark-mode design system
│   ├── app.js                  # Router, state, API client
│   ├── server.js               # Express.js static file server
│   └── components/
│       ├── auth.js             # Login/Register/Logout UI
│       ├── dashboard.js        # Dashboard stats & recent docs
│       ├── upload.js           # File upload with drag-and-drop
│       ├── documents.js        # Document management table
│       ├── audit-report.js     # Audit report visualization
│       ├── chat.js             # Global + Drawer chat logic
│       ├── pricing.js          # Credit purchase page
│       └── sidebar.js          # Sidebar navigation
├── architecture_design.md      # Detailed architecture documentation
├── .gitignore                  # Protects secrets & generated data
└── README.md                   # This file
```

---

## 🔐 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OLLAMA_BASE_URL` | No | Ollama server URL (default: `http://localhost:11434`) |
| `LLM_MODEL` | No | LLM model name (default: `llama3.2:3b`) |
| `EMBED_MODEL` | No | Embedding model (default: `nomic-embed-text`) |
| `JWT_SECRET_KEY` | **Yes** | Random secret for JWT token signing |
| `STRIPE_API_KEY` | **Yes** | Stripe secret key (`sk_test_...`) |
| `STRIPE_WEBHOOK_SECRET` | **Yes** | Stripe webhook signing secret (`whsec_...`) |
| `STRIPE_PUBLISHABLE_KEY` | **Yes** | Stripe publishable key (`pk_test_...`) |

---

## 💰 Credit System

| Operation | Cost | Description |
|-----------|------|-------------|
| Document Audit | 1.0 credit | Full AI risk analysis with PDF report |
| Chat Query | 0.1 credit | RAG-powered Q&A about a specific document |
| New Account | 5.0 credits | Starter credits on registration |

---

## 🛠️ Troubleshooting

### "Ollama is not running"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama
ollama serve
```

### "Model not found"
```bash
# Pull the required models
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### Frontend not loading latest changes
Press `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows) to hard refresh. The app uses cache-busted script tags (`?v=2`).

### Empty chat responses
If documents were uploaded before the multi-tenant update, they lack `user_id` metadata. **Delete and re-upload** them to fix.

### Stripe webhook not working locally
Make sure you're using the Stripe CLI (`stripe listen --forward-to ...`). Dashboard webhooks cannot reach `localhost`.

---

## 📄 License

This project is built for educational and demonstration purposes.

---

**Built with ❤️ using the $0 AI Architecture Stack — Privacy First, Always.**
