from __future__ import annotations

from pathlib import Path

import numpy as np
from brainrender import Scene
from brainrender.actors import Points

from bg_viz_pipeline.lib.styles import (
    CUSTOM_REGION_ALPHA,
    CUSTOM_REGION_COLOR,
    PROBE_COLOR,
    PROBE_RADIUS,
)
from bg_viz_pipeline.lib.view_config import ViewConfig


def subject_from_folder(folder: Path) -> str:
    """
    Extract subject ID from a brainreg folder name like
    ds_SUBJECT_YYYYMMDD_...
    """
    name = folder.name
    if name.startswith("ds_"):
        parts = name.split("_")
        if len(parts) >= 2:
            return parts[1]
    return name


def print_root_bounds(scene: Scene, subject_id: str) -> None:
    """Log atlas root bounds (batch debugging)."""
    if not hasattr(scene, "root") or scene.root is None:
        return
    xmin, xmax, ymin, ymax, zmin, zmax = scene.root.bounds()
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    zmid = 0.5 * (zmin + zmax)
    print(
        f"{subject_id}:",
        "bounds",
        f"x=[{xmin:.1f}, {xmax:.1f}]",
        f"y=[{ymin:.1f}, {ymax:.1f}]",
        f"z=[{zmin:.1f}, {zmax:.1f}]",
    )
    print(f"{subject_id}: centre=({xmid:.1f}, {ymid:.1f}, {zmid:.1f})")


def add_brainreg_overlays(
    scene: Scene,
    brainreg_dir: Path,
    config: ViewConfig,
) -> None:
    """Add probe tracks, custom ``.obj`` regions, and brainmapper cells."""
    atlas_space_dir = brainreg_dir / "segmentation" / "atlas_space"
    tracks_dir = atlas_space_dir / "tracks"
    regions_dir = atlas_space_dir / "regions"
    cells_path = brainreg_dir / "brainmapper" / "points" / "points.npy"

    for npy_path in sorted(tracks_dir.glob("*.npy")):
        coords = np.load(npy_path)
        scene.add(
            Points(
                coords,
                name=npy_path.stem,
                colors=PROBE_COLOR,
                radius=PROBE_RADIUS,
            )
        )

    if regions_dir.exists():
        for obj_path in sorted(regions_dir.glob("*.obj")):
            scene.add(
                str(obj_path),
                color=CUSTOM_REGION_COLOR,
                alpha=CUSTOM_REGION_ALPHA,
            )

    if cells_path.exists():
        cells = np.load(cells_path)
        total_cells = len(cells)
        if total_cells > config.max_points:
            step = total_cells / config.max_points
            idx = (np.arange(config.max_points) * step).astype(int)
            cells = cells[idx]
        scene.add(Points(cells, radius=45, colors="palegoldenrod"))
