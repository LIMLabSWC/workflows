#!/usr/bin/env python3

"""
Visualize probe `.npy` tracks in brainrender and export an interactive HTML file.

All `.npy` track files in the given directory are rendered. Brain regions are
either supplied via `--regions` or automatically derived from the per‑probe
CSV files (one CSV per probe/shank) using the "Region acronym" column.

Usage:
    python visualize_probe.py <atlas_name> <tracks_dir> <output_html> [--regions R1 R2 ...]

Example:
    python visualize_probe.py \
        swc_female_rat_50um \
        /path/to/tracks \
        /path/to/out.html \
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

# ----------------------------
# Argument parser
# ----------------------------
parser = argparse.ArgumentParser(description="Brainrender probe visualization")

parser.add_argument("atlas_name", type=str, help="Atlas name for brainrender")
parser.add_argument(
    "tracks_dir",
    type=str,
    help="Directory containing probe `.npy` tracks and per‑probe CSV files",
)
parser.add_argument("output_html", type=str, help="Output HTML file path")

parser.add_argument(
    "--regions",
    nargs="*",
    default=[],
    help="List of brain region acronyms to display (e.g. --regions M2 VLO LO)"
)

args = parser.parse_args()

atlas_name   = args.atlas_name
resource_path = Path(args.tracks_dir)
output_path   = Path(args.output_html)


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
probe_regions = get_probe_regions(resource_path)

print("\n" + "=" * 80)
print(" PROBE / REGION SUMMARY")
print("=" * 80)

if probe_regions:
    print("Detected regions per probe/shank:")
    for probe_name, acr_list in probe_regions.items():
        print(f"  {probe_name}: {', '.join(acr_list)}")
else:
    print(f"No region CSV files found in: {resource_path}")

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
    else:
        print("No regions could be derived from CSV files.")

print("=" * 80 + "\n")

for reg in regions_to_show:
    scene.add_brain_region(reg, alpha=0.15)

# ----------------------------
# Load and add probe tracks
# ----------------------------
# Find all .npy files in the directory (regardless of prefix)
track_files = sorted(resource_path.glob("*.npy"))

if not track_files:
    print(f"No .npy track files found in: {resource_path}")
    sys.exit(1)

for i, tf in enumerate(track_files, start=1):
    coords = np.load(tf)
    scene.add(
        Points(
            coords,
            name=f"probe_{i}",
            colors="darkred",
            radius=50,
        )
    )

# ----------------------------
# Export HTML
# ----------------------------
scene.export(output_path)
print(f"Saved visualization to: {output_path}")
