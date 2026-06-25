#!/usr/bin/env python3
"""
Interactive brain atlas viewer.

Edit the SETTINGS dict below, then run::

    python -m bg_viz_pipeline.scripts.interactive_render
"""

from bg_viz_pipeline.lib import render

render.init_brainrender_settings()

try:
    from vedo import settings as vsettings
    vsettings.use_depth_peeling = False
except Exception:
    pass

# =============================================================================
# Settings — same keys as viewer_presets.json (but lower_snake here)
# =============================================================================

SETTINGS = {
    "atlas_name": render.DEFAULT_ATLAS_NAME,
    "mesh_mode": "root",           # "root" or "regions"
    "region_mode": "leaves",       # "leaves" or "all" (when mesh_mode == "regions")
    "root_alpha": render.INTERACTIVE_ROOT_ALPHA,
    "region_alpha": render.INTERACTIVE_REGION_ALPHA,
    "subject_pose": "on_base",     # on_base | on_bulb | on_side
    "camera_distance_factor": 4.0,
    "camera_rotation_deg": -45.0,
    "camera_elevation_deg": -30.0,
    "base_frontal_azimuth_deg": 0.0,
    "slice_mode": "custom",        # none | frontal | horizontal | sagittal | custom
    "plane_depth": 0.35,
    "custom_plane_normal": (0.0, 1.0, 0.0),
    "close_actors": True,
    "slice_cap_color": "salmon",
    "plotter_axes": 9,
    "shader_style": render.INTERACTIVE_SHADER_STYLE,
}


def main():
    render.configure_brainrender(SETTINGS)
    scene = render.create_scene(SETTINGS, title=SETTINGS["atlas_name"])
    render.add_atlas_content(scene, SETTINGS)
    camera = render.apply_view(scene, SETTINGS)
    render.render_scene(scene, camera, interactive=True)
    render.maybe_save_atlas_screenshots(scene, SETTINGS)


if __name__ == "__main__":
    main()
