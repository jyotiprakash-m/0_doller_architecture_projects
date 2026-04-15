import logging
import re
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from services import db, seo_engine
from models import schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/audits", tags=["Audits"])

def extract_score(text: str, label: str = "Overall Score") -> int:
    """Helper to extract a score from agent text using regex."""
    match = re.search(f"{label}:\\s*(\\d+)", text, re.IGNORECASE)
    if match:
        try:
            return min(100, max(0, int(match.group(1))))
        except ValueError:
            return 50
    return 50

def run_seo_audit_background(business_id: int, session: Session):
    try:
        profile = session.query(db.BusinessProfile).filter(db.BusinessProfile.id == business_id).first()
        if not profile:
            logger.error(f"Profile not found for ID {business_id}")
            return
            
        crew = seo_engine.create_seo_audit_crew(
            business_name=profile.name,
            industry=profile.industry,
            location=profile.location
        )
        
        result = crew.kickoff()
        
        # Handle string result for older CrewAI versions (like v0.11.2)
        final_output = str(result)
        
        # Use the raw string for parsing. We expect the agents to output the scores 
        # in the text as per our instructions in seo_engine.py.
        overall = extract_score(final_output, "Overall Score")
        google_presence = extract_score(final_output, "Google Presence Score")
        content_score = extract_score(final_output, "Content Score")
        social_score = extract_score(final_output, "Social Score")
        
        # Store the report
        audit_report = db.SEOAuditReport(
            business_id=business_id,
            overall_score=overall,
            google_presence_score=google_presence,
            content_score=content_score,
            social_score=social_score,
            competitor_analysis=final_output, 
            social_analysis="Detailed Social/Reputation analysis included in raw report.",
            actionable_steps=final_output,
            raw_data=final_output
        )
        session.add(audit_report)
        session.commit()
        
    except Exception as e:
        logger.error(f"Error during SEO audit: {e}")

@router.post("/run/{business_id}")
def trigger_audit(business_id: int, background_tasks: BackgroundTasks, session: Session = Depends(db.get_db)):
    profile = session.query(db.BusinessProfile).filter(db.BusinessProfile.id == business_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Business Profile not found")
        
    background_tasks.add_task(run_seo_audit_background, business_id, session)
    return {"message": "SEO Audit started in the background."}

@router.get("/{business_id}", response_model=list[schemas.SEOAuditReportResponse])
def get_audits(business_id: int, session: Session = Depends(db.get_db)):
    audits = session.query(db.SEOAuditReport)\
        .filter(db.SEOAuditReport.business_id == business_id)\
        .order_by(db.SEOAuditReport.created_at.desc())\
        .all()
    return audits
