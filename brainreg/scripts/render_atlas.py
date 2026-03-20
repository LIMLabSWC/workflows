#!/usr/bin/env python3
"""
Interactive full-atlas view (default: leaf regions only, no root mesh).

Uses the same brainrender settings as `brainreg_viewer.py`. Custom slice
plane math matches viewer JSON presets, but cuts use ``close_actors=True``
(filled caps) unlike the viewer PNG path. Screenshots run only for the
three ``CUSTOM_PLANE_NORMAL`` values at the bottom of ``main()`` (see there).
"""

from __future__ import annotations

from brainrender import Scene, settings

from brainreg.lib.camera_helpers import create_camera

settings.LIGHTING = "default"
settings.SHADER_STYLE = "plastic"
settings.SHOW_AXES = False
settings.SCREENSHOT_TRANSPARENT_BACKGROUND = False

try:
    from vedo import settings as vsettings

    vsettings.use_depth_peeling = False
except Exception:
    pass

ATLAS_NAME = "swc_female_rat_50um"
REGION_ALPHA = 1.0
REGION_MODE = "leaves"  # "leaves" | "all"

CAMERA_DISTANCE_FACTOR = 2.0
CAMERA_ROTATION_DEG = -45.0
CAMERA_ELEVATION_DEG = -30.0
_BASE_FRONTAL_AZIMUTH_DEG = 180.0

SLICE_MODE = "custom"  # "none", "frontal", "horizontal", "sagittal", "custom"
PLANE_DEPTH = 0.5
CUSTOM_PLANE_NORMAL = (0.1, 0.0, 0.0)

_REGION_BATCH_SIZE = 256
# Same as brainreg_viewer.render_one (wire bounding box, not cube-axis ticks).
PLOTTER_AXES = 9


def _all_region_acronyms(scene: Scene) -> list[str]:
    acr = scene.atlas.lookup_df["acronym"].astype(str).tolist()
    return [a for a in acr if a != "root"]


def _leaf_region_acronyms(scene: Scene) -> list[str]:
    atlas = scene.atlas
    out: list[str] = []
    for node in atlas.structures.tree.leaves():
        sid = node.identifier
        try:
            acr = atlas.structures[sid]["acronym"]
        except KeyError:
            continue
        if acr == "root":
            continue
        out.append(acr)
    return out


def _region_acronyms(scene: Scene, mode: str) -> list[str]:
    if mode == "all":
        return _all_region_acronyms(scene)
    if mode == "leaves":
        return _leaf_region_acronyms(scene)
    raise ValueError(f"REGION_MODE must be 'leaves' or 'all', not {mode!r}")


def _union_bounds(
    scene: Scene,
) -> tuple[float, float, float, float, float, float] | None:
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    for actor in scene.clean_actors:
        mesh = getattr(actor, "_mesh", None) or actor.mesh
        try:
            b = mesh.bounds()
        except Exception:
            continue
        if b is None or len(b) < 6:
            continue
        xmin, xmax, ymin, ymax, zmin, zmax = (float(b[i]) for i in range(6))
        xs += (xmin, xmax)
        ys += (ymin, ymax)
        zs += (zmin, zmax)
    if not xs:
        return None
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def _apply_slice(
    scene: Scene,
    slice_mode: str | None,
    plane_depth: float,
    custom_plane_normal: tuple[float, float, float],
) -> None:
    if slice_mode in (None, "none"):
        return

    if slice_mode == "custom":
        plane_arg = None
        ub = _union_bounds(scene)
        if ub is not None:
            xmin, xmax, ymin, ymax, zmin, zmax = ub
            xmid = 0.5 * (xmin + xmax)
            ymid = 0.5 * (ymin + ymax)
            zmid = 0.5 * (zmin + zmax)
            nx, ny, nz = custom_plane_normal
            ax, ay, az = abs(nx), abs(ny), abs(nz)

            if ax >= ay and ax >= az:
                start = xmin if nx >= 0 else xmax
                cx = start + plane_depth * (xmid - start)
                cy, cz = ymid, zmid
            elif ay >= ax and ay >= az:
                start = ymin if ny >= 0 else ymax
                cx, cy, cz = xmid, start + plane_depth * (ymid - start), zmid
            else:
                start = zmin if nz >= 0 else zmax
                cx, cy, cz = xmid, ymid, start + plane_depth * (zmid - start)

            plane_arg = scene.atlas.get_plane(
                pos=(cx, cy, cz),
                norm=custom_plane_normal,
            )
    else:
        plane_arg = slice_mode

    if plane_arg is not None:
        # Caps cut meshes (brainreg_viewer omits this — open cuts). Solid-looking slice faces.
        scene.slice(plane=plane_arg, actors=None, close_actors=True)


def main() -> None:
    scene = Scene(atlas_name=ATLAS_NAME, title=ATLAS_NAME, root=False)

    regions = _region_acronyms(scene, REGION_MODE)
    for i in range(0, len(regions), _REGION_BATCH_SIZE):
        scene.add_brain_region(*regions[i : i + _REGION_BATCH_SIZE], alpha=REGION_ALPHA)

    ub = _union_bounds(scene)
    if ub is not None:
        xmin, xmax, ymin, ymax, zmin, zmax = ub
        camera = create_camera(
            (xmin, xmax, ymin, ymax, zmin, zmax),
            distance_factor=CAMERA_DISTANCE_FACTOR,
            base_frontal_azimuth_deg=_BASE_FRONTAL_AZIMUTH_DEG,
            rotation_deg=CAMERA_ROTATION_DEG,
            elevation_deg=CAMERA_ELEVATION_DEG,
        )
    else:
        camera = None

    _apply_slice(scene, SLICE_MODE, PLANE_DEPTH, CUSTOM_PLANE_NORMAL)
    scene.plotter.axes = PLOTTER_AXES

    if camera is not None:
        scene.render(camera=camera, interactive=True)
    else:
        scene.render(interactive=True)

    # Screenshot only for these normals (otherwise skip); filenames include SLICE_MODE.
    if CUSTOM_PLANE_NORMAL == (0.1, 0.0, 0.0):
        scene.screenshot(name=f"atlas_screenshot_{SLICE_MODE}_frontal.png", scale=2)
    elif CUSTOM_PLANE_NORMAL == (0.0, 0.0, -1.0):
        scene.screenshot(name=f"atlas_screenshot_{SLICE_MODE}_sagittal.png", scale=2)
    elif CUSTOM_PLANE_NORMAL == (0.0, 1.0, 0.0):
        scene.screenshot(name=f"atlas_screenshot_{SLICE_MODE}_horizontal.png", scale=2)


if __name__ == "__main__":
    main()

