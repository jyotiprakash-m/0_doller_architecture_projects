"""
Generate Router — trigger and monitor synthetic data generation jobs.
"""
import json
import logging
import threading
from fastapi import APIRouter, HTTPException, Depends

from services import db
from services.auth_utils import get_current_user_id
from services.agentic_engine import agentic_generation_engine as generation_engine
# from services.generation_engine import generation_engine
from services.duckdb_store import duckdb_store
from models.schemas import GenerationRequest, GenerationJob, GenerationJobListResponse, DataPreview

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/generate", tags=["Data Generation"])


def _run_generation(job_id: str, tables: list[dict], plan, seed: int, locale: str):
    """Background thread function for data generation."""
    try:
        generation_engine.generate_data(
            job_id=job_id,
            plan=plan,
            tables=tables,
            seed=seed,
            locale=locale,
        )
    except Exception as e:
        logger.error(f"Generation failed for job {job_id}: {e}")
        db.update_job_status(job_id, "failed", error_message=str(e))


@router.post("/{schema_id}", response_model=GenerationJob)
async def trigger_generation(
    schema_id: str,
    request: GenerationRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Trigger synthetic data generation for a schema project.
    Creates a generation job and starts processing in background.
    """
    # Validate schema exists
    project = db.get_schema_project(schema_id)
    if not project:
        raise HTTPException(status_code=404, detail="Schema project not found")
    if project["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check user credits
    user = db.get_user_by_id(user_id)
    if not user or user["credits"] <= 0:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    # Parse schema
    tables = json.loads(project["schema_json"])
    if not tables:
        raise HTTPException(status_code=400, detail="Schema has no tables defined")

    # Create job
    job = db.create_generation_job(
        user_id=user_id,
        schema_project_id=schema_id,
        row_count=request.row_count,
        seed=request.seed,
        locale=request.locale,
    )

    # Deduct credits
    db.update_user_credits(user_id, -1)

    # Update status to analyzing
    db.update_job_status(job["id"], "analyzing")

    # Create generation plan
    try:
        plan = generation_engine.create_generation_plan(tables, request.row_count)
        plan_json = json.dumps({
            "generation_order": plan.generation_order,
            "total_rows": plan.total_rows,
            "tables": [
                {
                    "name": tp.name,
                    "row_count": tp.row_count,
                    "depends_on": tp.depends_on,
                    "columns": [
                        {
                            "name": cp.name,
                            "faker_method": cp.faker_method,
                            "is_pk": cp.is_primary_key,
                            "is_fk": cp.is_foreign_key,
                        }
                        for cp in tp.columns
                    ],
                }
                for tp in plan.tables
            ],
        })
        db.update_job_status(job["id"], "analyzing", generation_plan_json=plan_json)
    except Exception as e:
        db.update_job_status(job["id"], "failed", error_message=f"Plan creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create generation plan: {e}")

    # Start generation in background thread
    thread = threading.Thread(
        target=_run_generation,
        args=(job["id"], tables, plan, request.seed, request.locale),
        daemon=True,
    )
    thread.start()

    # Return the updated job
    updated_job = db.get_generation_job(job["id"])
    return updated_job


@router.get("/{job_id}/status", response_model=GenerationJob)
async def get_job_status(job_id: str, user_id: str = Depends(get_current_user_id)):
    """Get the current status of a generation job."""
    job = db.get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return job


@router.get("/{job_id}/preview", response_model=DataPreview)
async def preview_data(
    job_id: str,
    table_name: str,
    page: int = 1,
    page_size: int = 50,
    user_id: str = Depends(get_current_user_id),
):
    """Preview generated synthetic data for a specific table."""
    job = db.get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Generation not yet completed")

    preview = duckdb_store.preview_data(job_id, table_name, page, page_size)
    return preview


@router.get("/{job_id}/tables")
async def get_job_tables(job_id: str, user_id: str = Depends(get_current_user_id)):
    """Get list of tables generated in a job."""
    job = db.get_generation_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Generation job not found")
    if job["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    tables = duckdb_store.get_table_names(job_id)
    table_info = []
    for t in tables:
        row_count = duckdb_store.get_row_count(job_id, t)
        columns = duckdb_store.get_table_columns(job_id, t)
        table_info.append({
            "name": t,
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns,
        })

    return {"tables": table_info, "total": len(table_info)}


@router.get("/jobs/all", response_model=GenerationJobListResponse)
async def list_all_jobs(user_id: str = Depends(get_current_user_id)):
    """Get all generation jobs for the current user."""
    jobs = db.get_all_generation_jobs(user_id)
    return {"jobs": jobs, "total": len(jobs)}
