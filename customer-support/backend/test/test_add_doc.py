import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from services.doc_processor import extract_text
from services.rag_engine import rag_engine
from services import db
import logging

logging.basicConfig(level=logging.INFO)

doc_id = "b711912b"
conn = db.get_connection()
doc = conn.execute("SELECT * FROM kb_documents WHERE id = ?", (doc_id,)).fetchone()
conn.close()

if doc:
    file_path = doc["file_path"]
    text, count = extract_text(file_path)
    print("Calling add_document")
    chunks = rag_engine.add_document(
        doc_id=doc["id"],
        user_id=doc["user_id"],
        kb_id=doc["kb_id"],
        text=text,
        filename=doc["filename"],
        progress_callback=lambda p: print(f"Progress: {p}")
    )
    print(f"Chunks created: {chunks}")
