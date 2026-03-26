"""Database models for Agate AI Platform."""

from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class Project(SQLModel, table=True):
    """Project definition."""
    __tablename__ = "projects"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    system_prompt: Optional[str] = Field(default=None, description="Optional system prompt for all LLM calls in this project")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Graph(SQLModel, table=True):
    """Graph definition."""
    __tablename__ = "graphs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    spec_json: str  # JSON string of GraphSpec
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Run(SQLModel, table=True):
    """Run execution record - represents a user-initiated flow execution."""
    __tablename__ = "runs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    graph_id: int = Field(foreign_key="graphs.id", index=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    status: str = Field(default="pending", index=True)  # pending, running, completed, completed_with_errors
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProcessedItem(SQLModel, table=True):
    """Processed item - represents one piece of data flowing through a run."""
    __tablename__ = "processed_items"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: int = Field(foreign_key="runs.id", index=True)
    source_file: Optional[str] = None  # S3 key if from S3Input, null for TextInput/JSONInput
    input_json: str  # JSON string of input data
    output_json: Optional[str] = None  # JSON string of output
    node_outputs_json: Optional[str] = None  # JSON string of individual node outputs
    node_logs_json: Optional[str] = None  # JSON string of individual node logs
    status: str = Field(default="pending", index=True)  # pending, running, succeeded, failed
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectApiKey(SQLModel, table=True):
    """Project API keys (encrypted)."""
    __tablename__ = "project_api_keys"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", index=True)
    key_name: str = Field(index=True)  # e.g., "OPENAI_API_KEY"
    encrypted_value: str  # Encrypted API key
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Unique constraint on (project_id, key_name)
    __table_args__ = (
        {"extend_existing": True},
    )
