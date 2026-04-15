"""
Export Router — download generated synthetic data in various formats.
Supports CSV, SQL INSERT statements, and JSON.
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from services import db
from services.auth_utils import get_current_user_id
from services.duckdb_store import duckdb_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/export", tags=["Data Export"])


@router.get("/{job_id}/csv")
async def export_csv(job_id: str, table_name: str, user_id: str = Depends(get_current_user_id)):
    """Export generated data as CSV."""
    job = db.get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Generation not yet completed")

    try:
        csv_data = duckdb_store.export_csv(job_id, table_name)
        return PlainTextResponse(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{table_name}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


@router.get("/{job_id}/sql")
async def export_sql(job_id: str, table_name: str, user_id: str = Depends(get_current_user_id)):
    """Export generated data as SQL INSERT statements."""
    job = db.get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Generation not yet completed")

    try:
        sql_data = duckdb_store.export_sql(job_id, table_name)
        return PlainTextResponse(
            content=sql_data,
            media_type="application/sql",
            headers={"Content-Disposition": f'attachment; filename="{table_name}.sql"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")


@router.get("/{job_id}/json")
async def export_json(job_id: str, table_name: str, user_id: str = Depends(get_current_user_id)):
    """Export generated data as JSON."""
    job = db.get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Generation not yet completed")

    try:
        json_data = duckdb_store.export_json(job_id, table_name)
        return PlainTextResponse(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{table_name}.json"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e}")
