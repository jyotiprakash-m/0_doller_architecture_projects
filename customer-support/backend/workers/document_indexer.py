import os
import sys
import json
import logging
from pathlib import Path

# Add the parent directory to sys.path so we can import from backend modules
sys.path.append(str(Path(__file__).parent.parent))

from confluent_kafka import Consumer, KafkaError, KafkaException
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_DOCUMENT_INDEXING
from services import db
from services.rag_engine import rag_engine
from services.doc_processor import extract_text

import nest_asyncio
nest_asyncio.apply()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | KAFKA WORKER | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

def process_message(msg_value):
    """Process a single document indexing task from Kafka."""
    try:
        payload = json.loads(msg_value)
        doc_id = payload.get("doc_id")
        kb_id = payload.get("kb_id")
        user_id = payload.get("user_id")
        file_path = payload.get("file_path")
        filename = payload.get("filename")

        logger.info(f"Processing document: {filename} ({doc_id})")

        # 1. Extract Text (10% progress)
        db.update_kb_document_progress(doc_id, 10)
        logger.info(f"[{doc_id}] Step 1/3: Extracting text from {file_path}...")
        text, page_count = extract_text(file_path)
        logger.info(f"[{doc_id}] Step 1/3 Complete: Extracted {page_count} pages of text.")

        # 2. Add to RAG Engine — chunking, metadata extraction, and embedding
        # Progress updates happen inside rag_engine.add_document() via callback
        db.update_kb_document_progress(doc_id, 20)
        logger.info(f"[{doc_id}] Step 2/3: Sending to RAG Engine for chunking & metadata extraction...")
        chunk_count = rag_engine.add_document(
            doc_id=doc_id, 
            user_id=user_id, 
            kb_id=kb_id,
            text=text, 
            filename=filename,
            progress_callback=lambda pct: db.update_kb_document_progress(doc_id, pct)
        )

        # 3. Update DB Status
        logger.info(f"Indexing complete! {chunk_count} chunks created. Updating DB...")
        db.update_kb_document_status(doc_id, "indexed", chunk_count)
        
        logger.info(f"Successfully processed {filename}!")

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        if 'doc_id' in locals() and doc_id:
            logger.info(f"Marking document {doc_id} as error in DB.")
            db.update_kb_document_status(doc_id, "error")

def main():
    """Main consumer loop."""
    logger.info("Initializing RAG Engine...")
    rag_engine.initialize()
    logger.info("RAG Engine ready.")

    conf = {
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'group.id': 'document_indexer_group',
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False,      # Disable auto-commit to prevent message loss
        'max.poll.interval.ms': 3600000,  # Allow up to 1 hour for local LLM processing
        'session.timeout.ms': 45000       # Keep session alive if poll interval is respected
    }

    consumer = Consumer(conf)
    
    try:
        consumer.subscribe([KAFKA_TOPIC_DOCUMENT_INDEXING])
        logger.info(f"Subscribed to topic: {KAFKA_TOPIC_DOCUMENT_INDEXING}")
        logger.info(f"Kafka Document Indexer Worker Started! Waiting for tasks on {KAFKA_BOOTSTRAP_SERVERS}...")

        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # End of partition event
                    continue
                elif msg.error().code() == KafkaError.UNKNOWN_TOPIC_OR_PART:
                    # Topic doesn't exist yet (will be auto-created when producer sends first message)
                    logger.debug("Topic not available yet. Waiting for first message...")
                    continue
                else:
                    logger.error(f"Kafka error: {msg.error()}")
                    raise KafkaException(msg.error())
            else:
                # Valid message received
                logger.info(f"Received task! Offset: {msg.offset()}")
                process_message(msg.value().decode('utf-8'))
                # Manually commit offset after processing is complete
                consumer.commit(msg)

    except KeyboardInterrupt:
        logger.info("Worker shutting down gracefully...")
    finally:
        consumer.close()
        logger.info("Consumer closed.")

if __name__ == "__main__":
    main()
