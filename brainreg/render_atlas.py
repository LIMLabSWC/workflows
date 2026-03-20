from brainrender import Scene, settings

from camera_helpers import create_camera
from styles import (
    AXES_MODE,
    REGION_ALPHA,
    REGION_COLOR,
    FORCE_REGION_COLOR,
    ROOT_ALPHA,
    ROOT_COLOR,
    SCREENSHOT_TRANSPARENT_BACKGROUND,
    SHOW_AXES,
    BRAINRENDER_LIGHTING,
    BRAINRENDER_SHADER_STYLE,
)

# Global brainrender look — same knobs as brainreg_viewer / styles.py
settings.LIGHTING = BRAINRENDER_LIGHTING
settings.SHADER_STYLE = BRAINRENDER_SHADER_STYLE
settings.SHOW_AXES = SHOW_AXES
settings.SCREENSHOT_TRANSPARENT_BACKGROUND = SCREENSHOT_TRANSPARENT_BACKGROUND


# ============================
# SIMPLE CONFIG (EDIT HERE)
# ============================

ATLAS_NAME = "swc_female_rat_50um"

# Example regions (same style as in your IPython snippet)
REGIONS_TO_SHOW = ["M2", "PrL", "MO", "IL", "S1-bf", "Am-u"]

# Camera configuration (exactly the same semantics as brainreg_viewer.py)
CAMERA_DISTANCE_FACTOR = 2.0
CAMERA_ROTATION_DEG = -45.0
CAMERA_ELEVATION_DEG = -15.0

# Optional slicing (same logic as brainreg_viewer.py)
SLICE_MODE = "none"  # "none", "frontal", "horizontal", "sagittal", or "custom"
PLANE_DEPTH = 0.5
CUSTOM_PLANE_NORMAL = (0.0, 0.0, 1.0)


def main() -> None:
    """
    Script equivalent of your IPython workflow:
      - create Scene with atlas
      - add chosen regions
      - compute atlas-aware camera
      - optional slicing
      - render with that camera
    """
    # 1. Create scene
    scene = Scene(atlas_name=ATLAS_NAME, title="rat atlas")

    # 2. Add atlas regions (exactly like your IPython line)
    if REGIONS_TO_SHOW:
        if FORCE_REGION_COLOR:
            scene.add_brain_region(*REGIONS_TO_SHOW, alpha=REGION_ALPHA, color=REGION_COLOR)
        else:
            scene.add_brain_region(*REGIONS_TO_SHOW, alpha=REGION_ALPHA)

    # 3. Soften outline
    if hasattr(scene, "root") and scene.root is not None:
        scene.root.c(ROOT_COLOR).alpha(ROOT_ALPHA)

        xmin, xmax, ymin, ymax, zmin, zmax = scene.root.bounds()
        xmid = 0.5 * (xmin + xmax)
        ymid = 0.5 * (ymin + ymax)
        zmid = 0.5 * (zmin + zmax)

        _BASE_FRONTAL_AZIMUTH_DEG = 180.0
        camera = create_camera(
            (xmin, xmax, ymin, ymax, zmin, zmax),
            distance_factor=CAMERA_DISTANCE_FACTOR,
            base_frontal_azimuth_deg=_BASE_FRONTAL_AZIMUTH_DEG,
            rotation_deg=CAMERA_ROTATION_DEG,
            elevation_deg=CAMERA_ELEVATION_DEG,
        )
    else:
        camera = None

    # 4. Optional slicing
    plane_arg = None
    if SLICE_MODE not in (None, "none"):
        if SLICE_MODE == "custom" and hasattr(scene, "root") and scene.root is not None:
            xmin, xmax, ymin, ymax, zmin, zmax = scene.root.bounds()
            xmid = 0.5 * (xmin + xmax)
            ymid = 0.5 * (ymin + ymax)
            zmid = 0.5 * (zmin + zmax)

            nx, ny, nz = CUSTOM_PLANE_NORMAL
            ax, ay, az = abs(nx), abs(ny), abs(nz)

            if ax >= ay and ax >= az:
                start = xmin if nx >= 0 else xmax
                centre = xmid
                cx = start + PLANE_DEPTH * (centre - start)
                cy = ymid
                cz = zmid
            elif ay >= ax and ay >= az:
                start = ymin if ny >= 0 else ymax
                centre = ymid
                cx = xmid
                cy = start + PLANE_DEPTH * (centre - start)
                cz = zmid
            else:
                start = zmin if nz >= 0 else zmax
                centre = zmid
                cx = xmid
                cy = ymid
                cz = start + PLANE_DEPTH * (centre - start)

            plane_pos = (cx, cy, cz)
            custom_plane = scene.atlas.get_plane(
                pos=plane_pos,
                norm=CUSTOM_PLANE_NORMAL,
            )
            plane_arg = custom_plane
        else:
            plane_arg = SLICE_MODE

        if plane_arg is not None:
            scene.slice(plane=plane_arg, actors=None)

    # 5. Axes + render
    scene.plotter.axes = AXES_MODE
    if camera is not None:
        scene.render(camera=camera, interactive=True)
    else:
        scene.render(interactive=True)


if __name__ == "__main__":
    main()

