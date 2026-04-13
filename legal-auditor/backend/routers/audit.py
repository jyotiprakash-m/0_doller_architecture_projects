"""
Audit API endpoints.
Run AI-powered audits on legal documents using the local LLM.
"""
import logging
from services import db
from services.document_processor import extract_text
from services.audit_engine import audit_engine
from services.auth_utils import get_current_user_id
from fastapi import APIRouter, HTTPException, Response, Depends

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/audit", tags=["Audit"])


@router.post("/{document_id}")
async def run_audit(
    document_id: str, 
    user_id: str = Depends(get_current_user_id)
):
    """
    Run a comprehensive AI audit on a document.
    All analysis happens locally via Ollama — zero data leaves the machine.
    """
    # Get user and check credits
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user["credits"] < 1:
        raise HTTPException(
            status_code=402, 
            detail="Insufficient credits. Please top up to run more audits."
        )

    # Get document
    doc = db.get_document(document_id)
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Extract text from the document
        extracted_text, _ = extract_text(doc["file_path"], doc["file_type"])

        # Create audit report record
        report = db.create_audit_report(user_id, document_id)

        # Deduct credit
        db.update_user_credits(user_id, -1.0)

        # Run AI audit (local LLM)
        logger.info(f"Running audit on '{doc['filename']}' using local LLM...")
        audit_result = audit_engine.analyze_document(extracted_text, doc["filename"])
        result = audit_result.to_dict()

        # Save results
        db.update_audit_report(
            report_id=report["id"],
            summary=result["executive_summary"],
            risk_score=result["overall_risk_score"],
            compliance_score=result["compliance_score"],
            findings=result["findings"],
            key_clauses=result["key_clauses"],
        )

        # Update document status
        db.update_document_status(document_id, "audited")

        return {
            "id": report["id"],
            "document_id": document_id,
            "document_name": doc["filename"],
            "status": "completed",
            "executive_summary": result["executive_summary"],
            "overall_risk_score": result["overall_risk_score"],
            "compliance_score": result["compliance_score"],
            "total_findings": len(result["findings"]),
            "high_risk_count": result["high_risk_count"],
            "medium_risk_count": result["medium_risk_count"],
            "low_risk_count": result["low_risk_count"],
            "findings": result["findings"],
            "key_clauses": result["key_clauses"],
            "message": "Audit completed successfully. All analysis performed locally."
        }

    except Exception as e:
        logger.error(f"Audit failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


@router.get("/{document_id}/report")
async def get_audit_report(document_id: str, user_id: str = Depends(get_current_user_id)):
    """Get the audit report for a document."""
    doc = db.get_document(document_id)
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    report = db.get_audit_report(document_id)
    if not report:
        raise HTTPException(status_code=404, detail="No audit report found. Run an audit first.")

    report["document_name"] = doc["filename"]
    report["total_findings"] = len(report.get("findings", []))
    report["high_risk_count"] = sum(1 for f in report.get("findings", []) if f.get("risk_level") == "high")
    report["medium_risk_count"] = sum(1 for f in report.get("findings", []) if f.get("risk_level") == "medium")
    report["low_risk_count"] = sum(1 for f in report.get("findings", []) if f.get("risk_level") == "low")

    return report


@router.get("")
async def list_audits(user_id: str = Depends(get_current_user_id)):
    """List all audit reports for the current user."""
    reports = db.get_all_audit_reports(user_id)
    return {
        "audits": reports,
        "total": len(reports)
    }


@router.get("/{document_id}/download")
async def download_audit_report(document_id: str, user_id: str = Depends(get_current_user_id)):
    """Generate and download the audit report as a PDF."""
    doc = db.get_document(document_id)
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get raw report from DB (with JSON strings)
    conn = db.get_connection()
    report = conn.execute("SELECT * FROM audit_reports WHERE document_id = ? AND user_id = ? ORDER BY created_at DESC", (document_id, user_id)).fetchone()
    conn.close()
    
    if not report:
        raise HTTPException(status_code=404, detail="No audit report found. Run an audit first.")

    # Convert to dict
    report_dict = dict(report)
    
    # Generate PDF
    try:
        pdf_bytes = generate_audit_pdf(doc["filename"], report_dict)
        
        filename = f"Audit_Report_{doc['filename'].split('.')[0]}.pdf"
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        logger.error(f"PDF Generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
