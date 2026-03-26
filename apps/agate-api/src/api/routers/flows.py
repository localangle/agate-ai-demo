from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from agate_db import Graph, get_session_generator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flows", tags=["flows"])


class FlowTriggerRequest(BaseModel):
    """Payload sent by crawlers when a flow should be triggered."""

    run_id: Optional[str] = Field(default=None, description="Optional crawler run identifier")
    timestamp: datetime = Field(..., description="Time the crawl completed")
    object_key: Optional[str] = Field(
        default=None,
        description="S3 key prefix (within the configured bucket) containing crawler output",
    )
    output_bucket: Optional[str] = Field(
        default=None,
        description="Optional override for the S3 bucket containing crawler output",
    )


def _resolve_graph(session: Session, flow_id: str) -> Graph:
    """Resolve a graph definition from the provided flow identifier."""
    graph: Optional[Graph] = None

    if flow_id.isdigit():
        graph = session.get(Graph, int(flow_id))

    if not graph:
        statement = select(Graph).where(Graph.name == flow_id)
        graph = session.exec(statement).first()

    if not graph:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")

    return graph


@router.post("/{flow_id}/trigger", status_code=status.HTTP_202_ACCEPTED)
def trigger_flow_run(
    flow_id: str,
    payload: FlowTriggerRequest,
    session: Session = Depends(get_session_generator),
) -> dict[str, object]:
    """Kick off a flow run after a crawler finishes uploading data."""
    logger.info("Received flow trigger request for flow_id=%s, payload=%s", flow_id, payload.model_dump())
    _resolve_graph(session, flow_id)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Crawler/object_key flow trigger is not available in this demo (APIInput and S3Input nodes were removed).",
    )

