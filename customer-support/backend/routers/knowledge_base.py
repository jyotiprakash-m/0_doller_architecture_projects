"""
Knowledge Base Router — CRUD for knowledge bases and document uploads.
"""
import logging
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel

from config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from services import db
from services.auth_utils import get_current_user_id
from services.rag_engine import rag_engine
from services.doc_processor import extract_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/kb", tags=["Knowledge Base"])


class CreateKBRequest(BaseModel):
    name: str
    description: str = ""


@router.post("")
async def create_kb(req: CreateKBRequest, user_id: str = Depends(get_current_user_id)):
    """Create a new knowledge base."""
    kb = db.create_knowledge_base(user_id=user_id, name=req.name, description=req.description)
    logger.info(f"KB created: {kb['name']} ({kb['id']})")
    return kb


@router.get("")
async def list_kbs(user_id: str = Depends(get_current_user_id)):
    """List all knowledge bases for the current user."""
    return db.get_knowledge_bases(user_id)


@router.get("/{kb_id}")
async def get_kb(kb_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific knowledge base."""
    kb = db.get_knowledge_base(kb_id)
    if not kb or kb["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.post("/{kb_id}/upload")
async def upload_document(kb_id: str, file: UploadFile = File(...),
                          user_id: str = Depends(get_current_user_id)):
    """Upload a document to a knowledge base."""
    # Verify KB ownership
    kb = db.get_knowledge_base(kb_id)
    if not kb or kb["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    # Validate file
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400,
                            detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}")

    # Save file
    kb_dir = UPLOAD_DIR / kb_id
    kb_dir.mkdir(parents=True, exist_ok=True)
    file_path = kb_dir / file.filename

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large. Max: {MAX_UPLOAD_SIZE_MB}MB")

    with open(file_path, "wb") as f:
        f.write(content)

    # Create DB record (set status to processing)
    doc = db.create_kb_document(
        kb_id=kb_id, user_id=user_id, filename=file.filename,
        file_type=ext, file_size=len(content), file_path=str(file_path),
    )
    db.update_kb_document_status(doc["id"], "processing")
    db.update_kb_doc_count(kb_id, delta=1)

    # Publish to Kafka
    try:
        from confluent_kafka import Producer
        import json
        from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC_DOCUMENT_INDEXING

        producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
        
        task_payload = {
            "doc_id": doc["id"],
            "kb_id": kb_id,
            "user_id": user_id,
            "file_path": str(file_path),
            "filename": file.filename
        }
        
        producer.produce(
            KAFKA_TOPIC_DOCUMENT_INDEXING, 
            key=doc["id"], 
            value=json.dumps(task_payload).encode("utf-8")
        )
        producer.flush()
        
        logger.info(f"Published document indexing task to Kafka: {file.filename} ({doc['id']})")
    except Exception as e:
        logger.error(f"Failed to publish Kafka message: {e}")
        db.update_kb_document_status(doc["id"], "error")
        raise HTTPException(status_code=500, detail="Failed to queue document for processing.")

    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=202,
        content={**doc, "status": "processing", "message": "Document queued for background indexing."}
    )


@router.get("/{kb_id}/documents")
async def list_documents(kb_id: str, user_id: str = Depends(get_current_user_id)):
    """List all documents in a knowledge base."""
    kb = db.get_knowledge_base(kb_id)
    if not kb or kb["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return db.get_kb_documents(kb_id)


@router.delete("/{kb_id}/documents/{doc_id}")
async def delete_document(kb_id: str, doc_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a document from a knowledge base."""
    doc = db.get_kb_document(doc_id)
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    rag_engine.delete_document(doc_id)
    if doc.get("file_path"):
        Path(doc["file_path"]).unlink(missing_ok=True)
    db.delete_kb_document(doc_id)
    db.update_kb_doc_count(kb_id, delta=-1)

    return {"status": "deleted", "doc_id": doc_id}


from pydantic import BaseModel

from pydantic import BaseModel
from typing import List, Dict, Any

class DocChatRequest(BaseModel):
    question: str
    chat_history: List[Dict[str, Any]] = []

@router.post("/{kb_id}/documents/{doc_id}/chat")
async def chat_with_document(
    kb_id: str, 
    doc_id: str, 
    request: DocChatRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Ask a question about a specific document."""
    # Verify ownership
    doc = db.get_kb_document(doc_id)
    if not doc or doc["user_id"] != user_id or doc["kb_id"] != kb_id:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc["status"] != "indexed":
        raise HTTPException(status_code=400, detail="Document is not fully indexed yet.")

    try:
        # If there's chat history, append the last few messages for context
        search_query = request.question
        if request.chat_history:
            recent_history = request.chat_history[-2:] # Take last 2 messages (usually user + ai)
            context_str = " | ".join([f"{msg['role']}: {msg['content']}" for msg in recent_history])
            search_query = f"Previous conversation context: {context_str}. \n\nNew Question: {request.question}"

        # Strict RAG query against only this document
        result = rag_engine.query(
            question=search_query,
            user_id=user_id,
            kb_id=kb_id,
            doc_id=doc_id,
            top_k=3
        )
        return result
    except Exception as e:
        logger.error(f"Doc chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{kb_id}")
async def delete_kb(kb_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a knowledge base and all its documents."""
    kb = db.get_knowledge_base(kb_id)
    if not kb or kb["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    rag_engine.delete_kb_documents(kb_id)
    kb_dir = UPLOAD_DIR / kb_id
    if kb_dir.exists():
        shutil.rmtree(kb_dir)
    db.delete_knowledge_base(kb_id)

    return {"status": "deleted", "kb_id": kb_id}
