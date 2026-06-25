from __future__ import annotations

import numpy as np
from brainrender import Scene
from vedo import colors as vedo_colors

from bg_viz_pipeline.lib.bounds_helpers import union_bounds
from bg_viz_pipeline.lib.pose_helpers import SubjectPose, rotate_vector


def atlas_plane_normal(scene: Scene, slice_mode: str) -> tuple[float, float, float]:
    """Look up a named BrainGlobe slice plane (frontal / horizontal / sagittal)."""
    normals = scene.atlas.space.plane_normals
    if slice_mode not in normals:
        raise ValueError(
            f"SLICE_MODE must be 'custom' or one of {sorted(normals)}, not {slice_mode!r}"
        )
    return tuple(normals[slice_mode])


def posed_slice_normal(
    scene: Scene,
    pose: SubjectPose,
    slice_mode: str,
    custom_plane_normal: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Slice normal in atlas space, rotated to match the current specimen pose."""
    if slice_mode == "custom":
        base = custom_plane_normal
    else:
        base = atlas_plane_normal(scene, slice_mode)
    return rotate_vector(base, pose)


def plane_center_from_depth(
    bounds: tuple[float, float, float, float, float, float],
    plane_depth: float,
    normal: tuple[float, float, float],
) -> tuple[float, float, float]:
    """
    Interpolate a plane origin along ``normal``.

    ``plane_depth`` is 0 at the mesh edge and 1 at the centre, along the
    dominant axis of ``normal``.
    """
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
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

    return (cx, cy, cz)


def build_plane(
    scene: Scene,
    plane_depth: float,
    normal: tuple[float, float, float],
):
    """Build a vedo slice plane from scene bounds and a normal direction."""
    ub = union_bounds(scene)
    if ub is None:
        return None

    center = plane_center_from_depth(ub, plane_depth, normal)
    return scene.atlas.get_plane(pos=center, norm=normal)


def cap_mesh_with_color(mesh, cap_color: str) -> None:
    """
    Close an open cut mesh and colour only the new cap triangles.

    Used when ``close_actors`` and ``slice_cap_color`` are both set.
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


def refresh_silhouette(scene: Scene, actor) -> None:
    """Re-draw cartoon silhouette after a mesh has been modified in place."""
    if actor.silhouette is not None:
        scene.plotter.remove(actor.silhouette.mesh)
        scene.plotter.add(actor.make_silhouette().mesh)


def apply_slice(
    scene: Scene,
    pose: SubjectPose,
    slice_mode: str | None,
    plane_depth: float,
    custom_plane_normal: tuple[float, float, float],
    *,
    close_actors: bool,
    slice_cap_color: str | None,
) -> None:
    """
    Cut scene actors with a plane in the posed coordinate frame.

    When ``close_actors`` is True and ``slice_cap_color`` is set, the cut
    face is capped and coloured. Otherwise ``scene.slice`` is used as-is.
    """
    if slice_mode in (None, "none"):
        return

    normal = posed_slice_normal(scene, pose, slice_mode, custom_plane_normal)
    plane = build_plane(scene, plane_depth, normal)
    if plane is None:
        return

    if close_actors and slice_cap_color:
        for actor in scene.clean_actors.copy():
            actor._mesh = actor._mesh.cut_with_plane(
                origin=plane.center,
                normal=plane.normal,
            )
            cap_mesh_with_color(actor._mesh, slice_cap_color)
            refresh_silhouette(scene, actor)
    else:
        scene.slice(plane=plane, actors=None, close_actors=close_actors)
