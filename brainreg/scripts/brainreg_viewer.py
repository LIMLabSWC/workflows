#!/usr/bin/env python3
"""Batch-render brainreg scenes from JSON presets to PNG (offscreen)."""

import argparse
import json
from pathlib import Path

import numpy as np
from brainrender import Scene, settings
from brainrender.actors import Points
from brainreg.lib.camera_helpers import create_camera
from brainreg.lib.styles import (
    REGION_ALPHA,
    ROOT_ALPHA,
    ROOT_COLOR,
    CUSTOM_REGION_COLOR,
    CUSTOM_REGION_ALPHA,
    PROBE_COLOR,
    PROBE_RADIUS,
)

# Global brainrender look via settings API (applies to all scenes)
settings.LIGHTING = "default"
settings.SHADER_STYLE = "plastic"
settings.SHOW_AXES = False
settings.SCREENSHOT_TRANSPARENT_BACKGROUND = False


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


def _sanitize_for_filename(s: str) -> str:
    """Make a string safe for use as a filename."""
    return "".join(
        c if c.isalnum() or c in ("-", "_", ".") else "_"  # noqa: PLR1704
        for c in s
    )


# ============================
# GLOBAL SETTINGS
# ============================

# Atlas name used by brainreg for these data
ATLAS_NAME = "swc_female_rat_50um"

# Base directory with all subjects
BASE_DIR = Path(
    "/home/viktor/use_cases"
)


def render_one(preset: dict) -> None:
    """
    Render one PNG for a preset.

    Requires ``.../atlas_space/tracks`` with at least one ``.npy``.
    """

    # Unpack preset parameters
    brainreg_dir = BASE_DIR / preset["BRAINREG_SUBDIR"]
    regions_to_show = preset["REGIONS_TO_SHOW"]
    camera_distance_factor = preset["CAMERA_DISTANCE_FACTOR"]
    camera_rotation_deg = preset["CAMERA_ROTATION_DEG"]
    camera_elevation_deg = preset["CAMERA_ELEVATION_DEG"]
    slice_mode = preset.get("SLICE_MODE", "none")
    plane_depth = preset.get("PLANE_DEPTH", 0.0)
    custom_plane_normal = tuple(
        preset.get("CUSTOM_PLANE_NORMAL", (0.0, 0.0, 1.0))
    )
    show_root = preset.get("SHOW_ROOT", True)
    max_points = preset.get("MAX_POINTS", 5000)

    atlas_space_dir = brainreg_dir / "segmentation" / "atlas_space"
    tracks_dir = atlas_space_dir / "tracks"
    regions_dir = atlas_space_dir / "regions"
    cells_path = brainreg_dir / "brainmapper" / "points" / "points.npy"

    subject_id = subject_from_folder(brainreg_dir)
    scene = Scene(atlas_name=ATLAS_NAME, title=subject_id)
    scene.plotter.window.SetOffScreenRendering(True)

    # Add atlas regions
    for region in regions_to_show:
        scene.add_brain_region(region, alpha=REGION_ALPHA, silhouette=True)

    # Soften the whole-brain outline so regions/probes stand out
    if hasattr(scene, "root") and scene.root is not None:

        if show_root:
            scene.root.c(ROOT_COLOR).alpha(ROOT_ALPHA)
        else:
            scene.root.alpha(0)



        # Print atlas/root mesh bounds and compute camera
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

        _BASE_FRONTAL_AZIMUTH_DEG = 180.0
        active_camera = create_camera(
            (xmin, xmax, ymin, ymax, zmin, zmax),
            distance_factor=camera_distance_factor,
            base_frontal_azimuth_deg=_BASE_FRONTAL_AZIMUTH_DEG,
            rotation_deg=camera_rotation_deg,
            elevation_deg=camera_elevation_deg,
        )
    else:
        active_camera = None

    # Add probe tracks
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

    # Add custom segmented regions
    if regions_dir.exists():
        for obj_path in sorted(regions_dir.glob("*.obj")):
            scene.add(
                str(obj_path),
                color=CUSTOM_REGION_COLOR,
                alpha=CUSTOM_REGION_ALPHA,
            )

    # Add brainmapper cells
    if cells_path.exists():
        cells = np.load(cells_path)
        total_cells = len(cells)

        if total_cells > max_points:
            step = total_cells / max_points
            idx = (np.arange(max_points) * step).astype(int)
            cells = cells[idx]

        cells = Points(cells, radius=45, colors="palegoldenrod")
        scene.add(cells)


    # Optional slicing
    if slice_mode not in (None, "none"):
        if slice_mode == "custom":
            plane_arg = None
            if hasattr(scene, "root") and scene.root is not None:
                xmin, xmax, ymin, ymax, zmin, zmax = scene.root.bounds()
                xmid = 0.5 * (xmin + xmax)
                ymid = 0.5 * (ymin + ymax)
                zmid = 0.5 * (zmin + zmax)

                nx, ny, nz = custom_plane_normal
                ax = abs(nx)
                ay = abs(ny)
                az = abs(nz)

                if ax >= ay and ax >= az:
                    start = xmin if nx >= 0 else xmax
                    centre = xmid
                    cx = start + plane_depth * (centre - start)
                    cy = ymid
                    cz = zmid
                elif ay >= ax and ay >= az:
                    start = ymin if ny >= 0 else ymax
                    centre = ymid
                    cx = xmid
                    cy = start + plane_depth * (centre - start)
                    cz = zmid
                else:
                    start = zmin if nz >= 0 else zmax
                    centre = zmid
                    cx = xmid
                    cy = ymid
                    cz = start + plane_depth * (centre - start)

                plane_pos = (cx, cy, cz)
                custom_plane = scene.atlas.get_plane(
                    pos=plane_pos,
                    norm=custom_plane_normal,
                )
                plane_arg = custom_plane
        else:
            plane_arg = slice_mode

        if plane_arg is not None:
            scene.slice(
                plane=plane_arg,
                actors=None,
            )

    # Rendering and saving
    scene.plotter.axes = 9

    parts = [f"sub-{subject_id}"]
    parts.append(f"dist-{camera_distance_factor:.2f}")
    parts.append(f"rot-{camera_rotation_deg:.1f}")
    parts.append(f"el-{camera_elevation_deg:.1f}")

    if slice_mode and slice_mode not in ("none", None):
        parts.append(f"slice-{slice_mode}")
        if slice_mode == "custom":
            parts.append(f"depth-{plane_depth:.2f}")
            parts.append(
                "n-"
                f"{custom_plane_normal[0]:.2f}_"
                f"{custom_plane_normal[1]:.2f}_"
                f"{custom_plane_normal[2]:.2f}"
            )

    scene.title = " | ".join(parts)
    filename_base = "_".join(parts)
    filename = _sanitize_for_filename(filename_base) + ".png"

    if active_camera is not None:
        scene.render(camera=active_camera, interactive=False)
    else:
        scene.render(interactive=False)

    scene.screenshot(name=filename, scale=2)


def render_all(presets: list[dict], args: argparse.Namespace) -> None:
    """
    Iterate over all presets and render the ones matching CLI filters.
    """
    for preset in presets:
        subdir = preset["BRAINREG_SUBDIR"]

        if args.only_subdir and args.only_subdir not in subdir:
            continue

        if args.only_subject:
            subj = subject_from_folder(Path(subdir))
            if args.only_subject not in subj:
                continue

        render_one(preset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render brainreg PNG views from JSON presets."
    )
    parser.add_argument(
        "--only-subdir",
        type=str,
        help=(
            "Only render presets whose BRAINREG_SUBDIR contains this "
            "substring."
        ),
    )
    parser.add_argument(
        "--only-subject",
        type=str,
        help=(
            "Only render presets whose derived subject_id (from folder name) "
            "contains this substring (e.g. 'ROI-1', 'MPX-R-0033')."
        ),
    )
    args = parser.parse_args()

    presets_path = (
        Path(__file__).resolve().parents[1] / "presets" / "viewer_presets.json"
    )
    with presets_path.open() as f:
        presets = json.load(f)

    render_all(presets, args)

