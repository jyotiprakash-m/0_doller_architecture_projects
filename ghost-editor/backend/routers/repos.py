from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.repository import Repository
from schemas.repository import RepoCreate, RepoResponse
from typing import List

router = APIRouter()

@router.post("/", response_model=RepoResponse)
def create_repo(repo: RepoCreate, db: Session = Depends(get_db)):
    db_repo = Repository(**repo.dict())
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo

@router.get("/", response_model=List[RepoResponse])
def list_repos(db: Session = Depends(get_db)):
    return db.query(Repository).all()

@router.get("/{repo_id}", response_model=RepoResponse)
def get_repo(repo_id: int, db: Session = Depends(get_db)):
    db_repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not db_repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return db_repo
