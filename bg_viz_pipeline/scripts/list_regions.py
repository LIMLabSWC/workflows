#!/usr/bin/env python3
"""
List probe track regions and render a per-probe region × shank figure.

Reads per-shank CSV files under ``segmentation/atlas_space/tracks`` (same layout
as ``probes_to_html.py``). For each probe, draws a table with shanks as columns
and brain regions as rows. Cells are filled with the atlas annotation colour
when that shank passes through the region. A shared legend lists every region
with its acronym, full name, and colour.

Pipeline (``main``)::

    read track CSVs → group shanks by probe → look up atlas colours/IDs
    → build colour grids → save SVG

Run::

    python -m bg_viz_pipeline.scripts.list_regions

Row ordering
------------
Matrix rows and the legend are sorted by **atlas region ID** (hierarchy order).
That is independent of the direction you traced each shank in Napari.

Figure layout
-------------
- One subplot table per probe (e.g. ``probe_2``, ``probe_PFC``).
- Square cells (``aspect="equal"``); panel height grows with row count.
- SVG saved to the repo root with a transparent background and tight crop.
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from brainglobe_atlasapi import BrainGlobeAtlas
from matplotlib.patches import Patch

# =============================================================================
# Constants
# =============================================================================

# Parse filenames like "probe_2_shank_1" → probe_id="probe_2", shank_num=1
_SHANK_RE = re.compile(r"^(.+)_shank_(\d+)$")

# RGB tuples in 0–1 range for matplotlib
_EMPTY_COLOR = (1.0, 1.0, 1.0)    # white: shank does not pass through this region
_MISSING_COLOR = (0.85, 0.85, 0.85)  # grey: acronym not found in atlas lookup

# =============================================================================
# Configuration — edit these values
# =============================================================================

ATLAS_NAME = "viktors_tweaked_warp_swc_female_rat_25um"
BRAINREG_DIR = Path(
    "/media/viktor/DataDrive/use_cases/ds_ROI-1_230620_102737_25_25_ch02_chan_2_red_2x4shankNPX"
)
# parents[2]: scripts/ → bg_viz_pipeline/ → workflows/ (repo root)
REPO_ROOT = Path(__file__).resolve().parents[2]

# Figure layout — square cells, same size in every table
CELL_SIZE = 0.32   # inches per grid cell (width and height)
LEGEND_COLS = 7    # legend column width in "cell" units (gridspec ratio)


# =============================================================================
# Data loading — read brainreg track CSVs
# =============================================================================


def get_probe_regions(input_dir: Path) -> dict[str, list[str]]:
    """
    Read per-shank track CSVs and return regions encountered along each track.

    Each CSV corresponds to one shank (filename stem, e.g. ``probe_2_shank_1``).
    Rows in the CSV follow the order you traced the track in Napari. This function
    collapses consecutive duplicate regions into a single entry while preserving
    first-encounter order — that order is used only to know *which* regions a
    shank visits, not to sort the final figure (see ``_regions_sorted_by_id``).

    Parameters
    ----------
    input_dir
        Directory containing ``*.csv`` files (typically
        ``.../segmentation/atlas_space/tracks``).

    Returns
    -------
    dict[str, list[str]]
        Mapping from shank name (CSV stem) to ordered unique region acronyms.
        Example: ``{"probe_2_shank_1": ["Am-u", "BFR-u", ...], ...}``.
    """
    regions_per_probe: dict[str, list[str]] = {}
    excluded_acronyms = {"Not found in brain"}

    for csv_path in sorted(input_dir.glob("*.csv")):
        probe_name = csv_path.stem
        seen: set[str] = set()
        ordered_acronyms: list[str] = []

        with csv_path.open(newline="") as f:
            reader = csv.DictReader(f)
            if "Region acronym" not in (reader.fieldnames or []):
                continue

            for row in reader:
                acr = row.get("Region acronym", "").strip()
                if not acr or acr in excluded_acronyms:
                    continue
                # Keep first encounter only — later rows are the same region at depth
                if acr not in seen:
                    seen.add(acr)
                    ordered_acronyms.append(acr)

        if ordered_acronyms:
            regions_per_probe[probe_name] = ordered_acronyms

    return regions_per_probe


# =============================================================================
# Grouping — nest shanks under their parent probe
# =============================================================================


def _parse_shank_name(name: str) -> tuple[str, int]:
    """
    Split a track filename stem into probe id and shank number.

    Parameters
    ----------
    name
        CSV stem, e.g. ``"probe_PFC_shank_3"``.

    Returns
    -------
    tuple[str, int]
        ``(probe_id, shank_num)``, e.g. ``("probe_PFC", 3)``.
        If the name does not match the expected pattern, returns ``(name, 0)``.
    """
    match = _SHANK_RE.match(name)
    if not match:
        return name, 0
    return match.group(1), int(match.group(2))


def _group_by_probe(
    regions_per_shank: dict[str, list[str]],
) -> dict[str, dict[int, list[str]]]:
    """
    Re-key flat shank data into probe → shank number → region list.

    Parameters
    ----------
    regions_per_shank
        Output of :func:`get_probe_regions`.

    Returns
    -------
    dict[str, dict[int, list[str]]]
        Nested mapping, e.g.
        ``{"probe_2": {1: ["Am-u", ...], 2: [...], ...}, ...}``.
    """
    grouped: dict[str, dict[int, list[str]]] = defaultdict(dict)
    for shank_name, regions in regions_per_shank.items():
        probe_id, shank_num = _parse_shank_name(shank_name)
        grouped[probe_id][shank_num] = regions
    return dict(grouped)


# =============================================================================
# Atlas lookup — colours, names, hierarchy IDs
# =============================================================================


def _regions_sorted_by_id(
    regions: set[str],
    atlas_lookup: dict[str, dict[str, object]],
) -> list[str]:
    """
    Sort region acronyms by atlas hierarchy ID.

    Region IDs come from the BrainGlobe atlas tree. Lower IDs are not necessarily
    superficial-to-deep along a probe, but the ordering is stable and does not
    depend on trace direction.

    Parameters
    ----------
    regions
        Set of region acronyms to sort.
    atlas_lookup
        Output of :func:`_atlas_region_lookup`.

    Returns
    -------
    list[str]
        Acronyms sorted by ``id``, with acronym as tiebreaker.
    """

    def sort_key(acr: str) -> tuple[int, str]:
        info = atlas_lookup.get(acr)
        rid = int(info["id"]) if info else 10**9  # type: ignore[arg-type]
        return (rid, acr)

    return sorted(regions, key=sort_key)


def _atlas_region_lookup(atlas_name: str) -> dict[str, dict[str, object]]:
    """
    Build a fast acronym → metadata mapping from a BrainGlobe atlas.

    Parameters
    ----------
    atlas_name
        Registered atlas name (same as used by brainreg / brainrender).

    Returns
    -------
    dict[str, dict[str, object]]
        Per acronym: ``{"name": str, "rgb": (r,g,b), "id": int}``.
        ``rgb`` values are 0–255 integers from the atlas annotation table.
    """
    atlas = BrainGlobeAtlas(atlas_name)
    lookup: dict[str, dict[str, object]] = {}
    for _, row in atlas.lookup_df.iterrows():
        acr = str(row["acronym"])
        sid = row["id"]
        rgb = tuple(int(c) for c in atlas.structures[sid]["rgb_triplet"])
        lookup[acr] = {"name": str(row["name"]), "rgb": rgb, "id": int(sid)}
    return lookup


def _rgb01(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """Convert 0–255 RGB integers to 0–1 floats for matplotlib."""
    return (rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)


def _region_color(
    acronym: str,
    atlas_lookup: dict[str, dict[str, object]],
) -> tuple[float, float, float]:
    """
    Return the matplotlib colour for a region acronym.

    Falls back to grey if the acronym is missing from the atlas lookup.
    """
    info = atlas_lookup.get(acronym)
    if info is None:
        return _MISSING_COLOR
    return _rgb01(info["rgb"])  # type: ignore[arg-type]


# =============================================================================
# Plotting — one probe table and the shared legend
# =============================================================================


def _draw_probe_table(
    ax: plt.Axes,
    probe_id: str,
    shanks: dict[int, list[str]],
    atlas_lookup: dict[str, dict[str, object]],
) -> set[str]:
    """
    Draw a single probe's region × shank heatmap on ``ax``.

    The grid is built as a 3-D numpy array ``(n_rows, n_cols, 3)`` of RGB values,
    then displayed with ``imshow``. A coloured cell means that shank passes
    through that region; white means it does not.

    Parameters
    ----------
    ax
        Matplotlib axes to draw on.
    probe_id
        Title label, e.g. ``"probe_2"``.
    shanks
        ``{shank_number: [region acronyms along that shank], ...}``.
    atlas_lookup
        Atlas metadata for colours and row ordering.

    Returns
    -------
    set[str]
        All region acronyms present in this probe (used to build the legend).
    """
    shank_nums = sorted(shanks)
    # Union of regions across all shanks of this probe, sorted by atlas ID
    row_regions = _regions_sorted_by_id(set().union(*shanks.values()), atlas_lookup)
    n_rows = len(row_regions)
    n_cols = len(shank_nums)

    # Start with an all-white grid, then fill hits with atlas colours
    color_grid = np.full((n_rows, n_cols, 3), _EMPTY_COLOR)
    for col, shank_num in enumerate(shank_nums):
        shank_regions = set(shanks[shank_num])
        for row, acr in enumerate(row_regions):
            if acr in shank_regions:
                color_grid[row, col] = _region_color(acr, atlas_lookup)

    # aspect="equal" keeps each grid cell square
    ax.imshow(color_grid, interpolation="nearest", aspect="equal")

    # Minor x-ticks at cell boundaries (−0.5, 0.5, 1.5, …) draw vertical dividers
    ax.set_xticks(np.arange(-0.5, n_cols, 1), minor=True)
    ax.grid(which="minor", axis="x", color="0.7", linewidth=0.8)
    ax.tick_params(which="minor", bottom=False, left=False)

    # Major ticks label shank numbers (columns) and region acronyms (rows)
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels([f"{n}" for n in shank_nums])
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(row_regions)
    ax.set_title(probe_id)
    ax.set_xlabel("Shank")
    ax.set_ylabel("Region")

    return set(row_regions)


def _draw_legend(
    ax: plt.Axes,
    region_acronyms: list[str],
    atlas_lookup: dict[str, dict[str, object]],
) -> None:
    """
    Draw a colour swatch legend for all regions in the figure.

    Parameters
    ----------
    ax
        Dedicated legend axes (no table drawn here).
    region_acronyms
        Pre-sorted list of acronyms (by atlas ID).
    atlas_lookup
        Atlas metadata for colours and full region names.
    """
    ax.axis("off")
    handles: list[Patch] = []
    labels: list[str] = []

    for acr in region_acronyms:
        color = _region_color(acr, atlas_lookup)
        name = atlas_lookup.get(acr, {}).get("name", acr)
        handles.append(Patch(facecolor=color, edgecolor="0.5", linewidth=0.6))
        labels.append(f"{acr} — {name}")

    ax.legend(
        handles,
        labels,
        loc="upper left",
        frameon=False,
        fontsize=8,
        handlelength=1.2,
        handleheight=1.0,
        labelspacing=0.5,
    )
    ax.set_title("Regions", loc="left", fontsize=10, pad=8)


# =============================================================================
# Figure assembly
# =============================================================================


def make_figure(
    regions_per_shank: dict[str, list[str]],
    atlas_name: str,
    *,
    title: str | None = None,
) -> plt.Figure:
    """
    Build the full multi-probe figure with tables and legend.

    Layout uses ``gridspec``:
    - Left column: one table row per probe; height proportional to region count.
    - Right column: shared legend spanning all probe rows.
    - ``width_ratios`` / ``height_ratios`` are in "cell" units so square cells
      stay the same physical size across probes.

    Parameters
    ----------
    regions_per_shank
        Flat shank → regions mapping from :func:`get_probe_regions`.
    atlas_name
        BrainGlobe atlas name for colours and IDs.
    title
        Optional figure suptitle.

    Returns
    -------
    matplotlib.figure.Figure
        Fully drawn figure; caller saves and closes it.
    """
    atlas_lookup = _atlas_region_lookup(atlas_name)
    probes = _group_by_probe(regions_per_shank)

    if not probes:
        raise ValueError("No probe/shank region data found.")

    probe_items = sorted(probes.items())
    max_cols = max(len(shanks) for _, shanks in probe_items)
    # Each probe panel is as many rows tall as it has unique regions
    row_counts = [
        len(_regions_sorted_by_id(set().union(*shanks.values()), atlas_lookup))
        for _, shanks in probe_items
    ]
    total_rows = sum(row_counts)

    # Figure size in inches; +3 leaves room for y-axis region labels
    fig_w = (max_cols + LEGEND_COLS + 3) * CELL_SIZE
    fig_h = (total_rows + 1.5) * CELL_SIZE
    fig = plt.figure(figsize=(fig_w, fig_h))
    gs = fig.add_gridspec(
        len(probe_items),
        2,
        width_ratios=[max_cols, LEGEND_COLS],
        height_ratios=row_counts,
        hspace=0.5,
        wspace=0.2,
    )

    all_regions: set[str] = set()
    for row_idx, (probe_id, shanks) in enumerate(probe_items):
        table_ax = fig.add_subplot(gs[row_idx, 0])
        all_regions |= _draw_probe_table(table_ax, probe_id, shanks, atlas_lookup)

    legend_ax = fig.add_subplot(gs[:, 1])
    _draw_legend(legend_ax, _regions_sorted_by_id(all_regions, atlas_lookup), atlas_lookup)

    if title:
        fig.suptitle(title, fontsize=12, y=0.99)

    # Transparent background — no white canvas around the content
    fig.patch.set_alpha(0)
    for ax in fig.axes:
        ax.set_facecolor("none")
    return fig


# =============================================================================
# Entry point
# =============================================================================


def main() -> None:
    """Load track data, print a summary, render the figure, save SVG."""
    tracks_dir = BRAINREG_DIR / "segmentation" / "atlas_space" / "tracks"
    subject = BRAINREG_DIR.name.removeprefix("ds_").split("_")[0]
    output_path = REPO_ROOT / f"probe_regions_{subject}.svg"

    regions_per_shank = get_probe_regions(tracks_dir)
    if not regions_per_shank:
        raise SystemExit(f"No region CSV files found in: {tracks_dir}")

    for shank_name, regions in regions_per_shank.items():
        print(f"{shank_name}: {', '.join(regions)}")

    fig = make_figure(
        regions_per_shank,
        ATLAS_NAME,
        title=f"Probe regions — {subject}",
    )
    fig.savefig(
        output_path,
        format="svg",
        transparent=True,
        bbox_inches="tight",  # crop to content
        pad_inches=0.02,
    )
    plt.close(fig)
    print(f"\nSaved figure to: {output_path}")


if __name__ == "__main__":
    main()
