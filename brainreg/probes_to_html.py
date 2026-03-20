#!/usr/bin/env python3

"""
Export probe `.npy` tracks to an interactive brainrender HTML file.

All `.npy` files under `segmentation/atlas_space/tracks` are drawn with
`brainrender.actors.Points` (sphere glyphs along each track).
Brain regions are either supplied via `--regions` or automatically derived
from the per‑probe CSV files (one CSV per probe/shank) using the
"Region acronym" column. Optionally, additional custom region meshes can be
overlaid from `.obj` files found in `segmentation/atlas_space/regions` (unless
`--no-custom-regions` is passed).

Usage:
    python probes_to_html.py <atlas_name> <brainreg_dir> <output_html>
        [--regions R1 R2 ...] [--no-custom-regions]

Example:
    python probes_to_html.py \
        swc_female_rat_50um \
        /path/to/brainreg_output \
        ROI_1_probes.html \
        --regions M2 VLO LO
"""

# ----------------------------
# Headless settings (no popup)
# ----------------------------
import os
os.environ["DISPLAY"] = ""
os.environ["PYOPENGL_PLATFORM"] = "egl"
os.environ["OFFSCREEN"] = "1"
os.environ["VTK_DEFAULT_RENDER_WINDOW_OFFSCREEN"] = "1"

# ----------------------------
# Imports
# ----------------------------
import sys
import argparse
from pathlib import Path
import csv
import numpy as np

from brainrender import Scene
from brainrender.actors import Points
from camera_helpers import create_camera
from styles import (
    REGION_ALPHA,
    CUSTOM_REGION_COLOR,
    CUSTOM_REGION_ALPHA,
    PROBE_COLOR,
    PROBE_RADIUS,
)

# ----------------------------
# Argument parser
# ----------------------------
parser = argparse.ArgumentParser(description="Brainrender probe visualization")

parser.add_argument("atlas_name", type=str, help="Atlas name for brainrender")
parser.add_argument(
    "brainreg_dir",
    type=str,
    help="Directory containing brainreg outputs",
)
parser.add_argument(
    "output_file_name",
    type=str,
    help="Output HTML file name (saved under brainreg_dir/segmentation/)",
)

parser.add_argument(
    "--regions",
    nargs="*",
    default=[],
    help="List of brain region acronyms to display (e.g. --regions M2 VLO LO)"
)
parser.add_argument(
    "--no-custom-regions",
    action="store_true",
    help="Disable loading custom region meshes from atlas_space/regions",
)
args = parser.parse_args()

atlas_name = args.atlas_name
brainreg_dir = Path(args.brainreg_dir)

atlas_space_dir = brainreg_dir / "segmentation" / "atlas_space"
tracks_dir = atlas_space_dir / "tracks"
regions_dir = atlas_space_dir / "regions"

output_path = brainreg_dir / "segmentation" / Path(args.output_file_name)

def find_custom_region_meshes(custom_regions_dir: Path) -> list[Path]:
    """
    Discover custom `.obj` region meshes in custom_regions_dir.

    Returns a sorted list of paths to `.obj` files. These paths can then be
    added to the scene elsewhere, e.g.:

        for obj_path in find_custom_region_meshes(...):
            scene.add(str(obj_path), color="crimson", alpha=0.4)
    """
    custom_regions_dir = Path(custom_regions_dir)

    if not custom_regions_dir.exists():
        print(f"Custom regions directory does not exist: {custom_regions_dir}")
        return []

    obj_files = sorted(custom_regions_dir.glob("*.obj"))

    print("\n" + "=" * 80)
    print(" CUSTOM REGION MESHES")
    print("=" * 80)

    if not obj_files:
        print(f"No .obj files found in: {custom_regions_dir}")
        print("=" * 80 + "\n")
        return []

    for obj_path in obj_files:
        print(f"  found: {obj_path.name}")

    print("=" * 80 + "\n")
    return obj_files


def get_probe_regions(input_dir: Path) -> dict:
    """
    Return a mapping from probe/shank name (CSV stem) to the
    ordered list of unique region acronyms encountered along
    that track.

    Expects CSV files with at least a "Region acronym" column.
    """
    regions_per_probe: dict[str, list[str]] = {}
    excluded_acronyms = {"Not found in brain"}

    for csv_path in sorted(input_dir.glob("*.csv")):
        probe_name = csv_path.stem  # e.g. "probe_2_shank_1"
        seen: set[str] = set()
        ordered_acronyms: list[str] = []

        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            if "Region acronym" not in reader.fieldnames:
                continue

            for row in reader:
                acr = row.get("Region acronym", "").strip()
                if not acr or acr in excluded_acronyms:
                    continue
                if acr not in seen:
                    seen.add(acr)
                    ordered_acronyms.append(acr)

        if ordered_acronyms:
            regions_per_probe[probe_name] = ordered_acronyms

    return regions_per_probe

# ----------------------------
# Ensure output directory exists
# ----------------------------
output_path.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Create the scene
# ----------------------------
scene = Scene(atlas_name=atlas_name, title="implant")

# ----------------------------
# Determine brain regions to show
# ----------------------------
probe_regions = get_probe_regions(tracks_dir)
custom_region_files: list[Path] = []

if not args.no_custom_regions and regions_dir.exists():
    custom_region_files = find_custom_region_meshes(regions_dir)

print("\n" + "=" * 80)
print(" PROBE / REGION SUMMARY")
print("=" * 80)

if probe_regions:
    print("Detected regions per probe/shank:")
    for probe_name, acr_list in probe_regions.items():
        print(f"  {probe_name}: {', '.join(acr_list)}")
else:
    print(f"No region CSV files found in: {tracks_dir}")

print("-" * 80)

if args.regions:
    # User explicitly requested regions
    regions_to_show = args.regions
    print(f"Using user-specified regions: {', '.join(regions_to_show)}")
else:
    # Automatically derive regions from CSVs, preserving order of appearance
    ordered_union: list[str] = []
    seen_union: set[str] = set()
    for _, acr_list in probe_regions.items():
        for acr in acr_list:
            if acr not in seen_union:
                seen_union.add(acr)
                ordered_union.append(acr)
    regions_to_show = ordered_union
    if regions_to_show:
        print(f"Using automatically derived regions: {', '.join(regions_to_show)}")
        print("\n")
        print(
            "If you want to omit regions from this list, "
            "rerun the script with the --regions flag to "
            "specify the regions you want to show.",
        )
    else:
        print("No regions could be derived from CSV files.")

print("=" * 80 + "\n")

for reg in regions_to_show:
    scene.add_brain_region(reg, alpha=REGION_ALPHA)

for obj_path in custom_region_files:
    scene.add(str(obj_path), color=CUSTOM_REGION_COLOR, alpha=CUSTOM_REGION_ALPHA)

# ----------------------------
# Load and add probe tracks
# ----------------------------
if not tracks_dir.exists():
    print(f"Tracks directory does not exist: {tracks_dir}")
    sys.exit(1)

# Find all .npy files in the tracks directory (regardless of prefix)
track_files = sorted(tracks_dir.glob("*.npy"))

if not track_files:
    print(f"No .npy track files found in: {tracks_dir}")
    sys.exit(1)

for i, tf in enumerate(track_files, start=1):
    coords = np.load(tf)
    scene.add(
        Points(
            coords,
            name=f"probe_{i}",
            colors=PROBE_COLOR,
            radius=PROBE_RADIUS,
        )
    )

# ----------------------------
# Camera (atlas-aware, similar to brainreg_viewer)
# ----------------------------
if hasattr(scene, "root") and scene.root is not None:
    xmin, xmax, ymin, ymax, zmin, zmax = scene.root.bounds()

    # Frontal-like baseline; distance/angles chosen for a general overview.
    _BASE_FRONTAL_AZIMUTH_DEG = 180.0
    _DIST_FACTOR = 2.0
    _ROT_DEG = 0.0
    _EL_DEG = -20.0

    cam = create_camera(
        (xmin, xmax, ymin, ymax, zmin, zmax),
        distance_factor=_DIST_FACTOR,
        base_frontal_azimuth_deg=_BASE_FRONTAL_AZIMUTH_DEG,
        rotation_deg=_ROT_DEG,
        elevation_deg=_EL_DEG,
    )
    # Render once to apply the camera before export; still headless.
    scene.render(camera=cam, interactive=False)

# ----------------------------
# Export HTML
# ----------------------------
scene.export(output_path)
print(f"Saved visualization to: {output_path}")
