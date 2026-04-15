"""
SQLite database service for user metadata, schema projects, and generation jobs.
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
            credits INTEGER DEFAULT 10,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS schema_projects (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            schema_json TEXT NOT NULL DEFAULT '[]',
            table_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS generation_jobs (
            id TEXT PRIMARY KEY,
            schema_project_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            row_count INTEGER DEFAULT 1000,
            rows_generated INTEGER DEFAULT 0,
            table_count INTEGER DEFAULT 0,
            tables_completed INTEGER DEFAULT 0,
            current_table TEXT,
            error_message TEXT,
            generation_plan_json TEXT,
            duckdb_path TEXT,
            seed INTEGER,
            locale TEXT DEFAULT 'en_US',
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (schema_project_id) REFERENCES schema_projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_schema_user ON schema_projects(user_id);
        CREATE INDEX IF NOT EXISTS idx_job_user ON generation_jobs(user_id);
        CREATE INDEX IF NOT EXISTS idx_job_schema ON generation_jobs(schema_project_id);
        CREATE INDEX IF NOT EXISTS idx_job_status ON generation_jobs(status);
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
            (user_id, email, hashed_password, 10, now)
        )
        conn.commit()
        return {"id": user_id, "email": email, "credits": 10}
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

def update_user_credits(user_id: str, amount: int):
    """Increment/Decrement user credits."""
    conn = get_connection()
    conn.execute("UPDATE users SET credits = credits + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    conn.close()


# --- Schema Project CRUD ---

def create_schema_project(user_id: str, name: str, description: str, schema_json: str, table_count: int) -> dict:
    """Create a new schema project."""
    conn = get_connection()
    project_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO schema_projects (id, user_id, name, description, schema_json, table_count, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (project_id, user_id, name, description, schema_json, table_count, now, now)
    )
    conn.commit()
    project = dict(conn.execute("SELECT * FROM schema_projects WHERE id = ?", (project_id,)).fetchone())
    conn.close()
    return project


def get_schema_project(project_id: str) -> dict | None:
    """Get a schema project by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM schema_projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_schema_projects(user_id: str) -> list[dict]:
    """Get all schema projects for a user."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM schema_projects WHERE user_id = ? ORDER BY updated_at DESC", (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_schema_project(project_id: str, name: str, description: str, schema_json: str, table_count: int):
    """Update a schema project."""
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE schema_projects SET name = ?, description = ?, schema_json = ?, table_count = ?, updated_at = ? WHERE id = ?",
        (name, description, schema_json, table_count, now, project_id)
    )
    conn.commit()
    conn.close()


def delete_schema_project(project_id: str):
    """Delete a schema project and its associated data."""
    conn = get_connection()
    conn.execute("DELETE FROM schema_projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()


# --- Generation Job CRUD ---

def create_generation_job(user_id: str, schema_project_id: str, row_count: int, seed: int = None, locale: str = "en_US") -> dict:
    """Create a new generation job."""
    conn = get_connection()
    job_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO generation_jobs 
        (id, schema_project_id, user_id, status, row_count, seed, locale, created_at) 
        VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)""",
        (job_id, schema_project_id, user_id, row_count, seed, locale, now)
    )
    conn.commit()
    job = dict(conn.execute("SELECT * FROM generation_jobs WHERE id = ?", (job_id,)).fetchone())
    conn.close()
    return job


def get_generation_job(job_id: str) -> dict | None:
    """Get a generation job by ID."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM generation_jobs WHERE id = ?", (job_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_generation_jobs(user_id: str) -> list[dict]:
    """Get all generation jobs for a user."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM generation_jobs WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_jobs_for_schema(schema_project_id: str) -> list[dict]:
    """Get all generation jobs for a schema project."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM generation_jobs WHERE schema_project_id = ? ORDER BY created_at DESC",
        (schema_project_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_job_status(job_id: str, status: str, **kwargs):
    """Update a generation job's status and optional fields."""
    conn = get_connection()
    updates = ["status = ?"]
    values = [status]

    for key in ("rows_generated", "tables_completed", "current_table",
                "error_message", "generation_plan_json", "duckdb_path", "table_count"):
        if key in kwargs:
            updates.append(f"{key} = ?")
            values.append(kwargs[key])

    if status == "completed":
        updates.append("completed_at = ?")
        values.append(datetime.now(timezone.utc).isoformat())

    values.append(job_id)
    conn.execute(f"UPDATE generation_jobs SET {', '.join(updates)} WHERE id = ?", values)
    conn.commit()
    conn.close()


def update_job_progress(job_id: str, rows_generated: int, tables_completed: int, current_table: str = None):
    """Update generation progress."""
    conn = get_connection()
    conn.execute(
        "UPDATE generation_jobs SET rows_generated = ?, tables_completed = ?, current_table = ? WHERE id = ?",
        (rows_generated, tables_completed, current_table, job_id)
    )
    conn.commit()
    conn.close()


# --- Dashboard Stats ---

def get_dashboard_stats(user_id: str) -> dict:
    """Get dashboard statistics for a user."""
    conn = get_connection()

    total_projects = conn.execute(
        "SELECT COUNT(*) FROM schema_projects WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    total_jobs = conn.execute(
        "SELECT COUNT(*) FROM generation_jobs WHERE user_id = ?", (user_id,)
    ).fetchone()[0]

    completed_jobs = conn.execute(
        "SELECT COUNT(*) FROM generation_jobs WHERE user_id = ? AND status = 'completed'", (user_id,)
    ).fetchone()[0]

    total_rows = conn.execute(
        "SELECT COALESCE(SUM(rows_generated), 0) FROM generation_jobs WHERE user_id = ? AND status = 'completed'",
        (user_id,)
    ).fetchone()[0]

    recent_projects = conn.execute(
        "SELECT * FROM schema_projects WHERE user_id = ? ORDER BY updated_at DESC LIMIT 5",
        (user_id,)
    ).fetchall()

    recent_jobs = conn.execute(
        """SELECT gj.*, sp.name as project_name
        FROM generation_jobs gj
        JOIN schema_projects sp ON gj.schema_project_id = sp.id
        WHERE gj.user_id = ?
        ORDER BY gj.created_at DESC LIMIT 5""",
        (user_id,)
    ).fetchall()

    user = get_user_by_id(user_id)
    credits = user["credits"] if user else 0

    conn.close()

    return {
        "total_projects": total_projects,
        "total_jobs": total_jobs,
        "total_rows_generated": total_rows,
        "completed_jobs": completed_jobs,
        "user_credits": credits,
        "recent_projects": [dict(r) for r in recent_projects],
        "recent_jobs": [dict(r) for r in recent_jobs],
    }
