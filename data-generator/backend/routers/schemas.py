"""
Schema Router — manage database schema projects.
Users can submit SQL DDL or structured JSON schemas.
"""
import json
import logging
from fastapi import APIRouter, HTTPException, Depends

from services import db
from services.auth_utils import get_current_user_id
from services.agentic_engine import agentic_generation_engine as generation_engine
# from services.generation_engine import generation_engine
from models.schemas import SchemaInput, SchemaProject, SchemaProjectListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/schemas", tags=["Schema Projects"])


@router.post("", response_model=SchemaProject)
async def create_schema(schema_input: SchemaInput, user_id: str = Depends(get_current_user_id)):
    """
    Create a new schema project.
    Accepts either raw SQL DDL or structured JSON table definitions.
    """
    tables = []

    if schema_input.sql_ddl:
        # Parse SQL DDL using LLM + fallback regex
        logger.info(f"Parsing SQL DDL for project '{schema_input.name}'...")
        tables = generation_engine.parse_ddl(schema_input.sql_ddl)
        if not tables:
            raise HTTPException(
                status_code=400,
                detail="Could not parse SQL DDL. Make sure your CREATE TABLE statements are valid."
            )
    elif schema_input.tables:
        # Use structured table definitions directly
        tables = [t.model_dump() for t in schema_input.tables]
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'sql_ddl' or 'tables' in the request."
        )

    schema_json = json.dumps(tables)
    project = db.create_schema_project(
        user_id=user_id,
        name=schema_input.name,
        description=schema_input.description or "",
        schema_json=schema_json,
        table_count=len(tables),
    )

    logger.info(f"Schema project '{schema_input.name}' created with {len(tables)} tables")
    return project


@router.get("", response_model=SchemaProjectListResponse)
async def list_schemas(user_id: str = Depends(get_current_user_id)):
    """Get all schema projects for the current user."""
    projects = db.get_all_schema_projects(user_id)
    return {"projects": projects, "total": len(projects)}


@router.get("/{project_id}", response_model=SchemaProject)
async def get_schema(project_id: str, user_id: str = Depends(get_current_user_id)):
    """Get a specific schema project by ID."""
    project = db.get_schema_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Schema project not found")
    if project["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return project


@router.delete("/{project_id}")
async def delete_schema(project_id: str, user_id: str = Depends(get_current_user_id)):
    """Delete a schema project."""
    project = db.get_schema_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Schema project not found")
    if project["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    db.delete_schema_project(project_id)
    logger.info(f"Schema project '{project_id}' deleted")
    return {"message": "Schema project deleted successfully"}
