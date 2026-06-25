from __future__ import annotations

from brainrender import Scene


def bounds_center(
    bounds: tuple[float, float, float, float, float, float],
) -> tuple[float, float, float]:
    """Centre of a vtk-style bounding box; used as the pose rotation pivot."""
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    return (0.5 * (xmin + xmax), 0.5 * (ymin + ymax), 0.5 * (zmin + zmax))


def union_bounds(
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
