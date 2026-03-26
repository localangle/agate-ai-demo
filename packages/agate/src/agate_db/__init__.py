"""Shared database models and connection for Agate AI Platform."""

from .constants import DEFAULT_PROJECT_NAME
from .models import Project, Graph, Run, ProcessedItem, ProjectApiKey
from .connection import engine, get_session, get_session_generator, init_db
from .api_keys import (
    get_project_api_key,
    set_project_api_key,
    delete_project_api_key,
    list_project_api_keys,
    get_all_project_api_keys
)

__all__ = [
    "DEFAULT_PROJECT_NAME",
    "Project", "Graph", "Run", "ProcessedItem", "ProjectApiKey",
    "engine", "get_session", "get_session_generator", "init_db",
    "get_project_api_key", "set_project_api_key", "delete_project_api_key",
    "list_project_api_keys", "get_all_project_api_keys",
]
