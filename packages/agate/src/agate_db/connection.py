"""Database connection and session management."""

import os
import json
from pathlib import Path
from sqlmodel import create_engine, Session, select

from .constants import DEFAULT_PROJECT_NAME
from .models import Project, Graph, Run

GRAPH_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "graphs"


# Database engine
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5433/demo")
# Configure connection pool to prevent exhaustion
# pool_size: number of connections to maintain persistently
# max_overflow: additional connections that can be created on demand
# pool_timeout: seconds to wait before giving up on getting a connection
# pool_recycle: seconds before recreating a connection (prevents stale connections)
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,  # Maintain 5 persistent connections
    max_overflow=10,  # Allow up to 10 additional connections when needed
    pool_timeout=30,  # Wait up to 30 seconds for a connection
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using them
)


def fix_sequences():
    """Fix PostgreSQL sequences to be sequential after the highest existing IDs."""
    from sqlmodel import text
    
    with Session(engine) as session:
        # Fix projects sequence
        result = session.exec(select(Project.id).order_by(Project.id.desc()).limit(1)).first()
        if result:
            session.exec(text(f"SELECT setval('projects_id_seq', {result})"))
        
        # Fix graphs sequence
        result = session.exec(select(Graph.id).order_by(Graph.id.desc()).limit(1)).first()
        if result:
            session.exec(text(f"SELECT setval('graphs_id_seq', {result})"))
        
        # Fix runs sequence
        result = session.exec(select(Run.id).order_by(Run.id.desc()).limit(1)).first()
        if result:
            session.exec(text(f"SELECT setval('runs_id_seq', {result})"))
        
        print("Fixed database sequences to be sequential")


def load_graph_fixtures() -> list[dict]:
    """Load graph fixture payloads from JSON files."""
    fixtures: list[dict] = []
    if not GRAPH_FIXTURES_DIR.exists():
        return fixtures

    for fixture_path in sorted(GRAPH_FIXTURES_DIR.glob("*.json")):
        with fixture_path.open("r", encoding="utf-8") as handle:
            fixture = json.load(handle)
        fixtures.append(fixture)

    return fixtures


def ensure_graph_fixtures(session: Session, project_id: int):
    """Create graph fixtures when missing."""
    fixtures = load_graph_fixtures()
    if not fixtures:
        return

    for fixture in fixtures:
        name = fixture.get("name")
        spec = fixture.get("spec")
        if not name or not spec:
            print(f"[agate_db] Skipping invalid graph fixture: {fixture}")
            continue

        existing = session.exec(
            select(Graph).where(
                Graph.project_id == project_id,
                Graph.name == name,
            )
        ).first()
        if existing:
            continue

        graph = Graph(
            name=name,
            project_id=project_id,
            spec_json=json.dumps(spec),
        )
        session.add(graph)
        session.commit()
        print(f"Created graph fixture '{name}'")


def init_db():
    """Initialize database tables and create default project."""
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)

    # Create default project if missing.
    with Session(engine) as session:
        demo = session.exec(
            select(Project).where(Project.name == DEFAULT_PROJECT_NAME)
        ).first()
        if not demo:
            session.add(Project(name=DEFAULT_PROJECT_NAME))
            session.commit()
            print(f"Created default '{DEFAULT_PROJECT_NAME}' project")

        # Seed default graph fixtures after project and tables exist.
        demo = session.exec(
            select(Project).where(Project.name == DEFAULT_PROJECT_NAME)
        ).first()
        if demo:
            ensure_graph_fixtures(session, demo.id)

    # Fix sequences to be sequential
    fix_sequences()


def get_session():
    """Get a database session."""
    return Session(engine)


def get_session_generator():
    """Get a database session as a generator (for FastAPI dependency injection)."""
    with Session(engine) as session:
        yield session
