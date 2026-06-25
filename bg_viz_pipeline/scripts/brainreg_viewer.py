#!/usr/bin/env python3
"""
Batch-render brainreg scenes to PNG (offscreen).

Reads presets from ``presets/viewer_presets.json``. For each preset, builds
a scene with atlas regions, probe tracks, optional custom segmentation, and
brainmapper cells, then saves a filename-encoded screenshot.

Run::

    python -m bg_viz_pipeline.scripts.brainreg_viewer [--only-subdir ...] [--only-subject ...]

Pipeline (``render_one``)::

    create_scene → add_atlas_content → add_brainreg_overlays → apply_view → render
"""

import argparse
import json
from pathlib import Path

from brainrender import settings

from bg_viz_pipeline.lib.brainreg_loaders import (
    add_brainreg_overlays,
    print_root_bounds,
    subject_from_folder,
)
from bg_viz_pipeline.lib.output_helpers import batch_png_filename, batch_png_title_parts
from bg_viz_pipeline.lib.scene_pipeline import (
    add_atlas_content,
    apply_view,
    configure_brainrender,
    create_scene,
    render_scene,
)
from bg_viz_pipeline.lib.view_config import ViewConfig

settings.LIGHTING = "default"
settings.SHOW_AXES = False
settings.SCREENSHOT_TRANSPARENT_BACKGROUND = False

# Atlas name used by brainreg for these data
ATLAS_NAME = "viktors_tweaked_warp_swc_female_rat_25um"

# Base directory with all subjects
BASE_DIR = Path(
    "/media/viktor/DataDrive/use_cases"
)


def render_one(preset: dict) -> None:
    """
    Render one PNG for a preset.

    Requires ``.../atlas_space/tracks`` with at least one ``.npy``.
    """
    config = ViewConfig.from_preset_dict(preset, atlas_name=ATLAS_NAME)
    configure_brainrender(config)

    brainreg_dir = BASE_DIR / config.brainreg_subdir
    subject_id = subject_from_folder(brainreg_dir)

    scene = create_scene(config, title=subject_id, offscreen=True)
    add_atlas_content(scene, config)
    print_root_bounds(scene, subject_id)
    add_brainreg_overlays(scene, brainreg_dir, config)

    camera = apply_view(scene, config)

    scene.title = " | ".join(batch_png_title_parts(subject_id, config))
    filename = batch_png_filename(subject_id, config)

    render_scene(scene, camera, interactive=False)
    scene.screenshot(name=filename, scale=2)


def render_all(presets: list[dict], args: argparse.Namespace) -> None:
    """Iterate over all presets and render the ones matching CLI filters."""
    for preset in presets:
        subdir = preset["BRAINREG_SUBDIR"]

        if args.only_subdir and args.only_subdir not in subdir:
            continue

        if args.only_subject:
            subj = subject_from_folder(Path(subdir))
            if args.only_subject not in subj:
                continue

        render_one(preset)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Render brainreg PNG views from JSON presets."
    )
    parser.add_argument(
        "--only-subdir",
        type=str,
        help=(
            "Only render presets whose BRAINREG_SUBDIR contains this "
            "substring."
        ),
    )
    parser.add_argument(
        "--only-subject",
        type=str,
        help=(
            "Only render presets whose derived subject_id (from folder name) "
            "contains this substring (e.g. 'ROI-1', 'MPX-R-0033')."
        ),
    )
    args = parser.parse_args()

    presets_path = (
        Path(__file__).resolve().parents[1] / "presets" / "viewer_presets.json"
    )
    with presets_path.open() as f:
        presets = json.load(f)

    render_all(presets, args)
