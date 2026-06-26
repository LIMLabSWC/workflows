#!/usr/bin/env python3
"""
Probe region × shank summary tables (SVG).

Reads per-shank CSV files under ``segmentation/atlas_space/tracks``, builds one
table per probe (shanks = columns, regions = rows), colours cells with BrainGlobe
atlas colours, and saves an SVG to the workflows repo root.

Also prints a terminal summary (regions per shank, then a copy-paste list for
``REGIONS_TO_SHOW`` in presets).

Run from repo root::

    python -m bg_viz_pipeline.scripts.list_regions
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from brainglobe_atlasapi import BrainGlobeAtlas
from matplotlib.patches import Patch

from bg_viz_pipeline.lib.core import DEFAULT_ATLAS_NAME

# =============================================================================
# Configuration — edit these paths
# =============================================================================

BRAINREG_DIR = Path(
    "/media/viktor/DataDrive/use_cases/ds_ROI-1_230620_102737_25_25_ch02_chan_2_red_2x4shankNPX"
)
# scripts/ → bg_viz_pipeline/ → workflows/
REPO_ROOT = Path(__file__).resolve().parents[2]
TRACKS = BRAINREG_DIR / "segmentation/atlas_space/tracks"

# Figure layout: inches per grid cell (width and height of each table cell)
CELL = 0.32

# =============================================================================
# Atlas colours
# =============================================================================

atlas = BrainGlobeAtlas(DEFAULT_ATLAS_NAME)
# Index atlas table by acronym for quick name / id lookup
meta = atlas.lookup_df.set_index("acronym")


def rgb01(acronym: str) -> tuple[float, float, float]:
    """Atlas rgb_triplet (0–255) → matplotlib colour (0–1)."""
    structure_id = int(meta.loc[acronym, "id"])
    return tuple(c / 255 for c in atlas.structures[structure_id]["rgb_triplet"])


def by_id(acronyms: set[str]) -> list[str]:
    """Sort region acronyms by atlas hierarchy id (stable row / legend order)."""
    return sorted(
        acronyms,
        key=lambda a: (int(meta.loc[a, "id"]) if a in meta.index else 10**9, a),
    )


# =============================================================================
# Load track CSVs into one table
# =============================================================================

# One row per (shank, region). drop_duplicates keeps first encounter per shank.
parts = []
for csv_path in sorted(TRACKS.glob("*.csv")):
    table = pd.read_csv(csv_path)
    table = table.loc[
        table["Region acronym"].notna()
        & (table["Region acronym"] != "Not found in brain")
    ]
    table = table.drop_duplicates("Region acronym")[["Region acronym"]]
    table["shank"] = csv_path.stem  # e.g. probe_PFC_shank_1
    parts.append(table)

df = pd.concat(parts, ignore_index=True)

# Split filename stem into probe id and shank number
df[["probe", "shank_n"]] = df["shank"].str.extract(r"^(.+)_shank_(\d+)$")
df["shank_n"] = df["shank_n"].astype(int)

if df.empty:
    raise SystemExit(f"No region CSV files found in: {TRACKS}")

# =============================================================================
# Terminal summary — regions per shank + copy-paste list for presets
# =============================================================================

print("--------------------------------")
print("These are the regions per shank:\n")
for shank_name in sorted(df["shank"].unique()):
    regions = df.loc[df["shank"] == shank_name, "Region acronym"].tolist()
    print(f"{shank_name}: {', '.join(regions)}")
print("--------------------------------\n")

all_unique = []
for shank_name in sorted(df["shank"].unique()):
    for acronym in df.loc[df["shank"] == shank_name, "Region acronym"]:
        if acronym not in all_unique:
            all_unique.append(acronym)
preset_list = "[" + ", ".join(f'"{r}"' for r in all_unique) + "]"
print(f"These are all the unique regions in this brain:\n\n{preset_list}\n")

# =============================================================================
# Layout: one row of subplots per probe + shared legend column
# =============================================================================

probes = sorted(df["probe"].unique())
max_cols = df.groupby("probe")["shank_n"].nunique().max()
row_counts = [df.loc[df["probe"] == p, "Region acronym"].nunique() for p in probes]
all_acronyms = set(df["Region acronym"])

fig = plt.figure(figsize=((max_cols + 10) * CELL, (sum(row_counts) + 1.5) * CELL))
gs = fig.add_gridspec(
    len(probes),
    2,
    width_ratios=[max_cols, 7],  # second column = legend width (in cell units)
    height_ratios=row_counts,
    hspace=0.5,
    wspace=0.2,
)

# =============================================================================
# Draw one colour grid per probe
# =============================================================================

for i, probe in enumerate(probes):
    ax = fig.add_subplot(gs[i, 0])
    sub = df.loc[df["probe"] == probe]
    shanks = sorted(sub["shank_n"].unique())
    regions = by_id(set(sub["Region acronym"]))

    # White grid; fill cells where this shank visits the region
    grid = np.full((len(regions), len(shanks), 3), 1.0)
    for j, shank_num in enumerate(shanks):
        hit = set(sub.loc[sub["shank_n"] == shank_num, "Region acronym"])
        for row_i, acronym in enumerate(regions):
            if acronym in hit:
                grid[row_i, j] = rgb01(acronym)

    ax.imshow(grid, aspect="equal", interpolation="nearest")
    ax.set_xticks(range(len(shanks)), labels=shanks)
    ax.set_yticks(range(len(regions)), labels=regions, fontsize=7)
    ax.set_title(probe)
    ax.set_xlabel("Shank")
    ax.set_ylabel("Region")
    # Vertical lines between shank columns
    ax.set_xticks(np.arange(-0.5, len(shanks), 1), minor=True)
    ax.grid(which="minor", axis="x", color="0.7", linewidth=0.8)

# =============================================================================
# Shared legend (all regions across probes)
# =============================================================================

leg_ax = fig.add_subplot(gs[:, 1])
leg_ax.axis("off")
ordered = by_id(all_acronyms)
leg_ax.legend(
    [Patch(facecolor=rgb01(a), edgecolor="0.5") for a in ordered],
    [f"{a} — {meta.loc[a, 'name']}" for a in ordered],
    loc="upper left",
    frameon=False,
    fontsize=8,
)
leg_ax.set_title("Regions", loc="left", fontsize=10)

# =============================================================================
# Save
# =============================================================================

subject = BRAINREG_DIR.name.removeprefix("ds_").split("_")[0]
fig.suptitle(f"Probe regions — {subject}", fontsize=12, y=0.99)
fig.patch.set_alpha(0)
for ax in fig.axes:
    ax.set_facecolor("none")

out = REPO_ROOT / f"probe_regions_{subject}.svg"
fig.savefig(out, format="svg", transparent=True, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
print(f"Saved {out}")
