#!/usr/bin/env python3
"""
Interactive brain atlas viewer.

Loads an atlas, applies settings from the configuration block below, and
opens an interactive render window. Optional screenshots are saved when a
recognised custom slice normal is used.

Run::

    python -m bg_viz_pipeline.scripts.render_atlas

Pipeline (``main``)::

    create_scene → add_atlas_content → apply_view → render
"""

from __future__ import annotations

from brainrender import settings

from bg_viz_pipeline.lib.pose_helpers import SubjectPose
from bg_viz_pipeline.lib.scene_pipeline import (
    add_atlas_content,
    apply_view,
    configure_brainrender,
    create_scene,
    render_scene,
)
from bg_viz_pipeline.lib.view_config import ViewConfig

# =============================================================================
# Configuration — edit these values (same field names as viewer_presets.json)
# =============================================================================

ATLAS_NAME = "viktors_tweaked_warp_swc_female_rat_25um"

# "root" = whole-brain shell only
# "regions" = atlas regions (no root mesh)
MESH_MODE = "root"
ROOT_ALPHA = 0.8
REGION_ALPHA = 1.0
REGION_MODE = "leaves"
# Region selection when MESH_MODE == "regions" (tree jargon from BrainGlobe):
#   "leaves" — smallest subdivisions only (e.g. MOs, MOp), no parent shells.
#              These tile the brain without overlapping. Usually what you want.
#   "all"    — every named region, parents and children (overlapping meshes).

# --- Camera ---
# Total azimuth = BASE_FRONTAL_AZIMUTH_DEG + CAMERA_ROTATION_DEG
CAMERA_DISTANCE_FACTOR = 4.0
CAMERA_ROTATION_DEG = -45.0
CAMERA_ELEVATION_DEG = -30.0  # along atlas y — see scripts/README.md
BASE_FRONTAL_AZIMUTH_DEG = 0.0

SUBJECT_POSE: SubjectPose = "on_base"

SLICE_MODE = "custom"  # "none", "frontal", "horizontal", "sagittal", "custom"
PLANE_DEPTH = 0.35
CUSTOM_PLANE_NORMAL = (0.0, 1.0, 0.0)
CLOSE_ACTORS = True  # False = open cut (slice outline); True = solid cut face
SLICE_CAP_COLOR = "salmon"  # cut-face colour when CLOSE_ACTORS is True; None = same as mesh

PLOTTER_AXES = 9  # 8 = labelled x/y/z; see scripts/README.md § Atlas coordinates
SHADER_STYLE = "cartoon"

# =============================================================================
# brainrender / vedo defaults (usually leave as-is)
# =============================================================================

settings.LIGHTING = "default"
settings.SHOW_AXES = False
settings.SCREENSHOT_TRANSPARENT_BACKGROUND = False

try:
    from vedo import settings as vsettings

    vsettings.use_depth_peeling = False
except Exception:
    pass


def _view_config() -> ViewConfig:
    """Build ``ViewConfig`` from the module constants above."""
    return ViewConfig(
        atlas_name=ATLAS_NAME,
        mesh_mode=MESH_MODE,
        region_mode=REGION_MODE,
        root_alpha=ROOT_ALPHA,
        region_alpha=REGION_ALPHA,
        subject_pose=SUBJECT_POSE,
        camera_distance_factor=CAMERA_DISTANCE_FACTOR,
        camera_rotation_deg=CAMERA_ROTATION_DEG,
        camera_elevation_deg=CAMERA_ELEVATION_DEG,
        base_frontal_azimuth_deg=BASE_FRONTAL_AZIMUTH_DEG,
        slice_mode=SLICE_MODE,
        plane_depth=PLANE_DEPTH,
        custom_plane_normal=CUSTOM_PLANE_NORMAL,
        close_actors=CLOSE_ACTORS,
        slice_cap_color=SLICE_CAP_COLOR,
        plotter_axes=PLOTTER_AXES,
        shader_style=SHADER_STYLE,
    )


def main() -> None:
    """Build the scene and open the interactive plotter."""
    config = _view_config()
    configure_brainrender(config)

    scene = create_scene(config, title=config.atlas_name)
    add_atlas_content(scene, config)
    camera = apply_view(scene, config)
    render_scene(scene, camera, interactive=True)

    # Screenshot only for these normals; filenames include SLICE_MODE.
    n = config.custom_plane_normal
    frontal = n == (1.0, 0.0, 0.0) or n == (-1.0, 0.0, 0.0)
    sagittal = n == (0.0, 0.0, -1.0) or n == (0.0, 0.0, 1.0)
    horizontal = n == (0.0, 1.0, 0.0) or n == (0.0, -1.0, 0.0)
    if frontal:
        scene.screenshot(
            name=f"atlas_screenshot_{config.slice_mode}_frontal.png",
            scale=2,
        )
    elif sagittal:
        scene.screenshot(
            name=f"atlas_screenshot_{config.slice_mode}_sagittal.png",
            scale=2,
        )
    elif horizontal:
        scene.screenshot(
            name=f"atlas_screenshot_{config.slice_mode}_horizontal.png",
            scale=2,
        )


if __name__ == "__main__":
    main()
