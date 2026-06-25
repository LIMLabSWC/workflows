from __future__ import annotations

from brainrender import Scene

_REGION_BATCH_SIZE = 256


def all_region_acronyms(scene: Scene) -> list[str]:
    """Return every atlas region acronym except ``root``."""
    acr = scene.atlas.lookup_df["acronym"].astype(str).tolist()
    return [a for a in acr if a != "root"]


def leaf_region_acronyms(scene: Scene) -> list[str]:
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


def region_acronyms(scene: Scene, mode: str) -> list[str]:
    """Pick the region list for ``region_mode`` (``leaves`` or ``all``)."""
    if mode == "all":
        return all_region_acronyms(scene)
    if mode == "leaves":
        return leaf_region_acronyms(scene)
    raise ValueError(f"REGION_MODE must be 'leaves' or 'all', not {mode!r}")


def add_atlas_geometry(
    scene: Scene,
    *,
    mesh_mode: str,
    region_mode: str,
    root_alpha: float,
    region_alpha: float,
    batch_size: int = _REGION_BATCH_SIZE,
) -> None:
    """
    Add atlas geometry according to ``mesh_mode``.

    ``root`` — keep the whole-brain shell (``scene.root``).
    ``regions`` — add atlas regions in batches; root mesh is hidden.
    """
    if mesh_mode == "root":
        scene.root.alpha(root_alpha)
        return

    if mesh_mode == "regions":
        regions = region_acronyms(scene, region_mode)
        for i in range(0, len(regions), batch_size):
            batch = regions[i : i + batch_size]
            scene.add_brain_region(*batch, alpha=region_alpha)
        return

    raise ValueError(f"MESH_MODE must be 'root' or 'regions', not {mesh_mode!r}")
