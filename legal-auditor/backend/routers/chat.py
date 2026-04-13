"""
Chat API endpoints.
RAG-powered Q&A over legal documents using local LLM.
"""
import logging
from pydantic import BaseModel
from typing import Optional

from services import db
from services.rag_engine import rag_engine
from services.auth_utils import get_current_user_id
from fastapi import APIRouter, HTTPException, Depends

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    query: str
    document_ids: Optional[list[str]] = None


@router.post("")
async def chat(
    request: ChatRequest, 
    user_id: str = Depends(get_current_user_id)
):
    """
    Ask a question about your legal documents.
    Uses RAG pipeline (LlamaIndex + ChromaDB + Ollama) — all local.
    Responses include source citations from your documents.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Verify document ownership if specific docs requested
    if request.document_ids:
        for doc_id in request.document_ids:
            doc = db.get_document(doc_id)
            if not doc or doc["user_id"] != user_id:
                raise HTTPException(status_code=403, detail=f"Access denied to document: {doc_id}")

    # Check user credits
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if float(user["credits"]) < 0.1:
        raise HTTPException(
            status_code=402, 
            detail="Insufficient credits. Please top up to ask more questions."
        )

    try:
        # Save user message
        db.save_chat_message(user_id, "user", request.query, document_ids=request.document_ids)

        # Query RAG pipeline (local inference)
        result = rag_engine.query(
            question=request.query,
            user_id=user_id,
            doc_ids=request.document_ids,
        )

        # Deduct 0.1 chat credit upon success
        db.update_user_credits(user_id, -0.1)

        # Save assistant response
        db.save_chat_message(
            user_id,
            "assistant",
            result["answer"],
            sources=result["sources"],
            document_ids=request.document_ids,
        )

        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "confidence": result.get("confidence"),
        }

    except Exception as e:
        logger.error(f"Chat query failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}. Make sure Ollama is running."
        )


@router.get("/history")
async def get_history(user_id: str = Depends(get_current_user_id)):
    """Get chat history for current user."""
    messages = db.get_chat_history(user_id)
    return {"messages": messages}


@router.delete("/history")
async def clear_history(user_id: str = Depends(get_current_user_id)):
    """Clear chat history for current user."""
    db.clear_chat_history(user_id)
    return {"message": "Chat history cleared."}
