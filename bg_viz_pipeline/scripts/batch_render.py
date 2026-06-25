#!/usr/bin/env python3
"""
Batch-render brainreg scenes to PNG from presets/viewer_presets.json.

Run::

    python -m bg_viz_pipeline.scripts.batch_render [--only-subdir ...] [--only-subject ...]
"""

import argparse
import json
from pathlib import Path

from bg_viz_pipeline.lib import render

render.init_brainrender_settings()

ATLAS_NAME = render.DEFAULT_ATLAS_NAME
BASE_DIR = Path("/media/viktor/DataDrive/use_cases")
PRESETS_PATH = Path(__file__).resolve().parents[1] / "presets" / "viewer_presets.json"


def render_one(preset):
    settings = render.settings_from_preset(preset, atlas_name=ATLAS_NAME)
    render.configure_brainrender(settings)

    brainreg_dir = BASE_DIR / settings["brainreg_subdir"]
    subject_id = render.subject_from_folder(brainreg_dir)

    scene = render.create_scene(settings, title=subject_id, offscreen=True)
    render.add_atlas_content(scene, settings)
    render.print_root_bounds(scene, subject_id)
    render.add_brainreg_overlays(scene, brainreg_dir, settings)

    camera = render.apply_view(scene, settings)
    scene.title = " | ".join(render.batch_png_title_parts(subject_id, settings))
    render.render_scene(scene, camera, interactive=False)
    scene.screenshot(name=render.batch_png_filename(subject_id, settings), scale=2)


def main():
    parser = argparse.ArgumentParser(description="Render brainreg PNGs from JSON presets.")
    parser.add_argument("--only-subdir", help="Filter by BRAINREG_SUBDIR substring")
    parser.add_argument("--only-subject", help="Filter by subject id substring")
    args = parser.parse_args()

    with PRESETS_PATH.open() as f:
        presets = json.load(f)

    for preset in presets:
        subdir = preset["BRAINREG_SUBDIR"]
        if args.only_subdir and args.only_subdir not in subdir:
            continue
        if args.only_subject and args.only_subject not in render.subject_from_folder(Path(subdir)):
            continue
        render_one(preset)


if __name__ == "__main__":
    main()
