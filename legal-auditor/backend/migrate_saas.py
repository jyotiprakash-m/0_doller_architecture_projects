
import sqlite3
from pathlib import Path

# Relative to backend directory
db_path = Path("legal_auditor.db")

if not db_path.exists():
    print(f"Database not found at {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("Applying SaaS migrations...")

try:
    # 1. Add user_id to documents
    cursor.execute("ALTER TABLE documents ADD COLUMN user_id TEXT")
    print("Added user_id to documents")
except sqlite3.OperationalError as e:
    print(f"Documents: {e}")

try:
    # 2. Add user_id to audit_reports
    cursor.execute("ALTER TABLE audit_reports ADD COLUMN user_id TEXT")
    print("Added user_id to audit_reports")
except sqlite3.OperationalError as e:
    print(f"Audit Reports: {e}")

try:
    # 3. Add user_id to chat_history
    cursor.execute("ALTER TABLE chat_history ADD COLUMN user_id TEXT")
    print("Added user_id to chat_history")
except sqlite3.OperationalError as e:
    print(f"Chat History: {e}")

conn.commit()
conn.close()
print("Migration complete. Please restart the backend.")
