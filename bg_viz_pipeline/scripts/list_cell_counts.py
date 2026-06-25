#!/usr/bin/env python3
"""
Cellfinder cell counts per atlas region (SVG).

Reads ``analysis/summary.csv``, keeps the top N regions by total cell count,
draws left/right hemisphere bars coloured with BrainGlobe atlas colours, and
saves an SVG to the workflows repo root.

Run from repo root::

    python -m bg_viz_pipeline.scripts.list_cell_counts
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from brainglobe_atlasapi import BrainGlobeAtlas

from bg_viz_pipeline.lib.render import DEFAULT_ATLAS_NAME

# =============================================================================
# Configuration — edit these paths
# =============================================================================

SUMMARY_CSV = Path(
    "/home/viktor/Drives/ceph/_projects/capsid_testing/rawdata/"
    "sub-030_id-CAP30/ses-01_date-20220913_dtype-2pe/2pe/"
    "cellfinder_swc_female_rat/50um/cellfinder_output_09042026/analysis/summary.csv"
)
# scripts/ → bg_viz_pipeline/ → workflows/
REPO_ROOT = Path(__file__).resolve().parents[2]

# Only plot this many regions (largest total_cells first)
TOP_N = 15

# =============================================================================
# Load summary and keep top regions
# =============================================================================

df = pd.read_csv(SUMMARY_CSV)
df = df.loc[df["total_cells"] > 0].nlargest(TOP_N, "total_cells").iloc[::-1]

# =============================================================================
# Match structure names to atlas acronym + colour
# =============================================================================

atlas = BrainGlobeAtlas(DEFAULT_ATLAS_NAME)
meta = atlas.lookup_df.set_index(atlas.lookup_df["name"].str.strip())

df["acronym"] = df["structure_name"].str.strip().map(meta["acronym"])
df["rgb"] = df["structure_name"].str.strip().map(
    lambda name: tuple(atlas.structures[meta.loc[name, "id"]]["rgb_triplet"])
)


def to_mpl(rgb: tuple[int, int, int], dark: bool = False) -> list[float]:
    """Convert atlas rgb (0–255) to matplotlib; right bars use a darker variant."""
    colour = [x / 255 for x in rgb]
    return [min(1, x * 0.72) for x in colour] if dark else colour


# =============================================================================
# Horizontal bar chart: left (−x) and right (+x) from centre line
# =============================================================================

y_labels = df["acronym"]
fig, ax = plt.subplots(figsize=(7, 7))

ax.barh(
    y_labels,
    -df["left_cell_count"],
    color=[to_mpl(r) for r in df["rgb"]],
    height=0.75,
)
ax.barh(
    y_labels,
    df["right_cell_count"],
    color=[to_mpl(r, dark=True) for r in df["rgb"]],
    height=0.75,
)
ax.axvline(0, color="0.45")

max_count = max(df["left_cell_count"].max(), df["right_cell_count"].max())
ax.set_xlim(-max_count * 1.08, max_count * 1.08)
ax.set_xlabel("Cell count")
ax.text(0.01, 1.01, "Left", transform=ax.transAxes, ha="left", va="bottom")
ax.text(0.99, 1.01, "Right", transform=ax.transAxes, ha="right", va="bottom")

# =============================================================================
# Save — subject id from path like .../sub-030_id-CAP30/...
# =============================================================================

subject = SUMMARY_CSV.parent.parent.name
for part in SUMMARY_CSV.parts:
    if part.startswith("sub-") and "_id-" in part:
        subject = part.split("_id-", 1)[1]
        break

out = REPO_ROOT / f"cell_counts_{subject}.svg"
fig.savefig(out, format="svg", transparent=True, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print(f"Saved {out}")
