import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.doc_processor import extract_text
from services import db
import logging

logging.basicConfig(level=logging.INFO)

doc_id = "b711912b"
# The DB has the document, but we don't have its file_path offhand.
conn = db.get_connection()
doc = conn.execute("SELECT * FROM kb_documents WHERE id = ?", (doc_id,)).fetchone()
conn.close()

if not doc:
    print("Doc not found")
else:
    file_path = doc["file_path"]
    print(f"Extracting {file_path}")
    text, count = extract_text(file_path)
    print(f"Text extracted. Pages: {count}. Text length: {len(text)}")
