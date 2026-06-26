# Visualization scripts

Python tools for exploring atlas geometry and batch-rendering brainreg subjects.
Run all commands from the **`workflows` repo root** (so `bg_viz_pipeline` is importable).

Requires a BrainGlobe conda env (e.g. `brainglobe-env`).

## Quick comparison

| Script | Input | Output | Use when |
|--------|-------|--------|----------|
| [`interactive_render.py`](interactive_render.py) | `SETTINGS` dict at top of file | Interactive window (+ optional PNG) | Tuning slice, camera, pose on the atlas alone |
| [`batch_render.py`](batch_render.py) | [`presets/viewer_presets.json`](../presets/viewer_presets.json) | One PNG per preset | Batch figures with probes + regions for real subjects |
| [`probes_to_html.py`](probes_to_html.py) | CLI args | Interactive HTML | Shareable 3D probe view in a browser |
| [`list_regions.py`](list_regions.py) | `BRAINREG_DIR`, `CELL` at top of file | SVG + terminal region summary | Per-probe region × shank summary tables |
| [`list_cell_counts.py`](list_cell_counts.py) | `SUMMARY_CSV`, `TOP_N` at top of file | SVG in repo root | Bar chart of cellfinder cells per atlas region |
| [`make_white_transparent.py`](make_white_transparent.py) | CLI: input/output dirs | PNGs with white → alpha | Post-process batch PNGs for figures |

Preset field reference: [`presets/README.md`](../presets/README.md).

---

## `interactive_render` — interactive atlas explorer

Edit the ``SETTINGS`` dict at the top of [`interactive_render.py`](interactive_render.py), then:

```bash
python -m bg_viz_pipeline.scripts.interactive_render
```

### Three independent controls

Think of three dials you tune separately:

1. **Pose** (`subject_pose` in `SETTINGS`; `SUBJECT_POSE` in JSON) — how the specimen is mounted.
2. **Camera** (`camera_*`, `base_frontal_azimuth_deg`) — where you stand in the room.
3. **Slice** (`slice_mode`, `plane_depth`, `custom_plane_normal`, …) — where you cut.

Pose and camera are **intentionally separate**: changing pose moves the brain, not the camera. Re-tune camera after changing pose if the view no longer makes sense.

### Configuration reference

[`viewer_presets.json`](../presets/viewer_presets.json) uses **UPPER_SNAKE** keys.
[`interactive_render.py`](interactive_render.py) uses the same settings as **lower_snake**
keys in the ``SETTINGS`` dict (e.g. `CAMERA_ROTATION_DEG` → `camera_rotation_deg`).

| Setting | Values / type | What it does |
|---------|---------------|--------------|
| `mesh_mode` | `"root"` \| `"regions"` | Whole-brain shell vs atlas regions |
| `region_mode` | `"leaves"` \| `"all"` | Which regions when `mesh_mode == "regions"` |
| `root_alpha` / `region_alpha` | float | Mesh opacity (interactive defaults from `core.py`) |
| `subject_pose` | `"on_base"` \| `"on_bulb"` \| `"on_side"` | Specimen mounting |
| `camera_distance_factor` | float | Zoom (larger = farther) |
| `camera_rotation_deg` | float | Orbit left/right |
| `camera_elevation_deg` | float | Camera tilt along atlas y (see [Atlas coordinates](#atlas-coordinates)) |
| `base_frontal_azimuth_deg` | float | What “rotation = 0” means for this atlas |
| `slice_mode` | `"none"`, `"frontal"`, `"horizontal"`, `"sagittal"`, `"custom"` | Cut plane |
| `plane_depth` | 0–1 | Position along normal (`0` = one extreme, `1` = other) |
| `custom_plane_normal` | `(x, y, z)` | Direction when `slice_mode == "custom"` |
| `close_actors` | bool | `False` = open cut; `True` = solid cap |
| `slice_cap_color` | colour name or `None` | Cap colour when `close_actors` is True |
| `plotter_axes` | int | vedo axes (`0` = off; `8` or `9` = labelled cube axes; default `9` in `SETTINGS`) |
| `shader_style` | `"cartoon"` \| `"plastic"` | brainrender shader |
| `save_screenshot` | bool | Save PNG on window close (default `false`; interactive only) |
| `screenshot_path` | string, optional | Override filename (default: batch-style `atlas_*.png` from SETTINGS) |

**JSON ↔ `SETTINGS` key map** (presets use the left column; `interactive_render.py` uses the right):

| Preset (JSON) | `SETTINGS` dict |
|---------------|-----------------|
| `MESH_MODE` | `mesh_mode` |
| `REGION_MODE` | `region_mode` |
| `ROOT_ALPHA` | `root_alpha` |
| `REGION_ALPHA` | `region_alpha` |
| `SUBJECT_POSE` | `subject_pose` |
| `CAMERA_DISTANCE_FACTOR` | `camera_distance_factor` |
| `CAMERA_ROTATION_DEG` | `camera_rotation_deg` |
| `CAMERA_ELEVATION_DEG` | `camera_elevation_deg` |
| `BASE_FRONTAL_AZIMUTH_DEG` | `base_frontal_azimuth_deg` |
| `SLICE_MODE` | `slice_mode` |
| `PLANE_DEPTH` | `plane_depth` |
| `CUSTOM_PLANE_NORMAL` | `custom_plane_normal` |
| `CLOSE_ACTORS` | `close_actors` |
| `SLICE_CAP_COLOR` | `slice_cap_color` |
| `PLOTTER_AXES` | `plotter_axes` |
| `SHADER_STYLE` | `shader_style` |
| `ATLAS_NAME` | `atlas_name` |

Batch-only preset keys: `REGIONS_TO_SHOW`, `BRAINREG_SUBDIR`, `SHOW_ROOT`, `MAX_POINTS` (no interactive equivalent).

BrainGlobe axis names for this atlas: frontal **+x**, horizontal **+y**, sagittal **+z**.

### Atlas coordinates

Camera and slice knobs use **atlas/world coordinates**, not “up in the room”. For
`viktors_tweaked_warp_swc_female_rat_25um` the plotted **y axis points downward**
(y tick numbers increase toward the bottom of the window). The origin sits near
the dorsal/top edge of the volume, so most of the brain lies at positive y.

`camera_elevation_deg` moves the eye along that y axis. Tune by eye — do not
assume it matches intuitive above/below.

To see the axis numbers yourself, set `plotter_axes` to `8` or `9` in the
``SETTINGS`` dict (vedo cube axes on the bounding box).

Same camera settings, different pose — axes stay fixed in atlas space; only the
mesh rotates:

![Atlas axes, pose on_base](../docs/figures/atlas_axes_on_base.png)

*`subject_pose` = `"on_base"`*

![Atlas axes, pose on_bulb](../docs/figures/atlas_axes_on_bulb.png)

*`subject_pose` = `"on_bulb"`*

### Suggested workflow

1. Set `subject_pose`.
2. Adjust `camera_*` until the view looks right.
3. Set `slice_mode` and `plane_depth`.
4. Copy values into [`viewer_presets.json`](../presets/viewer_presets.json) using UPPER_SNAKE keys (see table above).

### Cookbook (starting points)

Tune by eye; these are reasonable first guesses:

**On base, oblique frontal**

```python
# In SETTINGS dict in interactive_render.py:
"subject_pose": "on_base",
"camera_distance_factor": 4.0,
"camera_rotation_deg": -45.0,
"camera_elevation_deg": -30.0,
"base_frontal_azimuth_deg": 0.0,
"slice_mode": "custom",
"custom_plane_normal": (-1.0, 0.0, 0.0),
"plane_depth": 0.4,
```

**On bulb (nose down)** — same camera, different mount:

```python
"subject_pose": "on_bulb",
# re-tune camera_* as needed
```

If a pose looks flipped, edit ``POSE_ROTATIONS_DEG`` in [`lib/core.py`](../lib/core.py).

### Screenshots

Set `save_screenshot: true` in the ``SETTINGS`` dict (or `save_screenshot` key in
`interactive_render.py`). When you **close** the window, a PNG is written to the
current directory.

- **Filename** — built from ``SETTINGS`` at launch (same tokens as batch:
  `dist`, `rot`, `el`, `slice`, `depth`, and `n-x_y_z` for custom planes).
  Override with `screenshot_path`.
- **Image** — whatever is on screen when you close (including orbit/zoom in the
  GUI). If you moved the camera, the picture may **not** match `rot` / `el` in
  the filename.

With `save_screenshot: false` (default), the interactive window opens with no save.

---

## `batch_render` — batch PNG export

Renders registered subjects with atlas regions, probe tracks, optional custom `.obj` regions, and brainmapper cells. Settings come from JSON presets.

1. Edit [`presets/viewer_presets.json`](../presets/viewer_presets.json) (see [`presets/README.md`](../presets/README.md)).
2. Set `BASE_DIR` in [`batch_render.py`](batch_render.py) to your data root if needed.
3. Run:

```bash
python -m bg_viz_pipeline.scripts.batch_render
python -m bg_viz_pipeline.scripts.batch_render --only-subject ROI-1
python -m bg_viz_pipeline.scripts.batch_render --only-subdir ds_MPX-R-0033
```

Output PNGs are written to the current directory. Filenames encode subject, camera, and slice settings (e.g. `sub-MPX-R-0033_dist-4.00_rot--45.0_el--15.0.png`).

**Note:** Batch presets default to `BASE_FRONTAL_AZIMUTH_DEG = 180` when omitted. Interactive `SETTINGS` uses `base_frontal_azimuth_deg: 0.0` — set the same value in both when copying camera settings.

Both scripts use [`lib/core.py`](../lib/core.py): `apply_view` runs pose → camera → slice
and sets `plotter_axes` from the preset / ``SETTINGS`` dict (batch default `9`, same as the
old `brainreg_viewer`; set `PLOTTER_AXES: 0` to hide). Batch presets default `CLOSE_ACTORS`
to `false` (`close_actors` in the settings dict); set `true` + `SLICE_CAP_COLOR` to match
interactive capped slices.

### Expected subject layout

```
<brainreg_dir>/
  segmentation/atlas_space/tracks/*.npy    # required (at least one)
  segmentation/atlas_space/tracks/*.csv   # optional (region tables per shank; for list_regions)
  segmentation/atlas_space/regions/*.obj   # optional
  brainmapper/points/points.npy            # optional
```

---

## `list_regions` — probe region × shank tables

Builds a flat summary figure: one table per probe, shanks as columns, brain
regions as rows. Cells use the same **BrainGlobe structure colours**
(`rgb_triplet`) as brainrender — not Napari’s default label colormap.

Edit `BRAINREG_DIR` and `CELL` at the top of [`list_regions.py`](list_regions.py), then:

```bash
python -m bg_viz_pipeline.scripts.list_regions
```

Writes `probe_regions_<subject>.svg` to the **workflows repo root** (alongside
other figure outputs like `atlas_*.png`).

**Terminal output:** regions per shank, then a JSON-style list of all unique
regions — copy into `REGIONS_TO_SHOW` in a preset (see [`presets/README.md`](../presets/README.md)).

### Input

Per-shank CSV files under `segmentation/atlas_space/tracks/` with at least
`Region acronym` (and `Region ID` in the atlas table for row ordering). Same
files used by `probes_to_html.py` to auto-detect regions. Filename stems must
follow `probe_<name>_shank_<n>` (e.g. `probe_PFC_shank_1.csv`).

### Figure behaviour

- **Rows / legend:** sorted by atlas region ID (stable hierarchy order;
  independent of Napari trace direction).
- **Cells:** coloured if that shank passes through the region; white otherwise.
- **Layout:** square cells, vertical dividers between shanks, transparent SVG
  background with tight crop.

Tune `CELL` (inches per grid cell) at the top of the script if the layout is
too cramped.

---

## `list_cell_counts` — cellfinder cells per region

Horizontal bar chart of **total detected cells** per atlas region from a
cellfinder ``analysis/summary.csv``. By default only the **top 15** regions by total cell count are drawn, with
separate **left** and **right** hemisphere bars per region. Bar colours use
BrainGlobe ``rgb_triplet`` (right bars are a darker variant).

Edit `SUMMARY_CSV` and `TOP_N` at the top of [`list_cell_counts.py`](list_cell_counts.py), then:

```bash
python -m bg_viz_pipeline.scripts.list_cell_counts
```

Writes ``cell_counts_<subject>.svg`` to the **workflows repo root**.

### Input

Cellfinder summary CSV with columns ``structure_name``, ``left_cell_count``,
``right_cell_count``, and ``total_cells``. Structure names are matched to the
atlas by full name (after stripping whitespace). Only the top ``TOP_N`` regions
by ``total_cells`` are drawn (default ``15``), each with left and right bars.

---

## `probes_to_html` — interactive HTML export

```bash
python -m bg_viz_pipeline.scripts.probes_to_html \
  <atlas_name> \
  <brainreg_dir> \
  <output.html> \
  --regions M2 VLO LO
```

See the module docstring in [`probes_to_html.py`](probes_to_html.py) for full options.

---

## `make_white_transparent` — PNG post-processing

Makes pure white `(255, 255, 255)` pixels transparent. Useful after
`batch_render` when figures need a clear background.

```bash
python -m bg_viz_pipeline.scripts.make_white_transparent ./pngs_in ./pngs_out
```

Requires Pillow (`pip install pillow`).

---

## Advanced (library code)

All 3D rendering shared by `interactive_render` and `batch_render` lives in one file:

| Module | Role |
|--------|------|
| [`lib/core.py`](../lib/core.py) | Shared constants and functions (`core.*`) |

Figure scripts (`list_regions`, `list_cell_counts`) are standalone — they only
import `DEFAULT_ATLAS_NAME` from `core.py`.

**Learning:** [`teaching/python_oop_exercises.md`](../../teaching/python_oop_exercises.md)
walks through the OOP ideas behind this pipeline. For a modular `ViewConfig`
version of the same render stack, see branch `refactor-to-batch-and-interactive`.
