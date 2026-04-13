"""
Document management API endpoints.
Upload, list, get, and delete legal documents.
"""
import os
import logging
from pathlib import Path
from config import DATA_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from services import db
from services.document_processor import extract_text, save_uploaded_file
from services.rag_engine import rag_engine
from services.auth_utils import get_current_user_id
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user_id)
):
    """
    Upload a legal document (PDF, DOCX, TXT).
    The document is processed, chunked, and indexed in the local vector store.
    NO data leaves this machine.
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE_MB}MB"
        )

    try:
        # Save file locally
        file_path = save_uploaded_file(content, file.filename, str(DATA_DIR))
        logger.info(f"Saved file: {file_path}")

        # Create database record
        doc = db.create_document(
            user_id=user_id,
            filename=file.filename,
            file_type=file_ext,
            file_size=file_size,
            file_path=file_path,
        )
        doc_id = doc["id"]

        # Extract text
        db.update_document_status(doc_id, "processing")
        extracted_text, page_count = extract_text(file_path, file_ext)

        # Update page count
        conn = db.get_connection()
        conn.execute("UPDATE documents SET page_count = ? WHERE id = ?", (page_count, doc_id))
        conn.commit()
        conn.close()

        # Index in vector store (local ChromaDB)
        try:
            chunk_count = rag_engine.add_document(doc_id, user_id, extracted_text, file.filename)
            db.update_document_status(doc_id, "indexed", chunk_count=chunk_count)
        except Exception as e:
            logger.warning(f"RAG indexing failed (Ollama may not be running): {e}")
            db.update_document_status(doc_id, "uploaded")
            chunk_count = 0

        return {
            "id": doc_id,
            "filename": file.filename,
            "file_type": file_ext,
            "file_size": file_size,
            "status": "indexed" if chunk_count > 0 else "uploaded",
            "uploaded_at": doc["uploaded_at"],
            "page_count": page_count,
            "chunk_count": chunk_count,
            "message": f"Document '{file.filename}' processed successfully. {chunk_count} chunks indexed locally."
        }

    except ValueError as e:
        db.update_document_status(doc_id, "error")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")


@router.get("")
async def list_documents(user_id: str = Depends(get_current_user_id)):
    """List all uploaded documents for the current user."""
    docs = db.get_all_documents(user_id)
    return {
        "documents": docs,
        "total": len(docs)
    }


@router.get("/{doc_id}")
async def get_document(doc_id: str, user_id: str = Depends(get_current_user_id)):
    """Get document details by ID."""
    doc = db.get_document(doc_id)
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/{doc_id}")
async def delete_document(doc_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a document and its vectors."""
    doc = db.get_document(doc_id)
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove vectors from ChromaDB
    try:
        rag_engine.delete_document(doc_id)
    except Exception as e:
        logger.warning(f"Could not remove vectors: {e}")

    # Remove file from disk
    try:
        if os.path.exists(doc["file_path"]):
            os.remove(doc["file_path"])
    except Exception as e:
        logger.warning(f"Could not remove file: {e}")

    # Remove from database
    db.delete_document(doc_id)

    return {"message": f"Document '{doc['filename']}' deleted successfully."}
