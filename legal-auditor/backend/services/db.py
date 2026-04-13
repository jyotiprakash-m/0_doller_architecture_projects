"""
SQLite database service for document metadata, audit reports, and chat history.
All data stays local — privacy first.
"""
import sqlite3
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from config import DB_PATH


def get_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize database tables."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            credits INTEGER DEFAULT 5,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT DEFAULT 'uploaded',
            page_count INTEGER DEFAULT 0,
            chunk_count INTEGER DEFAULT 0,
            uploaded_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS audit_reports (
            id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            audit_type TEXT DEFAULT 'comprehensive',
            status TEXT DEFAULT 'pending',
            executive_summary TEXT,
            overall_risk_score TEXT,
            compliance_score REAL DEFAULT 0.0,
            findings_json TEXT DEFAULT '[]',
            key_clauses_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS chat_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            sources_json TEXT DEFAULT '[]',
            document_ids_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_doc_user ON documents(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_reports(user_id);
        CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_document ON audit_reports(document_id);
        CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_history(created_at);
    """)

    conn.commit()
    conn.close()


# --- User CRUD ---

def create_user(email: str, hashed_password: str) -> dict:
    """Create a new user with initial credits."""
    conn = get_connection()
    user_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    try:
        conn.execute(
            "INSERT INTO users (id, email, hashed_password, credits, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, email, hashed_password, 5, now)
        )
        conn.commit()
        return {"id": user_id, "email": email, "credits": 5}
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

# --- Document CRUD ---

def create_document(user_id: str, filename: str, file_type: str, file_size: int, file_path: str, page_count: int = 0) -> dict:
    """Insert a new document record."""
    conn = get_connection()
    doc_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO documents (id, user_id, filename, file_type, file_size, file_path, status, page_count, uploaded_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 'uploaded', ?, ?, ?)",
        (doc_id, user_id, filename, file_type, file_size, file_path, page_count, now, now)
    )
    conn.commit()
    doc = dict(conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone())
    conn.close()
    return doc


def get_document(doc_id: str) -> dict | None:
    """Get a document by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_documents(user_id: str) -> list[dict]:
    """Get all documents for a specific user."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_document_status(doc_id: str, status: str, chunk_count: int = None):
    """Update document status."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    if chunk_count is not None:
        conn.execute("UPDATE documents SET status = ?, chunk_count = ?, updated_at = ? WHERE id = ?",
                      (status, chunk_count, now, doc_id))
    else:
        conn.execute("UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
                      (status, now, doc_id))
    conn.commit()
    conn.close()


def delete_document(doc_id: str):
    """Delete a document and its associated data."""
    conn = get_connection()
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()


# --- Audit CRUD ---

def create_audit_report(user_id: str, document_id: str, audit_type: str = "comprehensive") -> dict:
    """Create a new audit report record."""
    conn = get_connection()
    report_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO audit_reports (id, user_id, document_id, audit_type, status, created_at) VALUES (?, ?, ?, ?, 'processing', ?)",
        (report_id, user_id, document_id, audit_type, now)
    )
    conn.commit()
    report = dict(conn.execute("SELECT * FROM audit_reports WHERE id = ?", (report_id,)).fetchone())
    conn.close()
    return report


def update_audit_report(report_id: str, summary: str, risk_score: str, compliance_score: float, findings: list, key_clauses: list):
    """Update an audit report with results."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE audit_reports SET
            status = 'completed',
            executive_summary = ?,
            overall_risk_score = ?,
            compliance_score = ?,
            findings_json = ?,
            key_clauses_json = ?,
            completed_at = ?
        WHERE id = ?""",
        (summary, risk_score, compliance_score, json.dumps(findings), json.dumps(key_clauses), now, report_id)
    )
    conn.commit()
    conn.close()


def get_audit_report(document_id: str) -> dict | None:
    """Get the latest audit report for a document."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM audit_reports WHERE document_id = ? ORDER BY created_at DESC LIMIT 1",
        (document_id,)
    ).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["findings"] = json.loads(result.pop("findings_json", "[]"))
        result["key_clauses"] = json.loads(result.pop("key_clauses_json", "[]"))
        return result
    return None


def get_all_audit_reports(user_id: str) -> list[dict]:
    """Get all audit reports for a user."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT ar.*, d.filename as document_name
        FROM audit_reports ar
        JOIN documents d ON ar.document_id = d.id
        WHERE ar.user_id = ?
        ORDER BY ar.created_at DESC
    """, (user_id,)).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["findings"] = json.loads(d.pop("findings_json", "[]"))
        d["key_clauses"] = json.loads(d.pop("key_clauses_json", "[]"))
        results.append(d)
    return results


# --- Chat CRUD ---

def save_chat_message(user_id: str, role: str, content: str, sources: list = None, document_ids: list = None) -> dict:
    """Save a chat message."""
    conn = get_connection()
    msg_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO chat_history (id, user_id, role, content, sources_json, document_ids_json, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (msg_id, user_id, role, content, json.dumps(sources or []), json.dumps(document_ids or []), now)
    )
    conn.commit()
    conn.close()
    return {"id": msg_id, "role": role, "content": content, "sources": sources or [], "created_at": now}


def get_chat_history(user_id: str, limit: int = 50) -> list[dict]:
    """Get recent chat history for a user."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM chat_history WHERE user_id = ? ORDER BY created_at ASC LIMIT ?", (user_id, limit)).fetchall()
    conn.close()
    results = []
    for r in rows:
        d = dict(r)
        d["sources"] = json.loads(d.pop("sources_json", "[]"))
        d["document_ids"] = json.loads(d.pop("document_ids_json", "[]"))
        results.append(d)
    return results


def clear_chat_history(user_id: str):
    """Clear chat history for a user."""
    conn = get_connection()
    conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# --- Dashboard Stats ---

def get_dashboard_stats(user_id: str) -> dict:
    """Get dashboard statistics for a user."""
    conn = get_connection()

    total_docs = conn.execute("SELECT COUNT(*) FROM documents WHERE user_id = ?", (user_id,)).fetchone()[0]
    total_audits = conn.execute("SELECT COUNT(*) FROM audit_reports WHERE user_id = ? AND status = 'completed'", (user_id,)).fetchone()[0]

    # Count high-risk findings across all user audits
    high_risk = 0
    audit_rows = conn.execute("SELECT findings_json FROM audit_reports WHERE user_id = ? AND status = 'completed'", (user_id,)).fetchall()
    for row in audit_rows:
        findings = json.loads(row[0])
        high_risk += sum(1 for f in findings if f.get("risk_level") == "high")

    avg_compliance = conn.execute(
        "SELECT COALESCE(AVG(compliance_score), 0) FROM audit_reports WHERE user_id = ? AND status = 'completed'",
        (user_id,)
    ).fetchone()[0]

    recent_docs = conn.execute("SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT 5", (user_id,)).fetchall()
    recent_audits = conn.execute("""
        SELECT ar.*, d.filename as document_name
        FROM audit_reports ar
        JOIN documents d ON ar.document_id = d.id
        WHERE ar.user_id = ? AND ar.status = 'completed'
        ORDER BY ar.created_at DESC LIMIT 5
    """, (user_id,)).fetchall()

    user = get_user_by_id(user_id)
    credits = user["credits"] if user else 0

    conn.close()

    return {
        "total_documents": total_docs,
        "total_audits": total_audits,
        "high_risk_findings": high_risk,
        "avg_compliance_score": round(avg_compliance, 1),
        "user_credits": credits,
        "recent_documents": [dict(r) for r in recent_docs],
        "recent_audits": [{**dict(r), "findings": json.loads(r["findings_json"])} for r in recent_audits]
    }
