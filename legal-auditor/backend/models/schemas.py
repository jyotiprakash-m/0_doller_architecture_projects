"""
Pydantic models for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    AUDITED = "audited"
    ERROR = "error"


# --- Document Schemas ---

class DocumentUploadResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    uploaded_at: str
    page_count: Optional[int] = None
    message: str


class DocumentInfo(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    uploaded_at: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = 0


class DocumentListResponse(BaseModel):
    documents: list[DocumentInfo]
    total: int


# --- Audit Schemas ---

class AuditFinding(BaseModel):
    id: str
    category: str
    title: str
    description: str
    risk_level: RiskLevel
    clause_text: Optional[str] = None
    recommendation: str
    page_reference: Optional[str] = None


class AuditReport(BaseModel):
    id: str
    document_id: str
    document_name: str
    status: str
    created_at: str
    executive_summary: Optional[str] = None
    overall_risk_score: Optional[str] = None
    total_findings: int = 0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0
    findings: list[AuditFinding] = []
    compliance_score: Optional[float] = None
    key_clauses: list[dict] = []


class AuditRequest(BaseModel):
    audit_type: str = Field(default="comprehensive", description="Type: comprehensive, compliance, risk, clause_extraction")


# --- Chat Schemas ---

class ChatMessage(BaseModel):
    role: str
    content: str
    sources: Optional[list[dict]] = None
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    query: str
    document_ids: Optional[list[str]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict] = []
    confidence: Optional[float] = None


# --- Dashboard Schemas ---

class DashboardStats(BaseModel):
    total_documents: int = 0
    total_audits: int = 0
    high_risk_findings: int = 0
    avg_compliance_score: float = 0.0
    recent_documents: list[DocumentInfo] = []
    recent_audits: list[dict] = []
