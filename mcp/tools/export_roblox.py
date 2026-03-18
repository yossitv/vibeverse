"""Export an optimized 3D model for Roblox Studio consumption.

For the MVP the export step copies the GLB into an ``exported/`` directory
and writes a companion metadata JSON that the Roblox plugin can read.
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "storage" / "assets"


def export_for_roblox(optimized_path: str, job_id: str, prompt: str) -> str:
    """Prepare the final asset bundle for the Roblox plugin.

    Returns the path to the exported directory.
    """
    src = Path(optimized_path)
    if not src.exists():
        raise FileNotFoundError(f"Optimized model not found: {optimized_path}")

    export_dir = ASSETS_DIR / job_id / "exported"
    export_dir.mkdir(parents=True, exist_ok=True)

    dest_model = export_dir / "model.glb"
    shutil.copy2(src, dest_model)

    metadata = {
        "job_id": job_id,
        "prompt": prompt,
        "model_file": str(dest_model),
        "format": "glb",
        "exported_at": time.time(),
    }
    meta_path = export_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))

    return str(export_dir)
