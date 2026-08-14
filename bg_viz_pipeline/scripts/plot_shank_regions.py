#!/usr/bin/env python3
"""
NP2.0 4-shank probe with traversed regions drawn to scale (SVG).

What this script does (in order):
  1. Load atlas colours
  2. Load per-shank track CSVs (region along depth)
  3. Load official NP2.0 geometry from ProbeInterface
  4. For each probe panel:
       a. paint region rectangles
       b. overlay probe outline + contacts (plot_probe)
       c. draw bank brackets on the right
       d. zoom to insertion depth
  5. Add legend + save SVG

Run from repo root::

    python -m bg_viz_pipeline.scripts.plot_shank_regions
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from brainglobe_atlasapi import BrainGlobeAtlas
from matplotlib.patches import Patch, Rectangle
from probeinterface.neuropixels_tools import build_neuropixels_probe
from probeinterface.plotting import plot_probe

# =============================================================================
# 0) KNOBS — edit here
# =============================================================================

# --- data ---
ATLAS_NAME = "swc_female_rat_50um"
NP2_PART = "NP2013"  # Neuropixels 2.0 4-shank catalogue probe
OUT_BRAIN = "Not found in brain"  # CSV label outside the atlas

BRAINREG_DIR = Path(
    "/media/viktor/DataDrive/use_cases/ds_ROI-1_230620_102737_25_25_ch02_chan_2_red_2x4shankNPX"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
# Real data:
# TRACKS = BRAINREG_DIR / "segmentation/atlas_space/tracks"

# Temporary fake CSVs:
TRACKS = Path("/home/viktor/Documents/fake_tracks")

# --- figure size ---
PANEL_W = 3.2  # inches per probe panel
FIG_H = 9.0
LEGEND_W = 3.6  # extra inches for the legend column

# --- text sizes (matplotlib fontsize) ---
FS_TITLE = 14  # per-probe panel title
FS_SUPTITLE = 14  # whole-figure title
FS_LEGEND = 14
FS_SHANK = 14  # "1" "2" "3" "4" above each shank
FS_BANK = 14  # "bank 0" labels

# --- look ---
REGION_ALPHA = 0.85
CONTACT_ALPHA = 0.4
BRACKET_GAP = 40  # µm to the right of the probe before the bank bracket
BRACKET_W = 50


# =============================================================================
# 1) ATLAS COLOURS
# =============================================================================

atlas = BrainGlobeAtlas(ATLAS_NAME, check_latest=False)
meta = atlas.lookup_df.set_index("acronym")


def rgb01(acronym: str) -> tuple[float, float, float]:
    """Atlas rgb_triplet (0–255) → matplotlib colour (0–1)."""
    structure_id = int(meta.loc[acronym, "id"])
    return tuple(c / 255 for c in atlas.structures[structure_id]["rgb_triplet"])


def by_id(acronyms: set[str]) -> list[str]:
    """Sort acronyms by atlas id (stable legend order)."""
    return sorted(
        acronyms,
        key=lambda a: (int(meta.loc[a, "id"]) if a in meta.index else 10**9, a),
    )


# =============================================================================
# 2) LOAD TRACK CSVs
# =============================================================================
# One file per shank, e.g. probe_PFC_shank_1.csv.
# "Distance from first position [um]" = arc length along the track.
# We treat the largest distance as the tip (deep end).

parts = []
for csv_path in sorted(TRACKS.glob("*.csv")):
    table = pd.read_csv(csv_path)
    table = table.loc[table["Region acronym"].notna()]
    table["shank"] = csv_path.stem
    parts.append(table)

if not parts:
    raise SystemExit(f"No region CSV files found in: {TRACKS}")

df = pd.concat(parts, ignore_index=True)
# Filename → probe name + shank number (CSV is 1..4; ProbeInterface is 0..3)
df[["probe", "shank_n"]] = df["shank"].str.extract(r"^(.+)_shank_(\d+)$")
df["shank_n"] = df["shank_n"].astype(int)


# =============================================================================
# 3) PROBE GEOMETRY + BANK DEPTHS
# =============================================================================

np2 = build_neuropixels_probe(NP2_PART)
xy = np2.contact_positions  # (N, 2) µm; y≈0 near tip, larger toward base
shank_ids = np2.shank_ids.astype(int)
tips = np.asarray(np2.annotations["shank_tips"], float)

# Catalogue bank = electrode_index // 384 (not a SpikeGLX IMRO selection).
# Bank 3 is shorter (~128 sites); banks 0–2 are full 384.
elec = np.fromiter((int(cid.split("e", 1)[1]) for cid in np2.contact_ids), int)
banks = elec // 384
bank_y = {
    int(b): (
        float(xy[(shank_ids == 0) & (banks == b), 1].min()),
        float(xy[(shank_ids == 0) & (banks == b), 1].max()),
    )
    for b in np.unique(banks)
}
bracket_x = float(xy[:, 0].max()) + BRACKET_GAP


# =============================================================================
# 4) SMALL DRAW HELPERS  (one job each — read these when editing the figure)
# =============================================================================

def draw_region_bands(ax, track, x0, width, y_tip):
    """Paint one rectangle per consecutive region along the track."""
    dist = track["Distance from first position [um]"].to_numpy(float)
    acr = track["Region acronym"].to_numpy()
    dmax = float(dist[-1])

    # Run edges: start of region → start of next (no gaps)
    change = np.flatnonzero(acr[1:] != acr[:-1]) + 1
    starts = np.concatenate([[0], change])
    ends = np.concatenate([change, [len(acr)]])

    for i0, i1 in zip(starts, ends):
        a = acr[i0]
        if a == OUT_BRAIN or a not in meta.index:
            continue
        d0 = float(dist[i0])
        d1 = float(dist[i1]) if i1 < len(dist) else dmax
        # Deepest sample (dmax) at tip; surface (d≈0) higher up.
        # ponytail: rectangles ignore tip taper (~200 µm on ~10 mm shank).
        y_lo = y_tip + (dmax - d1)
        height = d1 - d0
        if height <= 0:
            continue
        ax.add_patch(
            Rectangle(
                (x0, y_lo),
                width,
                height,
                facecolor=rgb01(a),
                edgecolor="none",
                zorder=0,
                alpha=REGION_ALPHA,
            )
        )


def draw_bank_brackets(ax, y_lo_view, y_hi_view):
    """Draw ] brackets + 'bank N' labels for banks visible in the zoom window."""
    for b, (y0, y1) in sorted(bank_y.items()):
        if y1 < y_lo_view or y0 > y_hi_view:
            continue
        y0c, y1c = max(y0, y_lo_view), min(y1, y_hi_view)
        ax.plot(
            [bracket_x, bracket_x + BRACKET_W, bracket_x + BRACKET_W, bracket_x],
            [y0c, y0c, y1c, y1c],
            color="0.2",
            lw=0.8,
            clip_on=False,
        )
        ax.text(
            bracket_x + BRACKET_W + 8,
            0.5 * (y0c + y1c),
            f"bank {b}",
            va="center",
            ha="left",
            fontsize=FS_BANK,
            color="0.2",
            clip_on=False,
        )


def style_panel(ax, title, y_lo, y_hi):
    """Zoom, title, hide clutter."""
    ax.set_ylim(y_lo, y_hi)
    ax.set_xlim(ax.get_xlim()[0], bracket_x + BRACKET_W + 90)
    ax.set_title(title, fontsize=FS_TITLE)
    ax.set_xticks([])
    ax.tick_params(labelsize=FS_BANK)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)


# =============================================================================
# 5) BUILD THE FIGURE  (recipe — one panel per probe)
# =============================================================================

probes = sorted(df["probe"].unique())
all_acronyms = {a for a in df["Region acronym"].unique() if a != OUT_BRAIN}

fig, axes = plt.subplots(
    1,
    len(probes),
    figsize=(PANEL_W * len(probes) + LEGEND_W, FIG_H),
    squeeze=False,
)
axes = axes[0]

for ax, probe_name in zip(axes, probes):
    sub = df.loc[df["probe"] == probe_name]
    insert_um = float(sub["Distance from first position [um]"].max())
    y_tip0 = float(tips[:, 1].min())
    y_hi_view = y_tip0 + insert_um + 400

    # --- 5a) region rectangles (behind everything) ---
    for shank_num in sorted(sub["shank_n"].unique()):
        si = int(shank_num) - 1
        on = shank_ids == si
        if not on.any():
            continue
        xs = xy[on, 0]
        x0 = float(xs.min() - 10)
        width = float(xs.max() - xs.min() + 20)
        y_tip = float(tips[si, 1])
        track = sub.loc[sub["shank_n"] == shank_num].sort_values(
            "Distance from first position [um]"
        )
        draw_region_bands(ax, track, x0, width, y_tip)
        ax.text(
            xs.mean(),
            y_tip + insert_um + 150,
            str(shank_num),
            ha="center",
            va="bottom",
            fontsize=FS_SHANK,
        )

    # --- 5b) official probe outline + contacts ---
    plot_probe(
        np2,
        ax=ax,
        contacts_colors=["0.25"] * np2.get_contact_count(),
        title=False,
        probe_shape_kwargs={"facecolor": "none", "edgecolor": "0.15", "lw": 0.6},
        contact_kwargs={"lw": 0, "alpha": CONTACT_ALPHA},
    )

    # --- 5c) bank brackets ---
    draw_bank_brackets(ax, y_tip0, y_hi_view)

    # --- 5d) zoom to insertion (plot_probe otherwise shows the full ~10 mm) ---
    style_panel(ax, probe_name, y_tip0 - 50, y_hi_view)


# =============================================================================
# 6) LEGEND + SAVE
# =============================================================================

ordered = by_id(all_acronyms)
fig.legend(
    [Patch(facecolor=rgb01(a), edgecolor="0.5") for a in ordered],
    [f"{a} — {meta.loc[a, 'name']}" for a in ordered],
    loc="center left",
    bbox_to_anchor=(1.01, 0.5),
    frameon=False,
    fontsize=FS_LEGEND,
    title="Regions",
)

subject = BRAINREG_DIR.name.removeprefix("ds_").split("_")[0]
fig.suptitle(f"NP2.0 4-shank regions — {subject}", fontsize=FS_SUPTITLE)
fig.patch.set_alpha(0)
for ax in fig.axes:
    ax.set_facecolor("none")

out = REPO_ROOT / f"probe_shanks_{subject}.svg"
fig.savefig(out, format="svg", transparent=True, bbox_inches="tight", pad_inches=0.08)
plt.close(fig)
print(f"Saved {out}")
