#!/usr/bin/env python3
from pathlib import Path

import numpy as np
import brainrender
from brainrender import Scene
from brainrender.actors import Points
from camera_helpers import create_camera


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
BRAINREG_DIR = BASE_DIR / "ds_ROI-1_230620_102737_25_25_ch02_chan_2_red_2x4shankNPX"

# Regions to highlight from the atlas
REGIONS_TO_SHOW = [
    "Am-u",
    "M2",
    "PrL",
    "MO",
    "IL",
]

# Visual styling parameters
REGION_ALPHA = 0.3          # main highlighted regions
ROOT_ALPHA = 0.1            # whole-brain outline
ROOT_COLOR = "grey"
CUSTOM_REGION_COLOR = "crimson"
CUSTOM_REGION_ALPHA = 0.4
PROBE_COLOR = "gold"
PROBE_RADIUS = 50

# Camera configuration (atlas-agnostic)
# CAMERA_DISTANCE_FACTOR:
#   - How far the camera sits from the atlas centre, as a multiple of the
#     largest brain extent. Typical range: 1.2–3.0. Larger = further away.
CAMERA_DISTANCE_FACTOR = 2.0

# CAMERA_ROTATION_DEG:
#   - Horizontal rotation around the brain, starting from a computed frontal
#     baseline. Use range [-180, 180]: negative = rotate left, positive = rotate right.
CAMERA_ROTATION_DEG = 45.0

# CAMERA_ELEVATION_DEG:
#   - Vertical tilt (degrees) in this atlas: 0 = level with centre.
#     Negative values (e.g. -10 to -40) look from above, positive from below.
#     Useful range ≈ [-60, 60].
CAMERA_ELEVATION_DEG = -30.0

# Slice mode:
# - None or "none": no slicing
# - "sagittal" / "frontal" / "horizontal": built‑in orthogonal planes
# - "custom": define a plane by:
#     * PLANE_NX / PLANE_NY / PLANE_NZ in [0, 1] (position within atlas bounds)
#     * CUSTOM_PLANE_NORMAL (orientation/direction of the cut)

SLICE_MODE = None

# Normalized position of the slicing plane within the atlas bounds (used when
# SLICE_MODE == "custom"). These are in [0, 1]:
#   0   = min (left / bottom / back)
#   0.5 = center
#   1   = max (right / top / front)
PLANE_NX = 0.5
PLANE_NY = 0.8
PLANE_NZ = 0.5

# Orientation of the custom plane (works for any atlas). Use one of:
#   (1, 0, 0)  -> frontal-like (front/back split)
#   (0, 1, 0)  -> horizontal-like (top/bottom split)
#   (0, 0, 1)  -> sagittal-like (left/right split)
# Flip the sign to invert which side is kept (e.g. (0, -1, 0)).
CUSTOM_PLANE_NORMAL = (0.0, 0.0, 1.0)


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
            cx = xmin + PLANE_NX * (xmax - xmin)
            cy = ymin + PLANE_NY * (ymax - ymin)
            cz = zmin + PLANE_NZ * (zmax - zmin)
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
        parts.append(f"nx-{PLANE_NX:.2f}")
        parts.append(f"ny-{PLANE_NY:.2f}")
        parts.append(f"nz-{PLANE_NZ:.2f}")
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