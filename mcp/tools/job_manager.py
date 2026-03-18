"""Job lifecycle management – create, update, and query jobs stored as local JSON."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "storage" / "sessions"

VALID_STATUSES = [
    "queued",
    "running",
    "image_generated",
    "converted_to_3d",
    "optimized",
    "exported",
    "placed",
    "failed",
]


def _ensure_dir() -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def create_job(prompt: str) -> dict[str, Any]:
    _ensure_dir()
    job_id = uuid.uuid4().hex[:12]
    job = {
        "job_id": job_id,
        "prompt": prompt,
        "status": "queued",
        "created_at": time.time(),
        "updated_at": time.time(),
        "image_paths": [],
        "model_path": None,
        "optimized_model_path": None,
        "exported_path": None,
        "tags": [],
        "error": None,
    }
    _save(job)
    return job


def get_job(job_id: str) -> dict[str, Any] | None:
    path = SESSIONS_DIR / f"{job_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def update_job(job_id: str, **fields: Any) -> dict[str, Any]:
    job = get_job(job_id)
    if job is None:
        raise ValueError(f"Job {job_id} not found")
    job.update(fields, updated_at=time.time())
    _save(job)
    return job


def list_jobs() -> list[dict[str, Any]]:
    _ensure_dir()
    jobs = []
    for p in sorted(SESSIONS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        jobs.append(json.loads(p.read_text()))
    return jobs


def _save(job: dict[str, Any]) -> None:
    path = SESSIONS_DIR / f"{job['job_id']}.json"
    path.write_text(json.dumps(job, indent=2))
