from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BusinessProfileBase(BaseModel):
    name: str
    industry: str
    location: str
    website: Optional[str] = None


class BusinessProfileCreate(BusinessProfileBase):
    pass


class BusinessProfileResponse(BusinessProfileBase):
    id: int

    class Config:
        from_attributes = True


class BusinessProfileWithLatestAudit(BusinessProfileBase):
    id: int
    latest_audit_score: Optional[int] = None
    latest_audit_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class SEOAuditReportResponse(BaseModel):
    id: int
    business_id: int
    created_at: datetime
    overall_score: int
    google_presence_score: int
    content_score: int
    social_score: int
    competitor_analysis: str
    social_analysis: str
    actionable_steps: str
    raw_data: str

    class Config:
        from_attributes = True
