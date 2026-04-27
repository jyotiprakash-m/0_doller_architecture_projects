"""
SQLite database service for SupportSim AI.
Manages users, knowledge bases, scenarios, training sessions, evaluations.
All data stays local — privacy first.
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from config import DB_PATH


def get_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize all database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        -- Users table (multi-tenant auth)
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            full_name TEXT DEFAULT '',
            role TEXT DEFAULT 'trainee',
            credits REAL DEFAULT 10.0,
            stripe_customer_id TEXT,
            subscription_status TEXT DEFAULT 'inactive',
            current_period_end TEXT,
            created_at TEXT NOT NULL
        );

        -- Knowledge Bases (company-specific knowledge)
        CREATE TABLE IF NOT EXISTS knowledge_bases (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            doc_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- KB Documents (uploaded files for RAG)
        CREATE TABLE IF NOT EXISTS kb_documents (
            id TEXT PRIMARY KEY,
            kb_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            chunk_count INTEGER DEFAULT 0,
            status TEXT DEFAULT 'uploaded',
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Training Scenarios (customer personas)
        CREATE TABLE IF NOT EXISTS scenarios (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            kb_id TEXT,
            persona_name TEXT NOT NULL,
            persona_description TEXT NOT NULL,
            difficulty TEXT DEFAULT 'medium',
            category TEXT DEFAULT 'general_inquiry',
            issue_description TEXT DEFAULT '',
            expected_resolution TEXT DEFAULT '',
            initial_emotional_state TEXT DEFAULT 'neutral',
            is_auto_generated INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE SET NULL
        );

        -- Training Sessions
        CREATE TABLE IF NOT EXISTS training_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            scenario_id TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            message_count INTEGER DEFAULT 0,
            current_emotional_state TEXT DEFAULT 'neutral',
            started_at TEXT NOT NULL,
            ended_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
        );

        -- Session Messages (chat log)
        CREATE TABLE IF NOT EXISTS session_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            emotional_state TEXT DEFAULT 'neutral',
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES training_sessions(id) ON DELETE CASCADE
        );

        -- Evaluations (AI scoring)
        CREATE TABLE IF NOT EXISTS evaluations (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL,
            overall_score REAL DEFAULT 0.0,
            empathy_score REAL DEFAULT 0.0,
            accuracy_score REAL DEFAULT 0.0,
            resolution_score REAL DEFAULT 0.0,
            communication_score REAL DEFAULT 0.0,
            feedback_json TEXT DEFAULT '{}',
            strengths_json TEXT DEFAULT '[]',
            improvements_json TEXT DEFAULT '[]',
            ideal_responses_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES training_sessions(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_kb_user ON knowledge_bases(user_id);
        CREATE INDEX IF NOT EXISTS idx_kb_docs_kb ON kb_documents(kb_id);
        CREATE INDEX IF NOT EXISTS idx_kb_docs_user ON kb_documents(user_id);
        CREATE INDEX IF NOT EXISTS idx_scenarios_user ON scenarios(user_id);
        CREATE INDEX IF NOT EXISTS idx_scenarios_kb ON scenarios(kb_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_user ON training_sessions(user_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_scenario ON training_sessions(scenario_id);
        CREATE INDEX IF NOT EXISTS idx_messages_session ON session_messages(session_id);
        CREATE INDEX IF NOT EXISTS idx_eval_session ON evaluations(session_id);
        CREATE INDEX IF NOT EXISTS idx_eval_user ON evaluations(user_id);
    """)

    # Schema migrations for existing DB
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN stripe_customer_id TEXT")
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_status TEXT DEFAULT 'inactive'")
        cursor.execute("ALTER TABLE users ADD COLUMN current_period_end TEXT")
    except sqlite3.OperationalError:
        pass  # Columns likely already exist

    try:
        cursor.execute("ALTER TABLE kb_documents ADD COLUMN progress INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


# ==========================================
# User CRUD
# ==========================================

def create_user(email: str, hashed_password: str, full_name: str = "", role: str = "trainee") -> dict:
    """Create a new user with starter credits."""
    conn = get_connection()
    user_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            "INSERT INTO users (id, email, hashed_password, full_name, role, credits, subscription_status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'inactive', ?)",
            (user_id, email, hashed_password, full_name, role, 10.0, now)
        )
        conn.commit()
        return {"id": user_id, "email": email, "full_name": full_name, "role": role, "credits": 10.0, "subscription_status": "inactive"}
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email: str) -> dict | None:
    """Get user by email."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict | None:
    """Get user by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_user_credits(user_id: str, amount: float):
    """Increment/Decrement user credits."""
    conn = get_connection()
    conn.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def update_stripe_subscription(user_id: str, customer_id: str, status: str, period_end: str, credits_to_add: float = 0):
    """Update user's Stripe subscription info."""
    conn = get_connection()
    if credits_to_add > 0:
        conn.execute(
            "UPDATE users SET stripe_customer_id = ?, subscription_status = ?, current_period_end = ?, credits = credits + ? WHERE id = ?",
            (customer_id, status, period_end, credits_to_add, user_id)
        )
    else:
        conn.execute(
            "UPDATE users SET stripe_customer_id = ?, subscription_status = ?, current_period_end = ? WHERE id = ?",
            (customer_id, status, period_end, user_id)
        )
    conn.commit()
    conn.close()


def get_user_credits(user_id: str) -> float:
    """Get current credit balance for a user."""
    user = get_user_by_id(user_id)
    return user["credits"] if user else 0.0


# ==========================================
# Knowledge Base CRUD
# ==========================================

def create_knowledge_base(user_id: str, name: str, description: str = "") -> dict:
    """Create a new knowledge base."""
    conn = get_connection()
    kb_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO knowledge_bases (id, user_id, name, description, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (kb_id, user_id, name, description, now, now)
    )
    conn.commit()
    kb = dict(conn.execute("SELECT * FROM knowledge_bases WHERE id = ?", (kb_id,)).fetchone())
    conn.close()
    return kb


def get_knowledge_bases(user_id: str) -> list[dict]:
    """Get all knowledge bases for a user."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM knowledge_bases WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_knowledge_base(kb_id: str) -> dict | None:
    """Get a knowledge base by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM knowledge_bases WHERE id = ?", (kb_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_kb_doc_count(kb_id: str, delta: int = 1):
    """Update the document count for a knowledge base."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE knowledge_bases SET doc_count = doc_count + ?, updated_at = ? WHERE id = ?",
        (delta, now, kb_id)
    )
    conn.commit()
    conn.close()


def delete_knowledge_base(kb_id: str):
    """Delete a knowledge base and all its documents."""
    conn = get_connection()
    conn.execute("DELETE FROM knowledge_bases WHERE id = ?", (kb_id,))
    conn.commit()
    conn.close()


# ==========================================
# KB Document CRUD
# ==========================================

def create_kb_document(kb_id: str, user_id: str, filename: str, file_type: str,
                       file_size: int, file_path: str) -> dict:
    """Insert a new KB document record."""
    conn = get_connection()
    doc_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO kb_documents (id, kb_id, user_id, filename, file_type, file_size, file_path, uploaded_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (doc_id, kb_id, user_id, filename, file_type, file_size, file_path, now)
    )
    conn.commit()
    doc = dict(conn.execute("SELECT * FROM kb_documents WHERE id = ?", (doc_id,)).fetchone())
    conn.close()
    return doc


def get_kb_documents(kb_id: str) -> list[dict]:
    """Get all documents in a knowledge base."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM kb_documents WHERE kb_id = ? ORDER BY uploaded_at DESC",
        (kb_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_kb_document(doc_id: str) -> dict | None:
    """Get a KB document by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM kb_documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_kb_document_status(doc_id: str, status: str, chunk_count: int = None):
    """Update KB document status and optionally chunk count."""
    conn = get_connection()
    if chunk_count is not None:
        conn.execute(
            "UPDATE kb_documents SET status = ?, chunk_count = ?, progress = 100 WHERE id = ?",
            (status, chunk_count, doc_id)
        )
    else:
        conn.execute("UPDATE kb_documents SET status = ? WHERE id = ?", (status, doc_id))
    conn.commit()
    conn.close()


def update_kb_document_progress(doc_id: str, progress: int):
    """Update KB document indexing progress (0-100)."""
    conn = get_connection()
    conn.execute("UPDATE kb_documents SET progress = ? WHERE id = ?", (progress, doc_id))
    conn.commit()
    conn.close()


def delete_kb_document(doc_id: str):
    """Delete a KB document."""
    conn = get_connection()
    conn.execute("DELETE FROM kb_documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()


# ==========================================
# Scenario CRUD
# ==========================================

def create_scenario(user_id: str, persona_name: str, persona_description: str,
                    difficulty: str = "medium", category: str = "general_inquiry",
                    issue_description: str = "", expected_resolution: str = "",
                    initial_emotional_state: str = "neutral",
                    kb_id: str = None, is_auto_generated: bool = False) -> dict:
    """Create a new training scenario."""
    conn = get_connection()
    scenario_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO scenarios (id, user_id, kb_id, persona_name, persona_description, "
        "difficulty, category, issue_description, expected_resolution, "
        "initial_emotional_state, is_auto_generated, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (scenario_id, user_id, kb_id, persona_name, persona_description,
         difficulty, category, issue_description, expected_resolution,
         initial_emotional_state, int(is_auto_generated), now)
    )
    conn.commit()
    scenario = dict(conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone())
    conn.close()
    return scenario


def get_scenarios(user_id: str, kb_id: str = None) -> list[dict]:
    """Get all scenarios for a user, optionally filtered by KB."""
    conn = get_connection()
    if kb_id:
        rows = conn.execute(
            "SELECT * FROM scenarios WHERE user_id = ? AND kb_id = ? ORDER BY created_at DESC",
            (user_id, kb_id)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM scenarios WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_scenario(scenario_id: str) -> dict | None:
    """Get a scenario by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_scenario(scenario_id: str):
    """Delete a scenario."""
    conn = get_connection()
    conn.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
    conn.commit()
    conn.close()


# ==========================================
# Training Session CRUD
# ==========================================

def create_training_session(user_id: str, scenario_id: str) -> dict:
    """Create a new training session."""
    conn = get_connection()
    session_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()

    # Get scenario's initial emotional state
    scenario = get_scenario(scenario_id)
    emotional_state = scenario.get("initial_emotional_state", "neutral") if scenario else "neutral"

    conn.execute(
        "INSERT INTO training_sessions (id, user_id, scenario_id, status, "
        "current_emotional_state, started_at) VALUES (?, ?, ?, 'active', ?, ?)",
        (session_id, user_id, scenario_id, emotional_state, now)
    )
    conn.commit()
    session = dict(conn.execute("SELECT * FROM training_sessions WHERE id = ?", (session_id,)).fetchone())
    conn.close()
    return session


def get_training_session(session_id: str) -> dict | None:
    """Get a training session by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM training_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_training_sessions(user_id: str, status: str = None) -> list[dict]:
    """Get training sessions for a user."""
    conn = get_connection()
    if status:
        rows = conn.execute(
            "SELECT ts.*, s.persona_name, s.category, s.difficulty "
            "FROM training_sessions ts "
            "JOIN scenarios s ON ts.scenario_id = s.id "
            "WHERE ts.user_id = ? AND ts.status = ? "
            "ORDER BY ts.started_at DESC",
            (user_id, status)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT ts.*, s.persona_name, s.category, s.difficulty "
            "FROM training_sessions ts "
            "JOIN scenarios s ON ts.scenario_id = s.id "
            "WHERE ts.user_id = ? "
            "ORDER BY ts.started_at DESC",
            (user_id,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_training_session(session_id: str, status: str = None,
                            emotional_state: str = None,
                            increment_messages: bool = False):
    """Update a training session."""
    conn = get_connection()
    updates = []
    params = []

    if status:
        updates.append("status = ?")
        params.append(status)
        if status in ("completed", "abandoned"):
            updates.append("ended_at = ?")
            params.append(datetime.now(timezone.utc).isoformat())

    if emotional_state:
        updates.append("current_emotional_state = ?")
        params.append(emotional_state)

    if increment_messages:
        updates.append("message_count = message_count + 1")

    if updates:
        params.append(session_id)
        conn.execute(
            f"UPDATE training_sessions SET {', '.join(updates)} WHERE id = ?",
            params
        )
        conn.commit()
    conn.close()


# ==========================================
# Session Message CRUD
# ==========================================

def add_session_message(session_id: str, role: str, content: str,
                        emotional_state: str = "neutral") -> dict:
    """Add a message to a training session."""
    conn = get_connection()
    msg_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO session_messages (id, session_id, role, content, emotional_state, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (msg_id, session_id, role, content, emotional_state, now)
    )
    conn.commit()
    conn.close()

    # Increment message count on session
    update_training_session(session_id, increment_messages=True)

    return {"id": msg_id, "role": role, "content": content,
            "emotional_state": emotional_state, "timestamp": now}


def get_session_messages(session_id: str) -> list[dict]:
    """Get all messages for a training session."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM session_messages WHERE session_id = ? ORDER BY timestamp ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ==========================================
# Evaluation CRUD
# ==========================================

def create_evaluation(session_id: str, user_id: str, overall_score: float,
                      empathy_score: float, accuracy_score: float,
                      resolution_score: float, communication_score: float,
                      feedback: dict = None, strengths: list = None,
                      improvements: list = None, ideal_responses: list = None) -> dict:
    """Create an evaluation for a training session."""
    conn = get_connection()
    eval_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO evaluations (id, session_id, user_id, overall_score, "
        "empathy_score, accuracy_score, resolution_score, communication_score, "
        "feedback_json, strengths_json, improvements_json, ideal_responses_json, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (eval_id, session_id, user_id, overall_score, empathy_score,
         accuracy_score, resolution_score, communication_score,
         json.dumps(feedback or {}), json.dumps(strengths or []),
         json.dumps(improvements or []), json.dumps(ideal_responses or []), now)
    )
    conn.commit()
    evaluation = dict(conn.execute("SELECT * FROM evaluations WHERE id = ?", (eval_id,)).fetchone())
    conn.close()
    return evaluation


def get_evaluation(session_id: str) -> dict | None:
    """Get evaluation for a training session."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM evaluations WHERE session_id = ?",
        (session_id,)
    ).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["feedback"] = json.loads(result.pop("feedback_json", "{}"))
        result["strengths"] = json.loads(result.pop("strengths_json", "[]"))
        result["improvements"] = json.loads(result.pop("improvements_json", "[]"))
        result["ideal_responses"] = json.loads(result.pop("ideal_responses_json", "[]"))
        return result
    return None


def get_user_evaluations(user_id: str, limit: int = 50) -> list[dict]:
    """Get all evaluations for a user."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT e.*, ts.scenario_id, ts.status, s.persona_name, s.category, s.difficulty "
        "FROM evaluations e "
        "JOIN training_sessions ts ON e.session_id = ts.id "
        "JOIN scenarios s ON ts.scenario_id = s.id "
        "WHERE e.user_id = ? "
        "ORDER BY e.created_at DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["feedback"] = json.loads(d.pop("feedback_json", "{}"))
        d["strengths"] = json.loads(d.pop("strengths_json", "[]"))
        d["improvements"] = json.loads(d.pop("improvements_json", "[]"))
        d["ideal_responses"] = json.loads(d.pop("ideal_responses_json", "[]"))
        results.append(d)
    return results


# ==========================================
# Dashboard / Analytics
# ==========================================

def get_dashboard_stats(user_id: str) -> dict:
    """Get dashboard statistics for a user."""
    conn = get_connection()

    total_sessions = conn.execute(
        "SELECT COUNT(*) FROM training_sessions WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    completed_sessions = conn.execute(
        "SELECT COUNT(*) FROM training_sessions WHERE user_id = ? AND status = 'completed'",
        (user_id,)
    ).fetchone()[0]

    total_kbs = conn.execute(
        "SELECT COUNT(*) FROM knowledge_bases WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    total_scenarios = conn.execute(
        "SELECT COUNT(*) FROM scenarios WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    # Average scores
    avg_scores = conn.execute(
        "SELECT COALESCE(AVG(overall_score), 0), COALESCE(AVG(empathy_score), 0), "
        "COALESCE(AVG(accuracy_score), 0), COALESCE(AVG(resolution_score), 0), "
        "COALESCE(AVG(communication_score), 0) "
        "FROM evaluations WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    # Best category
    best_category = conn.execute(
        "SELECT s.category, AVG(e.overall_score) as avg_score "
        "FROM evaluations e "
        "JOIN training_sessions ts ON e.session_id = ts.id "
        "JOIN scenarios s ON ts.scenario_id = s.id "
        "WHERE e.user_id = ? "
        "GROUP BY s.category ORDER BY avg_score DESC LIMIT 1",
        (user_id,)
    ).fetchone()

    # Recent sessions with scores
    recent_sessions = conn.execute(
        "SELECT ts.*, s.persona_name, s.category, s.difficulty, "
        "e.overall_score, e.empathy_score, e.accuracy_score "
        "FROM training_sessions ts "
        "JOIN scenarios s ON ts.scenario_id = s.id "
        "LEFT JOIN evaluations e ON ts.id = e.session_id "
        "WHERE ts.user_id = ? "
        "ORDER BY ts.started_at DESC LIMIT 10",
        (user_id,)
    ).fetchall()

    # Score trend (last 20 evaluations)
    score_trend = conn.execute(
        "SELECT e.overall_score, e.created_at "
        "FROM evaluations e "
        "WHERE e.user_id = ? "
        "ORDER BY e.created_at ASC LIMIT 20",
        (user_id,)
    ).fetchall()

    user = get_user_by_id(user_id)
    credits = user["credits"] if user else 0

    conn.close()

    return {
        "total_sessions": total_sessions,
        "completed_sessions": completed_sessions,
        "total_knowledge_bases": total_kbs,
        "total_scenarios": total_scenarios,
        "avg_overall_score": round(avg_scores[0], 1),
        "avg_empathy_score": round(avg_scores[1], 1),
        "avg_accuracy_score": round(avg_scores[2], 1),
        "avg_resolution_score": round(avg_scores[3], 1),
        "avg_communication_score": round(avg_scores[4], 1),
        "best_category": dict(best_category) if best_category else None,
        "user_credits": credits,
        "recent_sessions": [dict(r) for r in recent_sessions],
        "score_trend": [{"score": r[0], "date": r[1]} for r in score_trend],
    }


def get_progress_data(user_id: str) -> list[dict]:
    """Get evaluation progress data for charts."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT e.overall_score, e.empathy_score, e.accuracy_score, "
        "e.resolution_score, e.communication_score, e.created_at, "
        "s.category, s.difficulty "
        "FROM evaluations e "
        "JOIN training_sessions ts ON e.session_id = ts.id "
        "JOIN scenarios s ON ts.scenario_id = s.id "
        "WHERE e.user_id = ? "
        "ORDER BY e.created_at ASC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
