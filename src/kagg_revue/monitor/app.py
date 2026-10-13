"""FastAPI application for loopback-only experiment monitoring."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from kagg_revue.monitor.artifacts import RunRepository
from kagg_revue.monitor.config import MonitorSettings
from kagg_revue.monitor.curves import CurveQuery
from kagg_revue.monitor.opponents.query import OpponentQuery
from kagg_revue.monitor.system import SystemSampler

_UI_FILES = (
    "index.html",
    "styles.css",
    "app.js",
    "charts.js",
    "evaluation.js",
    "search.js",
    "apprentice.js",
    "branching.js",
    "learning.js",
    "quadrants.js",
    "opponents.js",
    "opponent-view.js",
    "opponents.css",
    "league.js",
    "explorer.js",
    "explorer.css",
    "plot.js",
    "pretraining.js",
    "pretraining.css",
)


def _ui_version(static_dir: Path) -> str:
    """Return a content identity shared by the HTML and static assets."""
    digest = hashlib.sha256()
    for name in _UI_FILES:
        digest.update(name.encode("utf-8"))
        digest.update((static_dir / name).read_bytes())
    return digest.hexdigest()[:12]


def _active_run_ids(system: dict[str, object]) -> set[str]:
    processes = system.get("training_processes")
    if not isinstance(processes, list):
        return set()
    return {
        str(process["run_id"])
        for process in processes
        if isinstance(process, dict) and "run_id" in process
    }


def create_app(settings: MonitorSettings, repository_root: Path) -> FastAPI:
    """Create a read-only dashboard application for one repository."""
    repository = RunRepository(repository_root, settings)
    sampler = SystemSampler(repository.repository_root, repository.outputs_dir)
    static_dir = Path(__file__).with_name("static")
    ui_version = _ui_version(static_dir)
    index_html = (
        (static_dir / "index.html")
        .read_text(encoding="utf-8")
        .replace("__UI_VERSION__", ui_version)
    )
    app = FastAPI(
        title="Revue Training Monitor",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.mount("/assets", StaticFiles(directory=static_dir), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> HTMLResponse:
        return HTMLResponse(index_html, headers={"Cache-Control": "no-cache"})

    @app.get("/api/overview")
    def overview(response: Response) -> dict[str, object]:
        response.headers["Cache-Control"] = "no-store"
        system = sampler.snapshot()
        runs = repository.list_runs(_active_run_ids(system))
        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "ui_version": ui_version,
            "refresh_seconds": settings.refresh_seconds,
            "display_defaults": {
                "window": settings.default_window,
                "smoothing": settings.smoothing_window,
                "raw": settings.show_raw,
            },
            "runs": runs,
            "system": system,
        }

    @app.get("/api/curves/{run_id:path}")
    def run_curves(
        run_id: str,
        response: Response,
        window: int = Query(default=500, ge=0, le=1_000_000),
        start: int | None = Query(default=None, ge=0),
        end: int | None = Query(default=None, ge=0),
        smoothing: int = Query(default=32, ge=1, le=2048),
        tags: str = Query(default="", max_length=8192),
    ) -> dict[str, object]:
        response.headers["Cache-Control"] = "no-store"
        try:
            return repository.curves(
                run_id,
                CurveQuery(
                    window=window,
                    start=start,
                    end=end,
                    smoothing=smoothing,
                    tags=tuple(tag for tag in tags.split(",") if tag),
                ),
            )
        except ValidationError as error:
            raise HTTPException(status_code=422, detail="invalid curve range") from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="run not found") from error

    @app.get("/api/opponents/{run_id:path}")
    def run_opponents(
        run_id: str,
        response: Response,
        window: int = Query(default=500, ge=0, le=1_000_000),
        start: int | None = Query(default=None, ge=0),
        end: int | None = Query(default=None, ge=0),
        smoothing: int = Query(default=32, ge=1, le=2048),
        opponent: str | None = Query(default=None, min_length=1, max_length=512),
        before: int | None = Query(default=None, ge=1),
        limit: int = Query(default=50, ge=1, le=200),
    ) -> dict[str, object]:
        response.headers["Cache-Control"] = "no-store"
        try:
            return repository.opponents(
                run_id,
                OpponentQuery(
                    window=window,
                    start=start,
                    end=end,
                    smoothing=smoothing,
                    opponent=opponent,
                    before=before,
                    limit=limit,
                ),
            )
        except ValidationError as error:
            raise HTTPException(status_code=422, detail="invalid opponent range") from error
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="run not found") from error

    @app.get("/api/runs/{run_id:path}")
    def run_detail(
        run_id: str,
        response: Response,
        after_modified: float | None = None,
    ) -> dict[str, object]:
        response.headers["Cache-Control"] = "no-store"
        system = sampler.snapshot()
        processes_value = system.get("training_processes")
        processes = (
            cast(list[dict[str, object]], processes_value)
            if isinstance(processes_value, list)
            else []
        )
        try:
            return repository.detail(
                run_id,
                _active_run_ids(system),
                processes,
                after_modified=after_modified,
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="run not found") from error

    @app.get("/api/health")
    def health(response: Response) -> dict[str, object]:
        response.headers["Cache-Control"] = "no-store"
        return {
            "status": "ok",
            "bind_scope": "loopback",
            "ui_version": ui_version,
            "generated_at": datetime.now(UTC).isoformat(),
        }

    return app


__all__ = ["create_app"]
