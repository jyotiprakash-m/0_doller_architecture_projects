"""
Pydantic models for request/response validation.
Synthetic Data Generator for Developers.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


# --- Enums ---

class JobStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportFormat(str, Enum):
    CSV = "csv"
    SQL = "sql"
    JSON = "json"


class ColumnType(str, Enum):
    """Supported column data types."""
    INTEGER = "integer"
    BIGINT = "bigint"
    FLOAT = "float"
    DOUBLE = "double"
    VARCHAR = "varchar"
    TEXT = "text"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    UUID = "uuid"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    JSON_TYPE = "json"


# --- Schema Definition Models ---

class ColumnDefinition(BaseModel):
    name: str = Field(..., description="Column name")
    data_type: str = Field(..., description="Data type (e.g., integer, varchar, text, date)")
    nullable: bool = Field(default=True, description="Whether the column can be NULL")
    primary_key: bool = Field(default=False, description="Is this a primary key?")
    unique: bool = Field(default=False, description="Should values be unique?")
    foreign_key: Optional[str] = Field(default=None, description="FK reference: 'table.column'")
    default_value: Optional[str] = Field(default=None, description="Default value")


class TableDefinition(BaseModel):
    name: str = Field(..., description="Table name")
    columns: list[ColumnDefinition] = Field(..., description="Column definitions")


class SchemaInput(BaseModel):
    """User input — either raw SQL DDL or structured JSON schema."""
    name: str = Field(..., description="Project name for this schema")
    description: Optional[str] = Field(default=None, description="Optional description")
    sql_ddl: Optional[str] = Field(default=None, description="Raw SQL DDL (CREATE TABLE statements)")
    tables: Optional[list[TableDefinition]] = Field(default=None, description="Structured table definitions")


class SchemaProject(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    schema_json: str  # JSON-serialized table definitions
    table_count: int = 0
    created_at: str
    updated_at: str


class SchemaProjectListResponse(BaseModel):
    projects: list[SchemaProject]
    total: int


# --- Generation Models ---

class GenerationRequest(BaseModel):
    row_count: int = Field(default=1000, ge=1, le=1000000, description="Number of rows per table")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")
    locale: str = Field(default="en_US", description="Locale for generated data (e.g., en_US, de_DE)")


class GenerationJob(BaseModel):
    id: str
    schema_project_id: str
    user_id: str
    status: JobStatus
    row_count: int
    rows_generated: int = 0
    table_count: int = 0
    tables_completed: int = 0
    current_table: Optional[str] = None
    error_message: Optional[str] = None
    generation_plan_json: Optional[str] = None
    duckdb_path: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None


class GenerationJobListResponse(BaseModel):
    jobs: list[GenerationJob]
    total: int


# --- Data Preview Models ---

class DataPreviewRequest(BaseModel):
    table_name: str
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)


class DataPreview(BaseModel):
    table_name: str
    columns: list[str]
    rows: list[list]  # List of row values
    total_rows: int
    page: int
    page_size: int
    total_pages: int


# --- Export Models ---

class ExportRequest(BaseModel):
    format: ExportFormat = ExportFormat.CSV
    tables: Optional[list[str]] = Field(default=None, description="Specific tables to export (None = all)")


# --- Dashboard Models ---

class DashboardStats(BaseModel):
    total_projects: int = 0
    total_jobs: int = 0
    total_rows_generated: int = 0
    completed_jobs: int = 0
    recent_projects: list[SchemaProject] = []
    recent_jobs: list[GenerationJob] = []
    user_credits: int = 0
