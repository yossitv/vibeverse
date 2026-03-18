"""VibeVerse MCP Server – asset pipeline tools for Roblox Studio.

Run:
    fastmcp run server.py:mcp
    # or
    python server.py
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

# Load .env from the project root
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from tools import job_manager, image_gen, convert_3d, optimize, export_roblox

mcp = FastMCP("VibeVerse")

# ---------------------------------------------------------------------------
# Resources – read-only data the client can inspect
# ---------------------------------------------------------------------------


@mcp.resource("vibeverse://jobs")
def list_jobs() -> str:
    """List all jobs with their current status."""
    return json.dumps(job_manager.list_jobs(), indent=2)


@mcp.resource("vibeverse://jobs/{job_id}")
def get_job(job_id: str) -> str:
    """Get details for a specific job."""
    job = job_manager.get_job(job_id)
    if job is None:
        return json.dumps({"error": f"Job {job_id} not found"})
    return json.dumps(job, indent=2)


# ---------------------------------------------------------------------------
# Tools – callable pipeline steps (section 6.8 of idea.md)
# ---------------------------------------------------------------------------


@mcp.tool()
async def generate_candidates(prompt: str) -> str:
    """Generate candidate images from a text prompt.

    Creates a new job, calls the image generation API, saves the images
    locally, and returns the job state including saved file paths.
    """
    job = job_manager.create_job(prompt)
    job_id = job["job_id"]

    try:
        job_manager.update_job(job_id, status="running")
        paths = await image_gen.generate_image(prompt, job_id)
        job = job_manager.update_job(job_id, status="image_generated", image_paths=paths)
    except Exception as exc:
        job = job_manager.update_job(job_id, status="failed", error=str(exc))

    return json.dumps(job, indent=2)


@mcp.tool()
async def convert_to_3d(job_id: str, image_index: int = 0) -> str:
    """Convert a generated image into a 3D object via Meshy AI.

    Uses the image at *image_index* from the job's candidate list.
    Returns updated job state with the model path.
    """
    job = job_manager.get_job(job_id)
    if job is None:
        return json.dumps({"error": f"Job {job_id} not found"})

    images = job.get("image_paths", [])
    if not images:
        return json.dumps({"error": "No images generated yet – run generate_candidates first"})
    if image_index >= len(images):
        return json.dumps({"error": f"image_index {image_index} out of range (have {len(images)})"})

    image_path = images[image_index]

    try:
        job_manager.update_job(job_id, status="running")
        model_path = await convert_3d.convert_image_to_3d(image_path, job_id)
        job = job_manager.update_job(job_id, status="converted_to_3d", model_path=model_path)
    except Exception as exc:
        job = job_manager.update_job(job_id, status="failed", error=str(exc))

    return json.dumps(job, indent=2)


@mcp.tool()
def tag_asset(job_id: str, tags: list[str]) -> str:
    """Add metadata tags to a job's asset.

    Tags are free-form strings (e.g. ["nvidia", "event-prop", "static"]).
    Returns updated job state.
    """
    job = job_manager.get_job(job_id)
    if job is None:
        return json.dumps({"error": f"Job {job_id} not found"})

    existing = set(job.get("tags", []))
    existing.update(tags)
    job = job_manager.update_job(job_id, tags=sorted(existing))
    return json.dumps(job, indent=2)


@mcp.tool()
def export_for_roblox(job_id: str) -> str:
    """Optimize and export a 3D asset for Roblox Studio.

    Runs the optimization step, then prepares the export bundle
    (GLB + metadata JSON) that the Roblox plugin can consume.
    Returns updated job state with the exported path.
    """
    job = job_manager.get_job(job_id)
    if job is None:
        return json.dumps({"error": f"Job {job_id} not found"})

    model_path = job.get("model_path")
    if not model_path:
        return json.dumps({"error": "No 3D model yet – run convert_to_3d first"})

    try:
        optimized = optimize.optimize_model(model_path, job_id)
        job_manager.update_job(job_id, status="optimized", optimized_model_path=optimized)

        exported = export_roblox.export_for_roblox(optimized, job_id, job["prompt"])
        job = job_manager.update_job(job_id, status="exported", exported_path=exported)
    except Exception as exc:
        job = job_manager.update_job(job_id, status="failed", error=str(exc))

    return json.dumps(job, indent=2)


@mcp.tool()
def get_job_status(job_id: str) -> str:
    """Check the current status of a pipeline job."""
    job = job_manager.get_job(job_id)
    if job is None:
        return json.dumps({"error": f"Job {job_id} not found"})
    return json.dumps(job, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
