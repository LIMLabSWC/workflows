#!/usr/bin/env python3
"""
Interactive atlas viewer for exploring slice planes and camera angles.

Edit the configuration block below, then run::

    python -m bg_viz_pipeline.scripts.render_atlas

**Mesh mode** — set ``MESH_MODE`` to ``"root"`` (whole-brain shell) or
``"regions"`` (leaf/all atlas regions, no root).

**Slice** — ``CLOSE_ACTORS`` chooses open cut (visible outline) vs solid cap.
When capped, ``SLICE_CAP_COLOR`` colours only the cut face.
"""

from __future__ import annotations

import numpy as np
from brainrender import Scene, settings
from vedo import colors as vedo_colors

from bg_viz_pipeline.lib.camera_helpers import create_camera

# =============================================================================
# Configuration — edit these values
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

CAMERA_DISTANCE_FACTOR = 4.0
CAMERA_ROTATION_DEG = 135.0
CAMERA_ELEVATION_DEG = -30.0

SLICE_MODE = "custom"  # "none", "frontal", "horizontal", "sagittal", "custom"
PLANE_DEPTH = 0.27
CUSTOM_PLANE_NORMAL = (-1.0, 0.0, 0.0)
CLOSE_ACTORS = True  # False = open cut (slice outline); True = solid cut face
SLICE_CAP_COLOR = "salmon"  # cut-face colour when CLOSE_ACTORS is True; None = same as mesh

PLOTTER_AXES = 0

# =============================================================================
# brainrender / vedo defaults (usually leave as-is)
# =============================================================================

settings.LIGHTING = "default"
settings.SHADER_STYLE = "cartoon"
settings.SHOW_AXES = False
settings.SCREENSHOT_TRANSPARENT_BACKGROUND = False

try:
    from vedo import settings as vsettings

    vsettings.use_depth_peeling = False
except Exception:
    pass

_BASE_FRONTAL_AZIMUTH_DEG = 180.0
_REGION_BATCH_SIZE = 256


def _all_region_acronyms(scene: Scene) -> list[str]:
    """Return every atlas region acronym except ``root``."""
    acr = scene.atlas.lookup_df["acronym"].astype(str).tolist()
    return [a for a in acr if a != "root"]


def _leaf_region_acronyms(scene: Scene) -> list[str]:
    """Smallest atlas regions: terminal nodes in the hierarchy (tree ``.leaves()``)."""
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
    """Pick the region list for ``REGION_MODE`` (``leaves`` or ``all``)."""
    if mode == "all":
        return _all_region_acronyms(scene)
    if mode == "leaves":
        return _leaf_region_acronyms(scene)
    raise ValueError(f"REGION_MODE must be 'leaves' or 'all', not {mode!r}")


def _add_meshes(scene: Scene) -> None:
    """
    Add atlas geometry according to ``MESH_MODE``.

    ``root`` — keep the whole-brain shell (``scene.root``).
    ``regions`` — add atlas regions in batches; root mesh is hidden.
    """
    if MESH_MODE == "root":
        scene.root.alpha(ROOT_ALPHA)
        return

    if MESH_MODE == "regions":
        regions = _region_acronyms(scene, REGION_MODE)
        for i in range(0, len(regions), _REGION_BATCH_SIZE):
            batch = regions[i : i + _REGION_BATCH_SIZE]
            scene.add_brain_region(*batch, alpha=REGION_ALPHA)
        return

    raise ValueError(f"MESH_MODE must be 'root' or 'regions', not {MESH_MODE!r}")


def _union_bounds(
    scene: Scene,
) -> tuple[float, float, float, float, float, float] | None:
    """Axis-aligned bounding box spanning all actors currently in the scene."""
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


def _custom_plane(
    scene: Scene,
    plane_depth: float,
    normal: tuple[float, float, float],
):
    """
    Build a vedo plane for ``SLICE_MODE == "custom"``.

    ``plane_depth`` is 0 at the mesh edge and 1 at the centre, along the
    axis of ``normal``.
    """
    ub = _union_bounds(scene)
    if ub is None:
        return None

    xmin, xmax, ymin, ymax, zmin, zmax = ub
    xmid = 0.5 * (xmin + xmax)
    ymid = 0.5 * (ymin + ymax)
    zmid = 0.5 * (zmin + zmax)
    nx, ny, nz = normal
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

    return scene.atlas.get_plane(pos=(cx, cy, cz), norm=normal)


def _cap_mesh_with_color(mesh, cap_color: str) -> None:
    """
    Close an open cut mesh and colour only the new cap triangles.

    Used when ``CLOSE_ACTORS`` and ``SLICE_CAP_COLOR`` are both set.
    """
    n_before = mesh.ncells
    mesh.cap()
    if n_before >= mesh.ncells:
        return

    cap_rgb = (np.array(vedo_colors.get_color(cap_color)) * 255).astype(np.uint8)
    base_rgb = (np.array(vedo_colors.get_color(mesh.color())) * 255).astype(np.uint8)
    cols = np.zeros((mesh.ncells, 4), dtype=np.uint8)
    cols[:, :3] = base_rgb
    cols[:, 3] = 255
    cols[n_before:, :3] = cap_rgb
    mesh.cellcolors = cols


def _refresh_silhouette(scene: Scene, actor) -> None:
    """Re-draw cartoon silhouette after a mesh has been modified in place."""
    if actor.silhouette is not None:
        scene.plotter.remove(actor.silhouette.mesh)
        scene.plotter.add(actor.make_silhouette().mesh)


def _apply_slice(
    scene: Scene,
    slice_mode: str | None,
    plane_depth: float,
    custom_plane_normal: tuple[float, float, float],
) -> None:
    """
    Cut scene actors with a plane.

    Plane presets: ``frontal``, ``horizontal``, ``sagittal``, or ``custom``
    (uses ``PLANE_DEPTH`` and ``CUSTOM_PLANE_NORMAL``).

    When ``CLOSE_ACTORS`` is True and ``SLICE_CAP_COLOR`` is set, the cut
    face is capped and coloured. Otherwise ``scene.slice`` is used as-is.
    """
    if slice_mode in (None, "none"):
        return

    if slice_mode == "custom":
        plane = _custom_plane(scene, plane_depth, custom_plane_normal)
    else:
        plane = slice_mode

    if plane is None:
        return

    if CLOSE_ACTORS and SLICE_CAP_COLOR:
        for actor in scene.clean_actors.copy():
            actor._mesh = actor._mesh.cut_with_plane(
                origin=plane.center,
                normal=plane.normal,
            )
            _cap_mesh_with_color(actor._mesh, SLICE_CAP_COLOR)
            _refresh_silhouette(scene, actor)
    else:
        scene.slice(plane=plane, actors=None, close_actors=CLOSE_ACTORS)


def _make_camera(scene: Scene):
    """Camera framing all current actors, or ``None`` if the scene is empty."""
    ub = _union_bounds(scene)
    if ub is None:
        return None
    xmin, xmax, ymin, ymax, zmin, zmax = ub
    return create_camera(
        (xmin, xmax, ymin, ymax, zmin, zmax),
        distance_factor=CAMERA_DISTANCE_FACTOR,
        base_frontal_azimuth_deg=_BASE_FRONTAL_AZIMUTH_DEG,
        rotation_deg=CAMERA_ROTATION_DEG,
        elevation_deg=CAMERA_ELEVATION_DEG,
    )


def main() -> None:
    """Build the scene, apply slice/camera settings, render interactively."""
    show_root = MESH_MODE == "root"
    scene = Scene(
        atlas_name=ATLAS_NAME,
        title=ATLAS_NAME,
        root=show_root,
        check_latest=False,
    )

    _add_meshes(scene)

    camera = _make_camera(scene)
    _apply_slice(scene, SLICE_MODE, PLANE_DEPTH, CUSTOM_PLANE_NORMAL)
    scene.plotter.axes = PLOTTER_AXES

    if camera is not None:
        scene.render(camera=camera, interactive=True)
    else:
        scene.render(interactive=True)

    # Screenshot only for these normals; filenames include SLICE_MODE.
    frontal = (
        CUSTOM_PLANE_NORMAL == (1.0, 0.0, 0.0)
        or CUSTOM_PLANE_NORMAL == (-1.0, 0.0, 0.0)
    )
    sagittal = (
        CUSTOM_PLANE_NORMAL == (0.0, 0.0, -1.0)
        or CUSTOM_PLANE_NORMAL == (0.0, 0.0, 1.0)
    )
    horizontal = (
        CUSTOM_PLANE_NORMAL == (0.0, 1.0, 0.0)
        or CUSTOM_PLANE_NORMAL == (0.0, -1.0, 0.0)
    )
    if frontal:
        scene.screenshot(
            name=f"atlas_screenshot_{SLICE_MODE}_frontal.png",
            scale=2,
        )
    elif sagittal:
        scene.screenshot(
            name=f"atlas_screenshot_{SLICE_MODE}_sagittal.png",
            scale=2,
        )
    elif horizontal:
        scene.screenshot(
            name=f"atlas_screenshot_{SLICE_MODE}_horizontal.png",
            scale=2,
        )


if __name__ == "__main__":
    main()
