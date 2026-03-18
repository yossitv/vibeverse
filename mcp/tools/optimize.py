"""3D model optimization for Roblox Studio.

For the MVP this performs basic validation and copies the file as the
"optimized" output.  A production version would run mesh decimation,
texture compression, etc.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "storage" / "assets"


def optimize_model(model_path: str, job_id: str) -> str:
    """Validate and copy the model as the optimized version.

    Returns the path to the optimized file.
    """
    src = Path(model_path)
    if not src.exists():
        raise FileNotFoundError(f"Model not found: {model_path}")

    job_dir = ASSETS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    dest = job_dir / "optimized.glb"
    shutil.copy2(src, dest)
    return str(dest)
