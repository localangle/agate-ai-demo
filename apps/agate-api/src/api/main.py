"""FastAPI application."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from agate_db import init_db, get_session
from api.routers import graphs, runs, projects, flows
from sqlmodel import text


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    init_db()
    yield


app = FastAPI(
    title="Agate API (demo)",
    description="Control plane for composable flows",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

UI_ORIGIN = os.getenv("UI_ORIGIN", "http://localhost:5173")

if UI_ORIGIN.startswith("http://localhost") or UI_ORIGIN.startswith("http://127.0.0.1"):
    ALLOWED_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
else:
    ALLOWED_ORIGINS = [UI_ORIGIN]

print(f"[CORS] Allowed origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(projects.router)
app.include_router(graphs.router)
app.include_router(runs.router)
app.include_router(flows.router)


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/health/detailed")
def health_detailed():
    try:
        session = get_session()
        try:
            session.exec(text("SELECT 1"))
            return {"ok": True, "database": "connected"}
        finally:
            session.close()
    except Exception as e:
        print(f"[HEALTH] Database check failed: {str(e)}")
        return {"ok": False, "database": "disconnected"}, 503


@app.get("/")
def root():
    return {
        "name": "Agate API (demo)",
        "version": "0.1.0",
    }
