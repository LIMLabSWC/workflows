from __future__ import annotations

from bg_viz_pipeline.lib.view_config import ViewConfig


def sanitize_filename(s: str) -> str:
    """Make a string safe for use as a PNG filename."""
    return "".join(
        c if c.isalnum() or c in ("-", "_", ".") else "_"
        for c in s
    )


def batch_png_title_parts(subject_id: str, config: ViewConfig) -> list[str]:
    """Build filename/title tokens from a preset ``ViewConfig``."""
    parts = [f"sub-{subject_id}"]
    parts.append(f"dist-{config.camera_distance_factor:.2f}")
    parts.append(f"rot-{config.camera_rotation_deg:.1f}")
    parts.append(f"el-{config.camera_elevation_deg:.1f}")

    slice_mode = config.slice_mode
    if slice_mode and slice_mode not in ("none", None):
        parts.append(f"slice-{slice_mode}")
        if slice_mode == "custom":
            parts.append(f"depth-{config.plane_depth:.2f}")
            n = config.custom_plane_normal
            parts.append(f"n-{n[0]:.2f}_{n[1]:.2f}_{n[2]:.2f}")

    return parts


def batch_png_filename(subject_id: str, config: ViewConfig) -> str:
    """Encoded PNG filename for a batch render."""
    return sanitize_filename("_".join(batch_png_title_parts(subject_id, config))) + ".png"
