from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from services import db, pdf_generator
import os

router = APIRouter(prefix="/api/reports", tags=["Reports"])

@router.get("/{audit_id}/pdf")
def get_pdf_report(audit_id: int, session: Session = Depends(db.get_db)):
    report = session.query(db.SEOAuditReport).filter(db.SEOAuditReport.id == audit_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Audit report not found")
        
    profile = session.query(db.BusinessProfile).filter(db.BusinessProfile.id == report.business_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")
    
    try:
        pdf_path = pdf_generator.generate_seo_pdf(profile.name, profile.location, report)
        return FileResponse(
            path=pdf_path, 
            filename=f"{profile.name.replace(' ', '_')}_SEO_Audit.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
