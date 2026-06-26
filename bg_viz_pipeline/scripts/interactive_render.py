#!/usr/bin/env python3
"""
Interactive brain atlas viewer.

Edit the SETTINGS dict below, then run::

    python -m bg_viz_pipeline.scripts.interactive_render
"""

from bg_viz_pipeline.lib import core

core.init_brainrender_settings()

try:
    from vedo import settings as vsettings
    vsettings.use_depth_peeling = False
except Exception:
    pass

# =============================================================================
# Settings — same keys as viewer_presets.json (but lower_snake here)
# =============================================================================

SETTINGS = {
    "atlas_name": core.DEFAULT_ATLAS_NAME,
    "mesh_mode": "root",           # "root" or "regions"
    "region_mode": "leaves",       # "leaves" or "all" (when mesh_mode == "regions")
    "root_alpha": core.INTERACTIVE_ROOT_ALPHA,
    "region_alpha": core.INTERACTIVE_REGION_ALPHA,
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
    "plotter_axes": 9,             # 0 = off; 8 or 9 = labelled axes (see scripts/README.md)
    "shader_style": core.INTERACTIVE_SHADER_STYLE,
    "save_screenshot": True,      # on close: save PNG (filename from SETTINGS below)
    # "screenshot_path": "my_view.png",  # optional; default: batch-style atlas_*.png
}


def main():
    core.configure_brainrender(SETTINGS)
    scene = core.create_scene(SETTINGS, title=SETTINGS["atlas_name"])
    core.add_atlas_content(scene, SETTINGS)
    camera = core.apply_view(scene, SETTINGS)
    core.render_scene(scene, camera, interactive=True)
    if SETTINGS.get("save_screenshot"):
        path = SETTINGS.get("screenshot_path") or core.interactive_screenshot_filename(SETTINGS)
        core.save_screenshot(scene, path)
        print(f"Saved {path}")
        print(
            "Filename encodes SETTINGS at launch (camera + slice). "
            "The PNG shows the view when you closed the window — if you orbited "
            "or zoomed, the image may not match dist/rot/el in the name."
        )


if __name__ == "__main__":
    main()
