"""Project API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from agate_db import (
    DEFAULT_PROJECT_NAME,
    LEGACY_DEFAULT_PROJECT_NAME,
    Project,
    Graph,
    Run,
    ProcessedItem,
    get_session_generator,
    ProjectApiKey,
    list_project_api_keys,
    set_project_api_key,
    delete_project_api_key,
)

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    """Project creation request."""
    name: str


class ProjectUpdate(BaseModel):
    """Project update request."""
    name: Optional[str] = None
    system_prompt: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project response."""
    id: int
    name: str
    system_prompt: Optional[str] = None
    created_at: str


class ApiKeyResponse(BaseModel):
    """API key response (metadata only, not the actual key value)."""
    key_name: str
    created_at: str
    updated_at: str


class ApiKeyCreate(BaseModel):
    """API key creation request."""
    key_name: str
    value: str


@router.post("/", response_model=ProjectResponse)
def create_project(
    project: ProjectCreate,
    session: Session = Depends(get_session_generator),
):
    """Create a new project."""
    existing = session.exec(select(Project).where(Project.name == project.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project with this name already exists")

    db_project = Project(name=project.name)
    session.add(db_project)
    session.commit()
    session.refresh(db_project)

    return ProjectResponse(
        id=db_project.id,
        name=db_project.name,
        system_prompt=db_project.system_prompt,
        created_at=db_project.created_at.isoformat()
    )


@router.get("/", response_model=List[ProjectResponse])
def list_projects(
    session: Session = Depends(get_session_generator),
):
    """List all projects (demo: no access control)."""
    projects = session.exec(select(Project).order_by(Project.created_at)).all()
    return [
        ProjectResponse(
            id=project.id,
            name=project.name,
            system_prompt=project.system_prompt,
            created_at=project.created_at.isoformat()
        )
        for project in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    session: Session = Depends(get_session_generator),
):
    """Get a specific project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(
        id=project.id,
        name=project.name,
        system_prompt=project.system_prompt,
        created_at=project.created_at.isoformat()
    )


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    session: Session = Depends(get_session_generator),
):
    """Update a project."""
    db_project = session.get(Project, project_id)
    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.name is not None:
        existing = session.exec(
            select(Project).where(
                Project.name == project.name,
                Project.id != project_id
            )
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Project with this name already exists")
        db_project.name = project.name

    if project.system_prompt is not None:
        db_project.system_prompt = project.system_prompt

    session.add(db_project)
    session.commit()
    session.refresh(db_project)

    return ProjectResponse(
        id=db_project.id,
        name=db_project.name,
        system_prompt=db_project.system_prompt,
        created_at=db_project.created_at.isoformat()
    )


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    session: Session = Depends(get_session_generator),
):
    """Delete a project and all associated graphs, runs, and processed items."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.name in (DEFAULT_PROJECT_NAME, LEGACY_DEFAULT_PROJECT_NAME):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete the default '{DEFAULT_PROJECT_NAME}' project",
        )

    graphs = session.exec(select(Graph).where(Graph.project_id == project_id)).all()

    for graph in graphs:
        runs = session.exec(select(Run).where(Run.graph_id == graph.id)).all()

        for run in runs:
            processed_items = session.exec(
                select(ProcessedItem).where(ProcessedItem.run_id == run.id)
            ).all()
            for item in processed_items:
                session.delete(item)

            session.delete(run)

    session.flush()

    for graph in graphs:
        session.delete(graph)

    session.flush()

    api_keys = session.exec(
        select(ProjectApiKey).where(ProjectApiKey.project_id == project_id)
    ).all()
    for api_key in api_keys:
        session.delete(api_key)

    session.flush()

    session.delete(project)
    session.commit()

    return {"message": f"Project '{project.name}' and all associated data deleted successfully"}


@router.get("/{project_id}/api-keys", response_model=List[ApiKeyResponse])
def list_project_api_keys_endpoint(
    project_id: int,
    session: Session = Depends(get_session_generator),
):
    """List all API keys for a project (metadata only)."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    api_keys = list_project_api_keys(session, project_id)
    return [
        ApiKeyResponse(
            key_name=api_key.key_name,
            created_at=api_key.created_at.isoformat(),
            updated_at=api_key.updated_at.isoformat()
        )
        for api_key in api_keys
    ]


@router.post("/{project_id}/api-keys", response_model=ApiKeyResponse)
def set_project_api_key_endpoint(
    project_id: int,
    api_key_data: ApiKeyCreate,
    session: Session = Depends(get_session_generator),
):
    """Set an API key for a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    valid_key_names = {
        "OPENAI_API_KEY",
    }
    if api_key_data.key_name not in valid_key_names:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid key name. Must be one of: {', '.join(sorted(valid_key_names))}"
        )

    try:
        api_key = set_project_api_key(session, project_id, api_key_data.key_name, api_key_data.value)
        return ApiKeyResponse(
            key_name=api_key.key_name,
            created_at=api_key.created_at.isoformat(),
            updated_at=api_key.updated_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/api-keys/{key_name}")
def delete_project_api_key_endpoint(
    project_id: int,
    key_name: str,
    session: Session = Depends(get_session_generator),
):
    """Delete an API key for a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    success = delete_project_api_key(session, project_id, key_name)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")

    return {"message": "API key deleted successfully"}
