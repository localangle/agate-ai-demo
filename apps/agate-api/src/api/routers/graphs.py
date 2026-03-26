"""Graph management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from pydantic import BaseModel

from agate_db import Graph, Project, get_session_generator as get_session
from agate_core import GraphSpec

router = APIRouter(prefix="/graphs", tags=["graphs"])


class GraphCreate(BaseModel):
    """Request to create a graph."""
    name: str
    project_id: int
    spec: GraphSpec


class GraphResponse(BaseModel):
    """Graph response."""
    id: int
    name: str
    project_id: int
    spec: GraphSpec
    created_at: str


@router.post("", response_model=GraphResponse)
def create_graph(
    graph_create: GraphCreate,
    session: Session = Depends(get_session),
):
    """Create a new graph."""
    project = session.get(Project, graph_create.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    spec_json = graph_create.spec.model_dump_json()

    graph = Graph(
        name=graph_create.name,
        project_id=graph_create.project_id,
        spec_json=spec_json
    )
    session.add(graph)
    session.commit()
    session.refresh(graph)

    return GraphResponse(
        id=graph.id,
        name=graph.name,
        project_id=graph.project_id,
        spec=GraphSpec.model_validate_json(graph.spec_json),
        created_at=graph.created_at.isoformat()
    )


@router.get("", response_model=List[GraphResponse])
def list_graphs(
    session: Session = Depends(get_session),
):
    """List all graphs (demo: no access control)."""
    graphs = session.exec(select(Graph).order_by(Graph.created_at.desc())).all()
    return [
        GraphResponse(
            id=graph.id,
            name=graph.name,
            project_id=graph.project_id,
            spec=GraphSpec.model_validate_json(graph.spec_json),
            created_at=graph.created_at.isoformat()
        )
        for graph in graphs
    ]


@router.get("/{graph_id}", response_model=GraphResponse)
def get_graph(
    graph_id: int,
    session: Session = Depends(get_session),
):
    """Get a specific graph."""
    graph = session.get(Graph, graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    return GraphResponse(
        id=graph.id,
        name=graph.name,
        project_id=graph.project_id,
        spec=GraphSpec.model_validate_json(graph.spec_json),
        created_at=graph.created_at.isoformat()
    )


@router.put("/{graph_id}", response_model=GraphResponse)
def update_graph(
    graph_id: int,
    graph_create: GraphCreate,
    session: Session = Depends(get_session),
):
    """Update an existing graph."""
    graph = session.get(Graph, graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    project = session.get(Project, graph_create.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    graph.name = graph_create.name
    graph.project_id = graph_create.project_id
    graph.spec_json = graph_create.spec.model_dump_json()

    session.add(graph)
    session.commit()
    session.refresh(graph)

    return GraphResponse(
        id=graph.id,
        name=graph.name,
        project_id=graph.project_id,
        spec=GraphSpec.model_validate_json(graph.spec_json),
        created_at=graph.created_at.isoformat()
    )


@router.delete("/{graph_id}")
def delete_graph(
    graph_id: int,
    session: Session = Depends(get_session),
):
    """Delete a graph and all associated runs and processed items."""
    graph = session.get(Graph, graph_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Graph not found")

    from agate_db import Run, ProcessedItem

    runs = session.exec(select(Run).where(Run.graph_id == graph_id)).all()
    run_ids = [run.id for run in runs]

    if run_ids:
        processed_items = session.exec(
            select(ProcessedItem).where(ProcessedItem.run_id.in_(run_ids))
        ).all()
        for item in processed_items:
            session.delete(item)

    for run in runs:
        session.delete(run)

    session.commit()

    session.delete(graph)
    session.commit()

    return {"message": f"Graph and {len(runs)} associated runs deleted successfully"}
