from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class RepoBase(BaseModel):
    name: str
    full_name: str
    url: str

class RepoCreate(RepoBase):
    pass

class RepoResponse(RepoBase):
    id: int
    is_active: bool
    last_synced_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
