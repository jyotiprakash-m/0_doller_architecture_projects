import hmac
import hashlib
import json
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from config import GITHUB_WEBHOOK_SECRET
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def verify_signature(payload_body: bytes, signature_header: str):
    if not GITHUB_WEBHOOK_SECRET:
        return True # Skip verification if secret not set (not recommended for production)
    
    if not signature_header:
        raise HTTPException(status_code=403, detail="x-hub-signature-256 header is missing")
    
    hash_object = hmac.new(GITHUB_WEBHOOK_SECRET.encode(), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + hash_object.hexdigest()
    
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=403, detail="Request signatures didn't match!")

@router.post("/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    db: Session = Depends(get_db)
):
    payload_body = await request.body()
    verify_signature(payload_body, x_hub_signature_256)
    
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event", "ping")
    
    logger.info(f"Received GitHub event: {event}")
    
    if event == "ping":
        return {"msg": "pong"}
    
    if event == "pull_request":
        action = payload.get("action")
        pr_number = payload.get("number")
        repo_name = payload.get("repository", {}).get("full_name")
        
        logger.info(f"PR Event: {action} on {repo_name} #{pr_number}")
        
        # Trigger Ghost-Editor logic here
        # task_id = agent_service.trigger_doc_update(repo_name, pr_number)
        
        return {"status": "processing", "event": event, "action": action}

    return {"status": "ignored", "event": event}
