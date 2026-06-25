"""
Unified view settings for interactive and batch atlas rendering.

``ViewConfig`` is the single model behind ``interactive_render.py`` (module
constants) and ``viewer_presets.json`` (via ``from_preset_dict``). Field names
in presets use the same UPPER_SNAKE keys as the interactive config block.

Python concepts used in this file (plain language)
--------------------------------------------------
**Class** — a blueprint for grouping related data and behaviour. Here,
``ViewConfig`` bundles all camera / slice / pose settings in one object instead
of passing dozens of separate variables.

**Dataclass** (``@dataclass``) — a shortcut that writes boring boilerplate for
you: it creates ``__init__`` so you can write ``ViewConfig(atlas_name="...", ...)``
and access fields as ``config.camera_rotation_deg``. Without it you'd write
many lines of repetitive assignment code.

**frozen=True** — after you build a ``ViewConfig``, you cannot change its fields
(e.g. ``config.camera_rotation_deg = 5`` would raise an error). Settings are
fixed for one render pass, which avoids accidental mutation mid-pipeline.

**Type hints** (``str``, ``float``, ``bool``, ``list[str] | None``) — notes for
humans and tools about what each value should be. They do not change runtime
behaviour; ``x: float = 4.0`` still works like a normal variable with default 4.0.
``list[str] | None`` means "either a list of strings, or None".

**Literal** (``MeshMode = Literal["root", "regions"]``) — a type hint meaning
"this string must be one of these exact options". Helps catch typos like
``"regoin"`` early.

**@classmethod** — a function tied to the class itself, not one instance.
``ViewConfig.from_preset_dict(...)`` is a factory: read JSON → return a new
``ViewConfig``. The first argument ``cls`` is the class (``ViewConfig``).

**Mapping** — anything dict-like (``dict``, JSON object after ``json.load``).
We use it because presets come from JSON, not necessarily a plain ``dict``.
"""

from __future__ import annotations

# ``dataclass`` is from the standard library — see module docstring above.
from dataclasses import dataclass
from typing import Any, Literal, Mapping

from bg_viz_pipeline.lib.camera_helpers import create_camera, DEFAULT_BATCH_BASE_FRONTAL_AZIMUTH_DEG
from bg_viz_pipeline.lib.pose_helpers import SubjectPose
from bg_viz_pipeline.lib.styles import (
    BATCH_REGION_ALPHA,
    BATCH_ROOT_ALPHA,
    BATCH_SHADER_STYLE,
)

# Allowed values for a few string settings (documentation + type checking).
MeshMode = Literal["root", "regions"]
RegionMode = Literal["leaves", "all"]
ShaderStyle = Literal["cartoon", "plastic"]


def _as_tuple3(value: Any) -> tuple[float, float, float]:
    """
    Convert JSON ``[x, y, z]`` (a list) into a Python ``(x, y, z)`` tuple.

    Presets store normals as lists; our code prefers immutable tuples.
    Leading underscore means "internal helper, not part of the public API".
    """
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise ValueError(f"Expected [x, y, z], got {value!r}")


@dataclass(frozen=True)
class ViewConfig:
    """
    Camera, slice, pose, and scene-content settings shared by both renderers.

    Each line below declares one field. Syntax::

        field_name: type = default_value

    is the same idea as a variable with a type note and default, but grouped
    inside the class. ``self`` in methods below refers to "this config object".
    """

    atlas_name: str

    # Atlas geometry (interactive uses mesh_mode; batch uses regions_to_show)
    mesh_mode: MeshMode = "root"
    regions_to_show: list[str] | None = None  # None = not used (interactive root/regions mode)
    region_mode: RegionMode = "leaves"
    show_root: bool = True
    root_alpha: float = 0.8
    region_alpha: float = 1.0

    # Pose
    subject_pose: SubjectPose = "on_base"

    # Camera — total azimuth = base_frontal_azimuth_deg + camera_rotation_deg
    camera_distance_factor: float = 4.0
    camera_rotation_deg: float = -45.0
    camera_elevation_deg: float = -30.0
    base_frontal_azimuth_deg: float = 0.0

    # Slice
    slice_mode: str = "none"
    plane_depth: float = 0.0
    custom_plane_normal: tuple[float, float, float] = (0.0, 0.0, 1.0)
    close_actors: bool = True
    slice_cap_color: str | None = "salmon"  # str | None = string or "no colour"

    # Display
    plotter_axes: int = 0
    shader_style: ShaderStyle = "cartoon"

    # Batch-only (None for interactive atlas-only views)
    brainreg_subdir: str | None = None
    max_points: int = 5000

    def make_camera(
        self,
        bounds: tuple[float, float, float, float, float, float],
    ) -> dict:
        """
        Build a brainrender camera dict from bounds and this config.

        ``self`` is this ViewConfig instance — we read its camera fields and pass
        them to ``create_camera`` in ``camera_helpers.py``.
        """
        return create_camera(
            bounds,
            distance_factor=self.camera_distance_factor,
            base_frontal_azimuth_deg=self.base_frontal_azimuth_deg,
            rotation_deg=self.camera_rotation_deg,
            elevation_deg=self.camera_elevation_deg,
        )

    @classmethod
    def from_preset_dict(
        cls,
        preset: Mapping[str, Any],
        *,
        atlas_name: str,
        default_base_frontal_azimuth_deg: float = DEFAULT_BATCH_BASE_FRONTAL_AZIMUTH_DEG,
        default_region_alpha: float = BATCH_REGION_ALPHA,
        default_shader_style: ShaderStyle = BATCH_SHADER_STYLE,
    ) -> ViewConfig:
        """
        Parse one object from ``viewer_presets.json`` into a ``ViewConfig``.

        **classmethod** — call as ``ViewConfig.from_preset_dict(preset, ...)``,
        not on an existing instance. ``cls`` is ``ViewConfig``; ``return cls(...)``
        builds a new frozen config.

        **preset.get("KEY", default)** — like dict lookup, but returns
        ``default`` if the key is missing (batch presets omit many optional keys).

        The lone ``*`` in the signature forces ``atlas_name=...`` to be passed
        by name (keyword), not position — avoids mixing up argument order.
        """
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

        # JSON keys are UPPER_SNAKE; ViewConfig fields are lower_snake — mapped here.
        return cls(
            atlas_name=str(preset.get("ATLAS_NAME", atlas_name)),
            mesh_mode=preset.get("MESH_MODE", "regions"),
            regions_to_show=list(preset["REGIONS_TO_SHOW"]),
            region_mode=preset.get("REGION_MODE", "leaves"),
            show_root=bool(preset.get("SHOW_ROOT", True)),
            root_alpha=float(preset.get("ROOT_ALPHA", BATCH_ROOT_ALPHA)),
            region_alpha=float(preset.get("REGION_ALPHA", default_region_alpha)),
            subject_pose=preset.get("SUBJECT_POSE", "on_base"),
            camera_distance_factor=float(preset["CAMERA_DISTANCE_FACTOR"]),
            camera_rotation_deg=float(preset["CAMERA_ROTATION_DEG"]),
            camera_elevation_deg=float(preset["CAMERA_ELEVATION_DEG"]),
            base_frontal_azimuth_deg=float(
                preset.get("BASE_FRONTAL_AZIMUTH_DEG", default_base_frontal_azimuth_deg)
            ),
            slice_mode=preset.get("SLICE_MODE", "none"),
            plane_depth=float(preset.get("PLANE_DEPTH", 0.0)),
            custom_plane_normal=_as_tuple3(
                preset.get("CUSTOM_PLANE_NORMAL", (0.0, 0.0, 1.0))
            ),
            close_actors=close_actors,
            slice_cap_color=slice_cap_color,
            plotter_axes=int(preset.get("PLOTTER_AXES", 0)),
            shader_style=preset.get("SHADER_STYLE", default_shader_style),
            brainreg_subdir=str(preset["BRAINREG_SUBDIR"]),
            max_points=int(preset.get("MAX_POINTS", 5000)),
        )
