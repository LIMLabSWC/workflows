#!/usr/bin/env python3
from pathlib import Path

import numpy as np
import brainrender
from brainrender import Scene
from brainrender.actors import Points
from camera_helpers import create_camera
from styles import (
    REGION_ALPHA,
    ROOT_ALPHA,
    ROOT_COLOR,
    CUSTOM_REGION_COLOR,
    CUSTOM_REGION_ALPHA,
    PROBE_COLOR,
    PROBE_RADIUS,
)


def subject_from_folder(folder: Path) -> str:
    """Extract subject ID from a brainreg folder name like ds_SUBJECT_YYYYMMDD_..."""
    name = folder.name
    if name.startswith("ds_"):
        parts = name.split("_")
        if len(parts) >= 2:
            return parts[1]
    return name


def _sanitize_for_filename(s: str) -> str:
    """Make a string safe for use as a filename."""
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in s)


# ============================
# GLOBAL SETTINGS
# ============================

# Atlas name used by brainreg for these data
ATLAS_NAME = "swc_female_rat_50um"

# Base directory with all subjects
BASE_DIR = Path(
    "/mnt/d/use_cases_for_paper/brainreg_outputs_swc_female_rat_50um/"
)

# Pick which subject to view (change this line only)
BRAINREG_DIR = BASE_DIR / "ds_MPX-R-0033_250606_133230_25_25_ch02_chan_2_red"

# Regions to highlight from the atlas M2, Cg1
REGIONS_TO_SHOW = [
    #"Am-u",
    "M2",
    "Cg1",
    "cc-ec-cing-dwm",
    #"PrL",
    #"MO",
    #"IL",
]

# Camera configuration (atlas-agnostic)
# CAMERA_DISTANCE_FACTOR:
#   - How far the camera sits from the atlas centre, as a multiple of the
#     largest brain extent. Larger = further away.
CAMERA_DISTANCE_FACTOR = 2.0

# CAMERA_ROTATION_DEG:
#   - Horizontal rotation around the brain, starting from a computed frontal
#     baseline. Use range [-180, 180]: negative = rotate left, positive = rotate right.
CAMERA_ROTATION_DEG = 0

# CAMERA_ELEVATION_DEG:
#   - Vertical tilt (degrees) in this atlas: 0 = level with centre.
#     Negative values (e.g. -10 to -40) look from above, positive from below.
#     Useful range ≈ [-60, 60].
CAMERA_ELEVATION_DEG = -90

# Slice mode:
# - None or "none": no slicing
# - "sagittal" / "frontal" / "horizontal": built‑in orthogonal planes
# - "custom": one atlas-aware slice plane controlled by:
#     * PLANE_DEPTH in [-1, 1] (position along slice axis)
#     * CUSTOM_PLANE_NORMAL (orientation/direction of the cut)

SLICE_MODE = "custom" 

# Normalized depth of the slicing plane within the atlas bounds (used when
# SLICE_MODE == "custom"). This is in [0, 1] and is always measured *inwards
# from the edge you are cutting from*, along the axis selected by
# CUSTOM_PLANE_NORMAL:
#   0.0 = exactly at that edge
#   1.0 = at the centre along that axis
# For example, with CUSTOM_PLANE_NORMAL = (0, 0, 1) (sagittal-like), a depth
# of 0.7 keeps a 70%-thick slab from the left (zmin) towards the centre; flipping
# the normal to (0, 0, -1) cuts the same thickness from the right (zmax).
PLANE_DEPTH = 0.7

# Orientation of the custom plane (works for any atlas). Use one of:
#   (1, 0, 0)  -> frontal-like (front/back split)
#   (0, 1, 0)  -> horizontal-like (top/bottom split)
#   (0, 0, 1)  -> sagittal-like (left/right split)
# Flip the sign to invert which side is kept (e.g. (0, -1, 0)).
CUSTOM_PLANE_NORMAL = (-1.0, 0.0, 0.0)


# Global brainrender look
brainrender.LIGHTING = "default"
brainrender.SHADER_STYLE = "plastic"
brainrender.SHOW_AXES = False
brainrender.SCREENSHOT_TRANSPARENT_BACKGROUND = False


# ============================
# SCENE CONSTRUCTION
# ============================

atlas_space_dir = BRAINREG_DIR / "segmentation" / "atlas_space"
tracks_dir = atlas_space_dir / "tracks"
regions_dir = atlas_space_dir / "regions"

if not tracks_dir.exists():
    raise FileNotFoundError(f"Tracks directory not found: {tracks_dir}")

subject_id = subject_from_folder(BRAINREG_DIR)
scene = Scene(atlas_name=ATLAS_NAME, title=subject_id)


# ============================
# ATLAS REGIONS
# ============================

for region in REGIONS_TO_SHOW:
    scene.add_brain_region(region, alpha=REGION_ALPHA)

# Soften the whole-brain outline so regions/probes stand out
if hasattr(scene, "root") and scene.root is not None:
    scene.root.c(ROOT_COLOR).alpha(ROOT_ALPHA)

    # Print atlas/root mesh bounds to help choose custom slice positions.
    xmin, xmax, ymin, ymax, zmin, zmax = scene.root.bounds()
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    zmid = 0.5 * (zmin + zmax)
    print(
        "Atlas/root bounds:",
        f"x=[{xmin:.1f}, {xmax:.1f}]",
        f"y=[{ymin:.1f}, {ymax:.1f}]",
        f"z=[{zmin:.1f}, {zmax:.1f}]",
    )
    print("Atlas/root center:", f"({xmid:.1f}, {ymid:.1f}, {zmid:.1f})")

    # ============================
    # CAMERAS (computed from atlas bounds)
    # ============================
    # Internal baseline azimuth for a frontal-like view. This is atlas-agnostic
    # as long as x is left–right and z is anterior–posterior (BrainGlobe
    # convention). Users normally control only CAMERA_ROTATION_DEG /
    # CAMERA_DISTANCE_FACTOR / CAMERA_ELEVATION_DEG above.
    _BASE_FRONTAL_AZIMUTH_DEG = 180.0

    ACTIVE_CAMERA = create_camera(
        (xmin, xmax, ymin, ymax, zmin, zmax),
        distance_factor=CAMERA_DISTANCE_FACTOR,
        base_frontal_azimuth_deg=_BASE_FRONTAL_AZIMUTH_DEG,
        rotation_deg=CAMERA_ROTATION_DEG,
        elevation_deg=CAMERA_ELEVATION_DEG,
    )


# ============================
# PROBE TRACKS
# ============================

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


# ============================
# CUSTOM SEGMENTED REGIONS
# ============================

if regions_dir.exists():
    for obj_path in sorted(regions_dir.glob("*.obj")):
        scene.add(str(obj_path), color=CUSTOM_REGION_COLOR, alpha=CUSTOM_REGION_ALPHA)


if SLICE_MODE not in (None, "none"):
    if SLICE_MODE == "custom":
        # Use a custom plane defined by position and normal in atlas space.
        # Position is computed from normalized coordinates (PLANE_NX/NY/NZ in [0, 1])
        # and the current atlas/root bounds. brainrender.atlas.Atlas.get_plane
        # takes `plane`, `pos`, and `norm`; we pass `norm` so that it doesn't
        # try to look up a named plane.
        if hasattr(scene, "root") and scene.root is not None:
            xmin, xmax, ymin, ymax, zmin, zmax = scene.root.bounds()
            # Map PLANE_DEPTH in [0, 1] to atlas coordinates along the primary
            # axis of CUSTOM_PLANE_NORMAL (x, y, or z), always measured from
            # the edge you are "cutting from" towards the centre.
            xmid = 0.5 * (xmin + xmax)
            ymid = 0.5 * (ymin + ymax)
            zmid = 0.5 * (zmin + zmax)

            nx, ny, nz = CUSTOM_PLANE_NORMAL
            ax = abs(nx)
            ay = abs(ny)
            az = abs(nz)

            if ax >= ay and ax >= az:
                # Frontal-like: move plane along x
                start = xmin if nx >= 0 else xmax
                centre = xmid
                cx = start + PLANE_DEPTH * (centre - start)
                cy = ymid
                cz = zmid
            elif ay >= ax and ay >= az:
                # Horizontal-like: move plane along y
                start = ymin if ny >= 0 else ymax
                centre = ymid
                cx = xmid
                cy = start + PLANE_DEPTH * (centre - start)
                cz = zmid
            else:
                # Sagittal-like: move plane along z
                start = zmin if nz >= 0 else zmax
                centre = zmid
                cx = xmid
                cy = ymid
                cz = start + PLANE_DEPTH * (centre - start)

            plane_pos = (cx, cy, cz)
        else:
            # Fallback: if root is missing, just don't slice
            plane_pos = None

        if plane_pos is not None:
            custom_plane = scene.atlas.get_plane(
                pos=plane_pos,
                norm=CUSTOM_PLANE_NORMAL,
            )
            plane_arg = custom_plane
        else:
            plane_arg = None
    else:
        # Use one of the built‑in plane names: "sagittal", "frontal", "horizontal"
        plane_arg = SLICE_MODE

    if plane_arg is not None:
        scene.slice(
            plane=plane_arg,
            actors=None,
        )


# ============================
# RENDERING
# ============================

# Set axes type
scene.plotter.axes = 9

# Build compact identifiers from key parameters
# Use short, filename-friendly tokens without duplicated words.
parts = [f"sub-{subject_id}"]

parts.append(f"dist-{CAMERA_DISTANCE_FACTOR:.2f}")
parts.append(f"rot-{CAMERA_ROTATION_DEG:.1f}")
parts.append(f"el-{CAMERA_ELEVATION_DEG:.1f}")

if SLICE_MODE and SLICE_MODE not in ("none", None):
    parts.append(f"slice-{SLICE_MODE}")
    if SLICE_MODE == "custom":
        parts.append(f"depth-{PLANE_DEPTH:.2f}")
        parts.append(
            "n-"
            f"{CUSTOM_PLANE_NORMAL[0]:.2f}_"
            f"{CUSTOM_PLANE_NORMAL[1]:.2f}_"
            f"{CUSTOM_PLANE_NORMAL[2]:.2f}"
        )

# Human-readable window title
scene.title = " | ".join(parts)

# File-friendly base name (already using '-' and '_' separators)
filename_base = "_".join(parts)
filename = _sanitize_for_filename(filename_base) + ".png"

scene.render(camera=ACTIVE_CAMERA, interactive=True)

# Save a PNG snapshot of the final view
scene.screenshot(name=filename)