"""
All shared 3D rendering logic for interactive_render and batch_render.

Settings are plain dicts (no dataclass). Keys are lower_snake, e.g.
``config["camera_rotation_deg"]``. JSON presets use UPPER_SNAKE; use
``settings_from_preset()`` to convert.
"""

import math
from pathlib import Path

import numpy as np
from brainrender import Scene, settings
from brainrender.actors import Points
from vedo import colors as vedo_colors

# -----------------------------------------------------------------------------
# Constants — atlas name, colours, batch vs interactive defaults
# -----------------------------------------------------------------------------

DEFAULT_ATLAS_NAME = "viktors_tweaked_warp_swc_female_rat_25um"
DEFAULT_BATCH_BASE_FRONTAL_AZIMUTH_DEG = 180.0

BATCH_REGION_ALPHA = 0.2
BATCH_ROOT_ALPHA = 0.2
BATCH_SHADER_STYLE = "plastic"

INTERACTIVE_ROOT_ALPHA = 0.8
INTERACTIVE_REGION_ALPHA = 1.0
INTERACTIVE_SHADER_STYLE = "cartoon"

ROOT_COLOR = "grey"
CUSTOM_REGION_COLOR = "orangered"
CUSTOM_REGION_ALPHA = 0.4
PROBE_COLOR = "chartreuse"
PROBE_RADIUS = 50
CELLS_COLOR = "palegoldenrod"
CELLS_RADIUS = 45

# Specimen pose: rotate mesh geometry (not the camera)
POSE_ROTATIONS_DEG = {
    "on_base": (0.0, 0.0, 0.0),
    "on_bulb": (0.0, 0.0, -90.0),
    "on_side": (90.0, 0.0, 0.0),
}

_REGION_BATCH_SIZE = 256


# -----------------------------------------------------------------------------
# Settings dicts — bridge SETTINGS / JSON presets to render code
# -----------------------------------------------------------------------------


def settings_from_preset(preset, atlas_name=DEFAULT_ATLAS_NAME):
    """Build a settings dict from one viewer_presets.json entry."""
    if "REGIONS_TO_SHOW" not in preset:
        raise KeyError("preset must include REGIONS_TO_SHOW")
    if "BRAINREG_SUBDIR" not in preset:
        raise KeyError("preset must include BRAINREG_SUBDIR")

    close_actors = bool(preset.get("CLOSE_ACTORS", False))
    if "SLICE_CAP_COLOR" in preset:
        cap = preset["SLICE_CAP_COLOR"]
        slice_cap_color = None if cap is None else str(cap)
    elif close_actors:
        slice_cap_color = "salmon"
    else:
        slice_cap_color = None

    normal = preset.get("CUSTOM_PLANE_NORMAL", (0.0, 0.0, 1.0))
    if isinstance(normal, (list, tuple)) and len(normal) == 3:
        normal = (float(normal[0]), float(normal[1]), float(normal[2]))
    else:
        raise ValueError(f"Expected [x, y, z], got {normal!r}")

    return {
        "atlas_name": str(preset.get("ATLAS_NAME", atlas_name)),
        "mesh_mode": preset.get("MESH_MODE", "regions"),
        "regions_to_show": list(preset["REGIONS_TO_SHOW"]),
        "region_mode": preset.get("REGION_MODE", "leaves"),
        "show_root": bool(preset.get("SHOW_ROOT", True)),
        "root_alpha": float(preset.get("ROOT_ALPHA", BATCH_ROOT_ALPHA)),
        "region_alpha": float(preset.get("REGION_ALPHA", BATCH_REGION_ALPHA)),
        "subject_pose": preset.get("SUBJECT_POSE", "on_base"),
        "camera_distance_factor": float(preset["CAMERA_DISTANCE_FACTOR"]),
        "camera_rotation_deg": float(preset["CAMERA_ROTATION_DEG"]),
        "camera_elevation_deg": float(preset["CAMERA_ELEVATION_DEG"]),
        "base_frontal_azimuth_deg": float(
            preset.get("BASE_FRONTAL_AZIMUTH_DEG", DEFAULT_BATCH_BASE_FRONTAL_AZIMUTH_DEG)
        ),
        "slice_mode": preset.get("SLICE_MODE", "none"),
        "plane_depth": float(preset.get("PLANE_DEPTH", 0.0)),
        "custom_plane_normal": normal,
        "close_actors": close_actors,
        "slice_cap_color": slice_cap_color,
        "plotter_axes": int(preset.get("PLOTTER_AXES", 0)),
        "shader_style": preset.get("SHADER_STYLE", BATCH_SHADER_STYLE),
        "brainreg_subdir": str(preset["BRAINREG_SUBDIR"]),
        "max_points": int(preset.get("MAX_POINTS", 5000)),
    }


# -----------------------------------------------------------------------------
# Camera — spherical orbit around brain centre
# -----------------------------------------------------------------------------


def _center_and_extent(bounds):
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    cx = 0.5 * (xmin + xmax)
    cy = 0.5 * (ymin + ymax)
    cz = 0.5 * (zmin + zmax)
    max_extent = max(xmax - xmin, ymax - ymin, zmax - zmin)
    return (cx, cy, cz), max_extent


def create_camera(bounds, distance_factor, base_frontal_azimuth_deg, rotation_deg, elevation_deg):
    """Build brainrender camera dict. Total azimuth = base + rotation."""
    center, max_extent = _center_and_extent(bounds)
    cx, cy, cz = center
    distance = distance_factor * max_extent
    azimuth = base_frontal_azimuth_deg + rotation_deg
    az = math.radians(azimuth)
    el = math.radians(elevation_deg)
    dx = math.cos(el) * math.cos(az)
    dy = math.sin(el)
    dz = math.cos(el) * math.sin(az)
    pos = (cx + distance * dx, cy + distance * dy, cz + distance * dz)
    return dict(
        pos=pos,
        focal_point=center,
        viewup=(0.0, -1.0, 0.0),
        roll=0.0,
        distance=distance,
        clipping_range=(0.1 * distance, 3.0 * distance),
    )


def make_camera(config, bounds):
    return create_camera(
        bounds,
        config["camera_distance_factor"],
        config["base_frontal_azimuth_deg"],
        config["camera_rotation_deg"],
        config["camera_elevation_deg"],
    )


# -----------------------------------------------------------------------------
# Bounds
# -----------------------------------------------------------------------------


def bounds_center(bounds):
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    return (0.5 * (xmin + xmax), 0.5 * (ymin + ymax), 0.5 * (zmin + zmax))


def union_bounds(scene):
    xs, ys, zs = [], [], []
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


# -----------------------------------------------------------------------------
# Pose — rotate meshes and slice normals
# -----------------------------------------------------------------------------


def _rotation_matrix_axis(axis, angle_deg):
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    if n == 0:
        return np.eye(3)
    x, y, z = x / n, y / n, z / n
    th = math.radians(angle_deg)
    c, s = math.cos(th), math.sin(th)
    t = 1 - c
    return np.array(
        [
            [t * x * x + c, t * x * y - s * z, t * x * z + s * y],
            [t * x * y + s * z, t * y * y + c, t * y * z - s * x],
            [t * x * z - s * y, t * y * z + s * x, t * z * z + c],
        ]
    )


def _pose_rotation_matrix(pose):
    rx, ry, rz = POSE_ROTATIONS_DEG[pose]
    return (
        _rotation_matrix_axis((0.0, 0.0, 1.0), rz)
        @ _rotation_matrix_axis((0.0, 1.0, 0.0), ry)
        @ _rotation_matrix_axis((1.0, 0.0, 0.0), rx)
    )


def rotate_vector(vector, pose):
    v = _pose_rotation_matrix(pose) @ np.asarray(vector, dtype=float)
    return (float(v[0]), float(v[1]), float(v[2]))


def _rotate_mesh_about_center(mesh, center, pose):
    if pose == "on_base":
        return
    r = _pose_rotation_matrix(pose)
    c = np.asarray(center, dtype=float)
    mesh.points = (np.asarray(mesh.points, dtype=float) - c) @ r.T + c
    mesh.compute_normals()


def apply_subject_pose(scene, pose, center):
    for actor in scene.clean_actors:
        mesh = getattr(actor, "_mesh", None) or actor.mesh
        _rotate_mesh_about_center(mesh, center, pose)
        if actor.silhouette is not None:
            _rotate_mesh_about_center(actor.silhouette.mesh, center, pose)


# -----------------------------------------------------------------------------
# Atlas meshes
# -----------------------------------------------------------------------------


def _leaf_region_acronyms(scene):
    out = []
    for node in scene.atlas.structures.tree.leaves():
        try:
            acr = scene.atlas.structures[node.identifier]["acronym"]
        except KeyError:
            continue
        if acr != "root":
            out.append(acr)
    return out


def _all_region_acronyms(scene):
    acr = scene.atlas.lookup_df["acronym"].astype(str).tolist()
    return [a for a in acr if a != "root"]


def _add_atlas_geometry(scene, mesh_mode, region_mode, root_alpha, region_alpha):
    if mesh_mode == "root":
        scene.root.alpha(root_alpha)
        return
    if mesh_mode == "regions":
        regions = _all_region_acronyms(scene) if region_mode == "all" else _leaf_region_acronyms(scene)
        for i in range(0, len(regions), _REGION_BATCH_SIZE):
            scene.add_brain_region(*regions[i : i + _REGION_BATCH_SIZE], alpha=region_alpha)
        return
    raise ValueError(f"MESH_MODE must be 'root' or 'regions', not {mesh_mode!r}")


# -----------------------------------------------------------------------------
# Slice
# -----------------------------------------------------------------------------


def _atlas_plane_normal(scene, slice_mode):
    normals = scene.atlas.space.plane_normals
    if slice_mode not in normals:
        raise ValueError(f"bad SLICE_MODE: {slice_mode!r}")
    return tuple(normals[slice_mode])


def _posed_slice_normal(scene, pose, slice_mode, custom_plane_normal):
    base = custom_plane_normal if slice_mode == "custom" else _atlas_plane_normal(scene, slice_mode)
    return rotate_vector(base, pose)


def _plane_center_from_depth(bounds, plane_depth, normal):
    xmin, xmax, ymin, ymax, zmin, zmax = bounds
    xmid, ymid, zmid = bounds_center(bounds)
    nx, ny, nz = normal
    ax, ay, az = abs(nx), abs(ny), abs(nz)
    if ax >= ay and ax >= az:
        start = xmin if nx >= 0 else xmax
        return (start + plane_depth * (xmid - start), ymid, zmid)
    if ay >= ax and ay >= az:
        start = ymin if ny >= 0 else ymax
        return (xmid, start + plane_depth * (ymid - start), zmid)
    start = zmin if nz >= 0 else zmax
    return (xmid, ymid, start + plane_depth * (zmid - start))


def _cap_mesh_with_color(mesh, cap_color):
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


def apply_slice(scene, config):
    slice_mode = config["slice_mode"]
    if slice_mode in (None, "none"):
        return

    normal = _posed_slice_normal(
        scene, config["subject_pose"], slice_mode, config["custom_plane_normal"]
    )
    ub = union_bounds(scene)
    if ub is None:
        return
    center = _plane_center_from_depth(ub, config["plane_depth"], normal)
    plane = scene.atlas.get_plane(pos=center, norm=normal)

    if config["close_actors"] and config["slice_cap_color"]:
        for actor in scene.clean_actors.copy():
            actor._mesh = actor._mesh.cut_with_plane(origin=plane.center, normal=plane.normal)
            _cap_mesh_with_color(actor._mesh, config["slice_cap_color"])
            if actor.silhouette is not None:
                scene.plotter.remove(actor.silhouette.mesh)
                scene.plotter.add(actor.make_silhouette().mesh)
    else:
        scene.slice(plane=plane, actors=None, close_actors=config["close_actors"])


# -----------------------------------------------------------------------------
# Scene pipeline — used by interactive_render and batch_render
# -----------------------------------------------------------------------------


def init_brainrender_settings():
    settings.LIGHTING = "default"
    settings.SHOW_AXES = False
    settings.SCREENSHOT_TRANSPARENT_BACKGROUND = False


def configure_brainrender(config):
    settings.SHADER_STYLE = config["shader_style"]


def create_scene(config, title, offscreen=False):
    root = config.get("regions_to_show") is None and config.get("mesh_mode") == "root"
    scene = Scene(atlas_name=config["atlas_name"], title=title, root=root, check_latest=False)
    if offscreen:
        scene.plotter.window.SetOffScreenRendering(True)
    return scene


def add_atlas_content(scene, config):
    regions = config.get("regions_to_show")
    if regions is not None:
        for region in regions:
            scene.add_brain_region(region, alpha=config["region_alpha"], silhouette=True)
        if hasattr(scene, "root") and scene.root is not None:
            if config.get("show_root", True):
                scene.root.c(ROOT_COLOR).alpha(config["root_alpha"])
            else:
                scene.root.alpha(0)
        return
    _add_atlas_geometry(
        scene,
        config["mesh_mode"],
        config.get("region_mode", "leaves"),
        config["root_alpha"],
        config["region_alpha"],
    )


def apply_view(scene, config):
    """Pose → camera → slice. Returns camera dict or None."""
    ub = union_bounds(scene)
    if ub is not None:
        apply_subject_pose(scene, config["subject_pose"], bounds_center(ub))

    camera = None
    ub = union_bounds(scene)
    if ub is not None:
        camera = make_camera(config, ub)

    apply_slice(scene, config)
    scene.plotter.axes = config.get("plotter_axes", 0)
    return camera


def render_scene(scene, camera, interactive):
    if camera is not None:
        scene.render(camera=camera, interactive=interactive)
    else:
        scene.render(interactive=interactive)


# -----------------------------------------------------------------------------
# Batch overlays — probes, custom OBJs, brainmapper cells
# -----------------------------------------------------------------------------


def subject_from_folder(folder):
    name = Path(folder).name
    if name.startswith("ds_"):
        parts = name.split("_")
        if len(parts) >= 2:
            return parts[1]
    return name


def print_root_bounds(scene, subject_id):
    if not hasattr(scene, "root") or scene.root is None:
        return
    xmin, xmax, ymin, ymax, zmin, zmax = scene.root.bounds()
    print(
        f"{subject_id}: bounds",
        f"x=[{xmin:.1f}, {xmax:.1f}]",
        f"y=[{ymin:.1f}, {ymax:.1f}]",
        f"z=[{zmin:.1f}, {zmax:.1f}]",
    )


def add_brainreg_overlays(scene, brainreg_dir, config):
    atlas_space = Path(brainreg_dir) / "segmentation" / "atlas_space"
    tracks_dir = atlas_space / "tracks"
    regions_dir = atlas_space / "regions"
    cells_path = Path(brainreg_dir) / "brainmapper" / "points" / "points.npy"

    for npy_path in sorted(tracks_dir.glob("*.npy")):
        scene.add(Points(np.load(npy_path), name=npy_path.stem, colors=PROBE_COLOR, radius=PROBE_RADIUS))

    if regions_dir.exists():
        for obj_path in sorted(regions_dir.glob("*.obj")):
            scene.add(str(obj_path), color=CUSTOM_REGION_COLOR, alpha=CUSTOM_REGION_ALPHA)

    if cells_path.exists():
        cells = np.load(cells_path)
        max_pts = config.get("max_points", 5000)
        if len(cells) > max_pts:
            step = len(cells) / max_pts
            idx = (np.arange(max_pts) * step).astype(int)
            cells = cells[idx]
        scene.add(Points(cells, radius=CELLS_RADIUS, colors=CELLS_COLOR))


# -----------------------------------------------------------------------------
# Output filenames / interactive screenshots
# -----------------------------------------------------------------------------


def _sanitize_filename(s):
    return "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in s)


def batch_png_title_parts(subject_id, config):
    parts = [
        f"sub-{subject_id}",
        f"dist-{config['camera_distance_factor']:.2f}",
        f"rot-{config['camera_rotation_deg']:.1f}",
        f"el-{config['camera_elevation_deg']:.1f}",
    ]
    slice_mode = config.get("slice_mode")
    if slice_mode and slice_mode not in ("none", None):
        parts.append(f"slice-{slice_mode}")
        if slice_mode == "custom":
            parts.append(f"depth-{config['plane_depth']:.2f}")
            n = config["custom_plane_normal"]
            parts.append(f"n-{n[0]:.2f}_{n[1]:.2f}_{n[2]:.2f}")
    return parts


def batch_png_filename(subject_id, config):
    return _sanitize_filename("_".join(batch_png_title_parts(subject_id, config))) + ".png"


def maybe_save_atlas_screenshots(scene, config):
    n = config["custom_plane_normal"]
    if n in ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)):
        tag = "frontal"
    elif n in ((0.0, 0.0, -1.0), (0.0, 0.0, 1.0)):
        tag = "sagittal"
    elif n in ((0.0, 1.0, 0.0), (0.0, -1.0, 0.0)):
        tag = "horizontal"
    else:
        return
    scene.screenshot(name=f"atlas_screenshot_{config['slice_mode']}_{tag}.png", scale=2)
