"""
Unified view settings for interactive and batch atlas rendering.

``ViewConfig`` is the single model behind ``render_atlas.py`` (module constants)
and ``viewer_presets.json`` (via ``from_preset_dict``). Field names in presets
use the same UPPER_SNAKE keys as the interactive config block.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from bg_viz_pipeline.lib.camera_helpers import create_camera
from bg_viz_pipeline.lib.pose_helpers import SubjectPose

MeshMode = Literal["root", "regions"]
RegionMode = Literal["leaves", "all"]
ShaderStyle = Literal["cartoon", "plastic"]

# Preserved batch default: existing presets assumed frontal azimuth 180°.
DEFAULT_BATCH_BASE_FRONTAL_AZIMUTH_DEG = 180.0


def _as_tuple3(value: Any) -> tuple[float, float, float]:
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (float(value[0]), float(value[1]), float(value[2]))
    raise ValueError(f"Expected [x, y, z], got {value!r}")


@dataclass(frozen=True)
class ViewConfig:
    """Camera, slice, pose, and scene-content settings shared by both renderers."""

    atlas_name: str

    # Atlas geometry (interactive uses mesh_mode; batch uses regions_to_show)
    mesh_mode: MeshMode = "root"
    regions_to_show: list[str] | None = None
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
    slice_cap_color: str | None = "salmon"

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
        """Build a brainrender camera dict from bounds and this config."""
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
        default_region_alpha: float = 0.2,
        default_shader_style: ShaderStyle = "plastic",
    ) -> ViewConfig:
        """
        Parse a ``viewer_presets.json`` entry.

        Missing keys use batch-oriented defaults (e.g. frontal azimuth 180°) so
        existing presets keep the same appearance.
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

        return cls(
            atlas_name=str(preset.get("ATLAS_NAME", atlas_name)),
            mesh_mode=preset.get("MESH_MODE", "regions"),
            regions_to_show=list(preset["REGIONS_TO_SHOW"]),
            region_mode=preset.get("REGION_MODE", "leaves"),
            show_root=bool(preset.get("SHOW_ROOT", True)),
            root_alpha=float(preset.get("ROOT_ALPHA", 0.2)),
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
