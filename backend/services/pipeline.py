from __future__ import annotations

import base64
import re
import threading
from pathlib import Path
from time import sleep
from typing import Any, Callable

from backend.services.storage import LocalJobStore, append_assistant_message, append_event

PREVIEW_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnRk2QAAAAASUVORK5CYII="
)

CUBE_OBJ = """# VibeVerse generated cube
o vibeverse_asset
v -0.5 -0.5 -0.5
v 0.5 -0.5 -0.5
v 0.5 0.5 -0.5
v -0.5 0.5 -0.5
v -0.5 -0.5 0.5
v 0.5 -0.5 0.5
v 0.5 0.5 0.5
v -0.5 0.5 0.5
f 1 2 3 4
f 5 6 7 8
f 1 5 8 4
f 2 6 7 3
f 4 3 7 8
f 1 2 6 5
"""

STOP_WORDS = {
    "a",
    "an",
    "and",
    "asset",
    "based",
    "create",
    "event",
    "for",
    "from",
    "image",
    "in",
    "of",
    "on",
    "prop",
    "the",
    "to",
    "with",
}


class DemoPipelineRunner:
    def __init__(self, store: LocalJobStore, step_delay: float = 0.15) -> None:
        self.store = store
        self.step_delay = step_delay

    def run_async(self, job_id: str) -> None:
        thread = threading.Thread(target=self._run_job, args=(job_id,), daemon=True)
        thread.start()

    def _run_job(self, job_id: str) -> None:
        try:
            self._transition(job_id, "running", "pipeline_started", "Pipeline started.")
            self._pause()

            preview_path = self._generate_preview(job_id)
            self._transition(
                job_id,
                "image_generated",
                "generate_candidates",
                "Generated a candidate preview image.",
                lambda job: self._set_preview(job, preview_path),
            )
            self._pause()

            model_path = self._convert_to_3d(job_id)
            self._transition(
                job_id,
                "converted_to_3d",
                "convert_to_3d",
                "Converted the preview image into a static 3D object.",
                lambda job: self._set_model(job, model_path),
            )
            self._pause()

            optimized_path = self._optimize(job_id)
            self._transition(
                job_id,
                "optimized",
                "optimize_model",
                "Optimized the generated model for Roblox import.",
                lambda job: self._set_optimized_model(job, optimized_path),
            )
            self._pause()

            export_path = self._export_for_roblox(job_id)
            self._transition(
                job_id,
                "exported",
                "export_for_roblox",
                "Exported a Roblox-ready OBJ asset.",
                lambda job: self._set_export(job, export_path),
            )
            self.store.sync_asset_metadata(job_id)
        except Exception as exc:  # pragma: no cover - defensive path
            def apply(job: dict[str, Any]) -> None:
                job["status"] = "failed"
                job["error"] = str(exc)
                append_event(job, "failed", "pipeline_failed", f"Pipeline failed: {exc}")
                append_assistant_message(job, f"Pipeline failed: {exc}")

            self.store.mutate_job(job_id, apply)
            self.store.sync_asset_metadata(job_id)

    def _transition(
        self,
        job_id: str,
        status: str,
        event_type: str,
        message: str,
        mutator: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        def apply(job: dict[str, Any]) -> None:
            job["status"] = status
            append_event(job, status, event_type, message)
            append_assistant_message(job, message)
            if mutator:
                mutator(job)

        self.store.mutate_job(job_id, apply)

    def _generate_preview(self, job_id: str) -> str:
        job = self.store.get_job(job_id)
        asset_dir = Path(job["paths"]["asset_dir"])
        preview_path = asset_dir / "preview.png"
        preview_path.write_bytes(PREVIEW_PNG_BYTES)
        return str(preview_path.resolve())

    def _convert_to_3d(self, job_id: str) -> str:
        job = self.store.get_job(job_id)
        asset_dir = Path(job["paths"]["asset_dir"])
        prompt = job["prompt"]
        model_path = asset_dir / "model.obj"
        model_path.write_text(f"# prompt: {prompt}\n{CUBE_OBJ}", encoding="utf-8")
        return str(model_path.resolve())

    def _optimize(self, job_id: str) -> str:
        job = self.store.get_job(job_id)
        model_path = Path(job["paths"]["model_path"])
        optimized_path = model_path.with_name("optimized_model.obj")
        source = model_path.read_text(encoding="utf-8")
        optimized_path.write_text("# optimized for Roblox import\n" + source, encoding="utf-8")
        return str(optimized_path.resolve())

    def _export_for_roblox(self, job_id: str) -> str:
        job = self.store.get_job(job_id)
        optimized_path = Path(job["paths"]["optimized_model_path"])
        export_path = optimized_path.with_name("roblox_asset.obj")
        source = optimized_path.read_text(encoding="utf-8")
        export_path.write_text("# roblox export\n" + source, encoding="utf-8")
        return str(export_path.resolve())

    def _set_preview(self, job: dict[str, Any], preview_path: str) -> None:
        job["paths"]["candidate_images"] = [preview_path]
        job["asset"]["preview_image"] = preview_path

    def _set_model(self, job: dict[str, Any], model_path: str) -> None:
        job["paths"]["model_path"] = model_path
        job["asset"]["model_path"] = model_path

    def _set_optimized_model(self, job: dict[str, Any], optimized_path: str) -> None:
        job["paths"]["optimized_model_path"] = optimized_path
        job["asset"]["optimized_model_path"] = optimized_path

    def _set_export(self, job: dict[str, Any], export_path: str) -> None:
        tags = self._derive_tags(job["prompt"])
        job["paths"]["export_path"] = export_path
        job["asset"]["export_path"] = export_path
        job["asset"]["tags"] = tags

    def _derive_tags(self, prompt: str) -> list[str]:
        words = re.findall(r"[a-zA-Z0-9]+", prompt.lower())
        tags: list[str] = []
        for word in words:
            if word in STOP_WORDS or word in tags:
                continue
            tags.append(word)
            if len(tags) == 5:
                break
        return tags

    def _pause(self) -> None:
        if self.step_delay > 0:
            sleep(self.step_delay)
