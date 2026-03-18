"""Image-to-3D conversion via Meshy AI API."""

from __future__ import annotations

import asyncio
import base64
import os
from pathlib import Path

import httpx

ASSETS_DIR = Path(__file__).resolve().parent.parent / "storage" / "assets"

API_KEY_ENV = "MESHY_API_KEY"
BASE_URL = "https://api.meshy.ai/openapi/v1"

POLL_INTERVAL = 5  # seconds
MAX_POLL_ATTEMPTS = 120  # 10 minutes


def _headers() -> dict[str, str]:
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{API_KEY_ENV} is not set")
    return {"Authorization": f"Bearer {api_key}"}


async def create_task(image_path: str) -> str:
    """Submit an image-to-3D task and return the task_id."""
    img_bytes = Path(image_path).read_bytes()
    b64 = base64.b64encode(img_bytes).decode()
    data_uri = f"data:image/png;base64,{b64}"

    body = {
        "image_url": data_uri,
        "enable_pbr": True,
    }

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{BASE_URL}/image-to-3d",
            headers=_headers(),
            json=body,
        )
        resp.raise_for_status()

    return resp.json()["result"]


async def poll_until_done(task_id: str) -> str:
    """Poll the task status until SUCCEEDED and return the GLB download URL."""
    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(MAX_POLL_ATTEMPTS):
            resp = await client.get(
                f"{BASE_URL}/image-to-3d/{task_id}",
                headers=_headers(),
            )
            resp.raise_for_status()
            status_data = resp.json()

            status = status_data.get("status")
            if status == "SUCCEEDED":
                glb_url = (status_data.get("model_urls") or {}).get("glb")
                if glb_url:
                    return glb_url
                raise RuntimeError("Task succeeded but no GLB URL in response")
            if status in ("FAILED", "CANCELED"):
                err = (status_data.get("task_error") or {}).get("message", "unknown")
                raise RuntimeError(f"Meshy task {status}: {err}")

            await asyncio.sleep(POLL_INTERVAL)

    raise RuntimeError("Timed out waiting for Meshy task")


async def download_glb(url: str, job_id: str, suffix: str = "model") -> str:
    """Download a GLB file and save it locally. Returns the saved path."""
    job_dir = ASSETS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    path = job_dir / f"{suffix}.glb"
    path.write_bytes(resp.content)
    return str(path)


async def convert_image_to_3d(image_path: str, job_id: str) -> str:
    """Full pipeline: submit image, poll, download GLB. Returns local path."""
    task_id = await create_task(image_path)
    glb_url = await poll_until_done(task_id)
    return await download_glb(glb_url, job_id)
