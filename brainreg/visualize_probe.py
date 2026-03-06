#!/usr/bin/env python3

"""
Visualize probe `.npy` tracks in brainrender and export an interactive HTML file.

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
import numpy as np

from brainrender import Scene
from brainrender.actors import Points

# ----------------------------
# Argument parser
# ----------------------------
parser = argparse.ArgumentParser(description="Brainrender probe visualization")

parser.add_argument("atlas_name", type=str, help="Atlas name for brainrender")
parser.add_argument("tracks_dir", type=str, help="Directory containing track_*.npy")
parser.add_argument("output_html", type=str, help="Output HTML file")

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

# ----------------------------
# Ensure output directory exists
# ----------------------------
output_path.parent.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Create the scene
# ----------------------------
scene = Scene(atlas_name=atlas_name, title="implant")

# ----------------------------
# Add requested brain regions
# ----------------------------
for reg in args.regions:
    scene.add_brain_region(reg, alpha=0.15)

# ----------------------------
# Load and add probe tracks
# ----------------------------
track_files = sorted(resource_path.glob("track_*.npy"))

if not track_files:
    print(f"No track_*.npy files found in: {resource_path}")
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
