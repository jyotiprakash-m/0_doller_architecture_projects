from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from services import db
from models import schemas
from typing import List

router = APIRouter(prefix="/api/profiles", tags=["Profiles"])

@router.post("/", response_model=schemas.BusinessProfileResponse)
def create_profile(profile: schemas.BusinessProfileCreate, session: Session = Depends(db.get_db)):
    db_profile = db.BusinessProfile(**profile.model_dump())
    session.add(db_profile)
    session.commit()
    session.refresh(db_profile)
    return db_profile

@router.get("/", response_model=List[schemas.BusinessProfileResponse])
def get_profiles(skip: int = 0, limit: int = 10, session: Session = Depends(db.get_db)):
    return session.query(db.BusinessProfile).offset(skip).limit(limit).all()

@router.get("/history", response_model=List[schemas.BusinessProfileWithLatestAudit])
def get_audit_history(session: Session = Depends(db.get_db)):
    # Subquery to get the latest audit for each business
    latest_audits = session.query(
        db.SEOAuditReport.business_id,
        func.max(db.SEOAuditReport.created_at).label("max_date")
    ).group_by(db.SEOAuditReport.business_id).subquery()

    results = session.query(
        db.BusinessProfile.id,
        db.BusinessProfile.name,
        db.BusinessProfile.industry,
        db.BusinessProfile.location,
        db.BusinessProfile.website,
        db.SEOAuditReport.overall_score.label("latest_audit_score"),
        db.SEOAuditReport.created_at.label("latest_audit_date")
    ).join(
        latest_audits, db.BusinessProfile.id == latest_audits.c.business_id
    ).join(
        db.SEOAuditReport, 
        (db.SEOAuditReport.business_id == latest_audits.c.business_id) & 
        (db.SEOAuditReport.created_at == latest_audits.c.max_date)
    ).order_by(db.SEOAuditReport.created_at.desc()).all()

    return results
