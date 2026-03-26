# tools/search.py

import logging
from typing import Any, List, Mapping, Optional, Sequence
from pydantic import BaseModel, Field
from ddgs import DDGS

logger = logging.getLogger(__name__)

########## MODELS ##########

class SearchResult(BaseModel):
    """A single search result."""
    title: str = Field(description="Title of the search result")
    snippet: str = Field(description="Text snippet from the result")
    url: str = Field(description="URL of the result")
    relevance_score: float = Field(default=1.0, description="Relevance score (0-1)")


class SearchResponse(BaseModel):
    """Response from a search operation."""
    success: bool = Field(description="Whether the search was successful")
    results: List[SearchResult] = Field(default_factory=list, description="List of search results")
    query: str = Field(description="The original search query")
    error: Optional[str] = Field(default=None, description="Error message if search failed")


def _row_to_search_result(row: Mapping[str, Any], rank: int) -> SearchResult:
    """Map a normalized search-provider row to SearchResult."""
    title = str(row.get("title") or row.get("Title") or f"Result {rank + 1}")
    snippet = str(
        row.get("description")
        or row.get("snippet")
        or row.get("body")
        or row.get("Snippet")
        or ""
    )
    url = str(row.get("url") or row.get("href") or row.get("URL") or "")
    return SearchResult(
        title=title,
        snippet=snippet[:2000] if snippet else "",
        url=url,
        relevance_score=max(0.1, 1.0 - rank * 0.08),
    )


def search_response_from_rows(query: str, rows: Sequence[Mapping[str, Any]]) -> SearchResponse:
    """Build SearchResponse from normalized rows (Agate-friendly; JSON-serializable)."""
    results = [_row_to_search_result(r, i) for i, r in enumerate(rows)]
    return SearchResponse(success=True, results=results, query=query)


########## DUCKDUCKGO (no API key; Agate-ready SearchResponse) ##########


def search_web_duckduckgo(
    query: str,
    max_results: int = 10,
    timeout: Optional[float] = 15.0,
) -> SearchResponse:
    """
    Web search via DuckDuckGo (no API key). Returns SearchResponse for agents and Agate nodes.

    Uses only public DDGS APIs (no private methods) for compatibility across
    package versions.

    Args:
        query: Search string.
        max_results: Max hits (capped for stability).
        timeout: HTTP timeout seconds; None uses library default (10).

    Returns:
        SearchResponse: success=False + error on total failure; success=True with zero
        results if every backend returned empty.
    """
    q = (query or "").strip()
    if not q:
        return SearchResponse(success=False, error="Empty query", results=[], query=query)

    # Keep query bounded for transport and logging
    q_search = q if len(q) <= 400 else q[:397] + "..."
    max_results = max(1, min(max_results, 25))
    to = int(timeout) if timeout is not None else 10

    rows: list[dict[str, Any]] = []
    last_err: Optional[str] = None

    logger.info("DuckDuckGo search start: query=%r max_results=%d timeout=%s", q_search, max_results, to)

    try:
        with DDGS(timeout=to) as ddgs:
            # Try preferred public backends first, then default.
            # Some ddgs versions may not accept the `backend` kwarg.
            for backend in ("lite", "html", None):
                if rows:
                    break
                try:
                    if backend is None:
                        rows = ddgs.text(q_search, max_results=max_results) or []
                        logger.info("DuckDuckGo backend=default returned %d rows", len(rows))
                    else:
                        rows = ddgs.text(q_search, max_results=max_results, backend=backend) or []
                        logger.info("DuckDuckGo backend=%s returned %d rows", backend, len(rows))
                except TypeError as ex:
                    # Older/newer versions may not support backend arg; fall back to default.
                    last_err = str(ex)
                    logger.debug("DuckDuckGo backend arg unsupported: %s", ex)
                    if backend is not None:
                        continue
                except Exception as ex:
                    last_err = str(ex)
                    if backend is None:
                        logger.info("DuckDuckGo default backend: %s", ex)
                    else:
                        logger.info("DuckDuckGo backend=%s: %s", backend, ex)

        if not rows and last_err:
            return SearchResponse(success=False, error=last_err, results=[], query=q)

        logger.info("DuckDuckGo search done: query=%r results=%d", q_search, len(rows))
        for idx, row in enumerate(rows[:3], start=1):
            title = str(row.get("title") or row.get("Title") or f"Result {idx}")
            snippet = str(
                row.get("description")
                or row.get("snippet")
                or row.get("body")
                or row.get("Snippet")
                or ""
            )
            snippet = " ".join(snippet.split())[:180]
            logger.info("DDG result %d: title=%r snippet=%r", idx, title, snippet)

        return search_response_from_rows(q, rows)
    except Exception as e:
        logger.error("DuckDuckGo search failed: %s", e)
        return SearchResponse(
            success=False,
            error=str(e),
            results=[],
            query=q,
        )