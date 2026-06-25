#!/usr/bin/env python3
"""
Interactive brain atlas viewer.

Loads an atlas, applies settings from the configuration block below, and
opens an interactive render window. Optional screenshots are saved when a
recognised custom slice normal is used.

Run::

    python -m bg_viz_pipeline.scripts.interactive_render

Pipeline (``main``)::

    create_scene → add_atlas_content → apply_view → render
"""

from __future__ import annotations

from bg_viz_pipeline.lib.output_helpers import maybe_save_atlas_screenshots
from bg_viz_pipeline.lib.pose_helpers import SubjectPose
from bg_viz_pipeline.lib.scene_pipeline import (
    add_atlas_content,
    apply_view,
    configure_brainrender,
    create_scene,
    init_brainrender_settings,
    render_scene,
)
from bg_viz_pipeline.lib.styles import (
    DEFAULT_ATLAS_NAME,
    INTERACTIVE_REGION_ALPHA,
    INTERACTIVE_ROOT_ALPHA,
    INTERACTIVE_SHADER_STYLE,
)
from bg_viz_pipeline.lib.view_config import ViewConfig

# =============================================================================
# Configuration — edit these values (same field names as viewer_presets.json)
# =============================================================================

ATLAS_NAME = DEFAULT_ATLAS_NAME

# "root" = whole-brain shell only
# "regions" = atlas regions (no root mesh)
MESH_MODE = "root"
ROOT_ALPHA = INTERACTIVE_ROOT_ALPHA
REGION_ALPHA = INTERACTIVE_REGION_ALPHA
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
SHADER_STYLE = INTERACTIVE_SHADER_STYLE

init_brainrender_settings()

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
    maybe_save_atlas_screenshots(scene, config)


if __name__ == "__main__":
    main()
