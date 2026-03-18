from __future__ import annotations

import json
import secrets
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable

DEFAULT_PROJECT = "gtc_event_assets"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_event(job: dict[str, Any], status: str, event_type: str, message: str) -> None:
    job.setdefault("events", []).append(
        {
            "timestamp": utc_now(),
            "status": status,
            "type": event_type,
            "message": message,
        }
    )


def append_assistant_message(job: dict[str, Any], content: str) -> None:
    job.setdefault("messages", []).append(
        {
            "role": "assistant",
            "content": content,
            "timestamp": utc_now(),
        }
    )


class LocalJobStore:
    def __init__(self, root_dir: str | Path, project: str = DEFAULT_PROJECT) -> None:
        self.root_dir = Path(root_dir).resolve()
        self.backend_dir = self.root_dir / "backend"
        self.jobs_dir = self.backend_dir / "jobs"
        self.sessions_dir = self.jobs_dir / "sessions"
        self.project_dir = self.jobs_dir / "projects" / project
        self.assets_dir = self.project_dir / "assets"
        self.assets_index_file = self.project_dir / "assets.json"
        self.project = project
        self._lock = threading.RLock()
        self.ensure_layout()

    def ensure_layout(self) -> None:
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        if not self.assets_index_file.exists():
            self._write_json(self.assets_index_file, [])

    def create_job(self, prompt: str) -> dict[str, Any]:
        base_id = secrets.token_hex(6)
        job_id = f"job_{base_id}"
        session_id = f"sess_{base_id}"
        asset_id = f"asset_{base_id}"
        asset_dir = self.assets_dir / asset_id
        asset_dir.mkdir(parents=True, exist_ok=True)

        created_at = utc_now()
        job = {
            "job_id": job_id,
            "session_id": session_id,
            "asset_id": asset_id,
            "project": self.project,
            "prompt": prompt,
            "status": "queued",
            "created_at": created_at,
            "updated_at": created_at,
            "error": None,
            "paths": {
                "session_record": str(self._job_record_path(job_id).resolve()),
                "asset_dir": str(asset_dir.resolve()),
                "candidate_images": [],
                "model_path": None,
                "optimized_model_path": None,
                "export_path": None,
                "metadata_path": str((asset_dir / "meta.json").resolve()),
            },
            "asset": {
                "asset_id": asset_id,
                "project": self.project,
                "preview_image": None,
                "model_path": None,
                "optimized_model_path": None,
                "export_path": None,
                "metadata_path": str((asset_dir / "meta.json").resolve()),
                "tags": [],
                "placement": {
                    "status": "pending",
                    "placed_at": None,
                },
            },
            "events": [],
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "timestamp": created_at,
                }
            ],
        }

        append_event(job, "queued", "request_created", "Job created and queued.")
        append_assistant_message(job, "Job queued. Waiting to start the asset pipeline.")

        with self._lock:
            self._write_json(self._job_record_path(job_id), job)
            self._write_asset_metadata_locked(job)
            self._upsert_asset_index_locked(job)

        return deepcopy(job)

    def get_job(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._load_job_locked(job_id))

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            jobs = [self._job_summary(self._read_json(path)) for path in self.sessions_dir.glob("sess_*.json")]
        jobs.sort(key=lambda item: item["created_at"], reverse=True)
        return jobs

    def mutate_job(
        self,
        job_id: str,
        mutator: Callable[[dict[str, Any]], None],
    ) -> dict[str, Any]:
        with self._lock:
            job = self._load_job_locked(job_id)
            mutator(job)
            job["updated_at"] = utc_now()
            self._write_json(self._job_record_path(job_id), job)
            self._write_asset_metadata_locked(job)
            self._upsert_asset_index_locked(job)
            return deepcopy(job)

    def mark_placed(self, job_id: str) -> dict[str, Any]:
        def apply(job: dict[str, Any]) -> None:
            if job["status"] not in {"exported", "placed"}:
                raise ValueError("Job must be exported before it can be marked as placed.")
            if job["status"] == "placed":
                return

            placed_at = utc_now()
            job["status"] = "placed"
            job["asset"]["placement"] = {
                "status": "placed",
                "placed_at": placed_at,
            }
            append_event(job, "placed", "placed_in_studio", "Asset marked as placed in Roblox Studio.")
            append_assistant_message(job, "Asset marked as placed in Roblox Studio.")

        return self.mutate_job(job_id, apply)

    def sync_asset_metadata(self, job_id: str) -> dict[str, Any]:
        with self._lock:
            job = self._load_job_locked(job_id)
            self._write_asset_metadata_locked(job)
            self._write_json(self._job_record_path(job_id), job)
            self._upsert_asset_index_locked(job)
            return deepcopy(job)

    def _job_summary(self, job: dict[str, Any]) -> dict[str, Any]:
        return {
            "job_id": job["job_id"],
            "session_id": job["session_id"],
            "asset_id": job["asset_id"],
            "prompt": job["prompt"],
            "status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        }

    def _job_record_path(self, job_id: str) -> Path:
        suffix = job_id.removeprefix("job_")
        return self.sessions_dir / f"sess_{suffix}.json"

    def _load_job_locked(self, job_id: str) -> dict[str, Any]:
        path = self._job_record_path(job_id)
        if not path.exists():
            raise KeyError(job_id)
        return self._read_json(path)

    def _upsert_asset_index_locked(self, job: dict[str, Any]) -> None:
        items = self._read_json(self.assets_index_file)
        summary = {
            "asset_id": job["asset_id"],
            "job_id": job["job_id"],
            "prompt": job["prompt"],
            "status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "preview_image": job["asset"]["preview_image"],
            "export_path": job["paths"]["export_path"],
            "metadata_path": job["paths"]["metadata_path"],
        }
        items = [item for item in items if item.get("job_id") != job["job_id"]]
        items.append(summary)
        items.sort(key=lambda item: item["created_at"], reverse=True)
        self._write_json(self.assets_index_file, items)

    def _write_asset_metadata_locked(self, job: dict[str, Any]) -> None:
        metadata_path = Path(job["paths"]["metadata_path"])
        metadata = {
            "asset_id": job["asset_id"],
            "job_id": job["job_id"],
            "project": job["project"],
            "prompt": job["prompt"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "status": job["status"],
            "tags": job["asset"]["tags"],
            "placement": job["asset"]["placement"],
            "generated_file_paths": {
                "candidate_images": job["paths"]["candidate_images"],
                "model_path": job["paths"]["model_path"],
                "optimized_model_path": job["paths"]["optimized_model_path"],
                "export_path": job["paths"]["export_path"],
            },
        }
        self._write_json(metadata_path, metadata)

    def _read_json(self, path: Path) -> Any:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            temp_path = Path(handle.name)
        temp_path.replace(path)
