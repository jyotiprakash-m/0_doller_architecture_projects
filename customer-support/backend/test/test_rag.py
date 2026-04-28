import sys
import logging

logging.basicConfig(level=logging.DEBUG)

from services.rag_engine import rag_engine

try:
    rag_engine.add_document("doc1", "user1", "kb1", "This is a test document text.", "test.txt")
    print("Success")
except Exception as e:
    logging.exception("Error occurred")
