# 🎯 SupportSim AI — Customer Support Agent Training Platform

AI-powered training platform that simulates customer interactions, evaluates agent responses, and provides personalized coaching — all running **locally at $0 cost**.

## Architecture

| Layer               | Technology                    |
| ------------------- | ----------------------------- |
| Frontend            | Streamlit (Python)            |
| Backend             | Python 3, FastAPI, Uvicorn    |
| Agent Orchestration | LangGraph                     |
| AI / LLM            | Ollama, LLaMA 3.2B            |
| Embeddings          | Nomic-Embed-Text              |
| RAG Framework       | LlamaIndex                    |
| Vector Database     | ChromaDB (persistent, local)  |
| Relational Database | SQLite                        |
| Authentication      | JWT (JSON Web Tokens), bcrypt |

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com/) installed and running

### 1. Pull AI Models

```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 2. Setup Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
cp .env.example .env      # Edit as needed
python main.py
```

### 3. Start Frontend

Open a **new terminal window/tab**, activate the backend virtual environment, and run the Streamlit app:

```bash
cd frontend
source ../backend/venv/bin/activate  # macOS/Linux
streamlit run app.py
```

### 4. Open in Browser

- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:8501

## Features

- 📚 **Knowledge Base** — Upload company docs (PDF, DOCX, TXT) for RAG-powered training
- 🎭 **AI Customer Simulation** — Realistic customer personas with emotional state evolution
- 🤖 **Auto-Scenario Generation** — AI creates training scenarios from your KB content
- 📊 **AI Evaluation** — Scored on empathy, accuracy, resolution, and communication
- 💡 **Coaching Feedback** — Personalized improvement suggestions with alternative phrasings
- 📈 **Analytics Dashboard** — Track progress, score trends, and leaderboard

## Project Structure

```
customer-support/
├── backend/
│   ├── config.py              # Central configuration
│   ├── main.py                # FastAPI entry point
│   ├── requirements.txt       # Python dependencies
│   ├── routers/               # API endpoints
│   │   ├── auth.py            # Login, Register, JWT
│   │   ├── knowledge_base.py  # KB CRUD + doc upload
│   │   ├── simulation.py      # Session management + chat
│   │   ├── evaluation.py      # Scoring + feedback
│   │   └── analytics.py       # Dashboard data
│   └── services/
│       ├── db.py              # SQLite operations
│       ├── auth_utils.py      # JWT helpers
│       ├── rag_engine.py      # LlamaIndex + ChromaDB
│       ├── doc_processor.py   # Document extraction
│       └── agents/
│           ├── orchestrator.py     # LangGraph coordinator
│           ├── customer_agent.py   # Customer persona sim
│           ├── evaluator_agent.py  # Response evaluation
│           ├── feedback_agent.py   # Coaching feedback
│           └── scenario_generator.py
├── frontend/
│   ├── app.py                 # Streamlit main entry
│   ├── pages/                 # Multi-page Streamlit app
│   └── utils/                 # API client + styles
└── .gitignore
```
