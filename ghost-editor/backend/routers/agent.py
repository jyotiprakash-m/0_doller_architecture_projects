from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.job import Job
from typing import List

router = APIRouter()

@router.get("/jobs", response_model=List[dict])
def list_jobs(db: Session = Depends(get_db)):
    # Simple list of jobs
    jobs = db.query(Job).order_by(Job.created_at.desc()).limit(10).all()
    return [{"id": j.id, "status": j.status, "repo_id": j.repo_id, "created_at": j.created_at} for j in jobs]

@router.post("/trigger/{repo_id}")
def trigger_agent(repo_id: int, db: Session = Depends(get_db)):
    # In a real app, this would queue a background task
    # For now, we just acknowledge the request
    return {"status": "triggered", "repo_id": repo_id, "msg": "Ghost-Editor agent started in background."}

@router.get("/status/{job_id}")
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"id": job.id, "status": job.status, "log": job.log}
