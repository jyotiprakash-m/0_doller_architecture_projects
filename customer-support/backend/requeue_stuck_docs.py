import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from services import db
from confluent_kafka import Producer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_DOCUMENT_INDEXING

conn = db.get_connection()
docs = conn.execute("SELECT * FROM kb_documents WHERE status = 'processing' AND progress = 0;").fetchall()

if not docs:
    print("No stuck documents found.")
else:
    producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    for doc in docs:
        task_payload = {
            "doc_id": doc["id"],
            "kb_id": doc["kb_id"],
            "user_id": doc["user_id"],
            "file_path": doc["file_path"],
            "filename": doc["filename"]
        }
        producer.produce(
            KAFKA_TOPIC_DOCUMENT_INDEXING, 
            key=doc["id"], 
            value=json.dumps(task_payload).encode("utf-8")
        )
        print(f"Re-queued document: {doc['filename']} ({doc['id']})")
    
    producer.flush()
    print("Done!")

conn.close()
