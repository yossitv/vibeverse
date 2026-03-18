"""Image generation via Gemini Nano Banana Pro (text-to-image)."""

from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import httpx

ASSETS_DIR = Path(__file__).resolve().parent.parent / "storage" / "assets"

API_KEY_ENV = "GEMINI_API_KEY"
MODEL = "nano-banana-pro-preview"
ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
)


async def generate_image(prompt: str, job_id: str) -> list[str]:
    """Generate a robot/object concept image from a text prompt.

    Returns a list of saved file paths.
    """
    api_key = os.environ.get(API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"{API_KEY_ENV} is not set")

    enriched_prompt = (
        f"{prompt}, highly detailed, full body visible from head to toe, "
        "A-pose with slightly spread arms, single white background #FFFFFF, "
        "clear silhouette, studio lighting, no cropping"
    )

    body = {
        "contents": [{"parts": [{"text": enriched_prompt}]}],
    }

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"{ENDPOINT}?key={api_key}",
            json=body,
        )
        resp.raise_for_status()

    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("No candidates returned from image generation API")

    saved: list[str] = []
    job_dir = ASSETS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    for idx, candidate in enumerate(candidates):
        for part in candidate.get("content", {}).get("parts", []):
            inline = part.get("inlineData")
            if inline and inline.get("data"):
                img_bytes = base64.b64decode(inline["data"])
                filename = f"candidate_{idx}_{int(time.time())}.png"
                path = job_dir / filename
                path.write_bytes(img_bytes)
                saved.append(str(path))

    if not saved:
        raise RuntimeError("Image generation returned no image data")

    return saved
