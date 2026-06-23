# Viewer presets (`viewer_presets.json`)

JSON array consumed by [`brainreg_viewer.py`](../scripts/brainreg_viewer.py). Each object describes one PNG to render.

Edit the file, then from the repo root:

```bash
python -m bg_viz_pipeline.scripts.brainreg_viewer
```

Script usage and workflow: [`scripts/README.md`](../scripts/README.md).

---

## Required fields

| Field | Type | Description |
|-------|------|-------------|
| `BRAINREG_SUBDIR` | string | Folder name under `BASE_DIR` in `brainreg_viewer.py` (e.g. `ds_MPX-R-0033_250606_...`) |
| `REGIONS_TO_SHOW` | list of strings | Atlas region acronyms to highlight (e.g. `["M2", "cc-ec-cing-dwm"]`) |
| `CAMERA_DISTANCE_FACTOR` | number | Zoom; distance = factor × max brain extent |
| `CAMERA_ROTATION_DEG` | number | Orbit left/right around the brain |
| `CAMERA_ELEVATION_DEG` | number | Camera tilt along atlas y ([details](../scripts/README.md#atlas-coordinates)) |

---

## Optional fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `SLICE_MODE` | string | `"none"` | `"none"`, `"frontal"`, `"horizontal"`, `"sagittal"`, or `"custom"` |
| `PLANE_DEPTH` | number | `0.0` | Slice position along the plane normal, 0–1 (used when slicing) |
| `CUSTOM_PLANE_NORMAL` | `[x, y, z]` | `[0, 0, 1]` | Plane direction when `SLICE_MODE` is `"custom"` |
| `SHOW_ROOT` | bool | `true` | Show whole-brain outline behind regions |
| `MAX_POINTS` | int | `5000` | Cap on brainmapper cells plotted |

---

## Slice modes

| `SLICE_MODE` | Plane |
|--------------|-------|
| `"none"` | No cut |
| `"frontal"` | Atlas frontal plane (+x) |
| `"horizontal"` | Atlas horizontal plane (+y) |
| `"sagittal"` | Atlas sagittal plane (+z) |
| `"custom"` | Uses `CUSTOM_PLANE_NORMAL` and `PLANE_DEPTH` |

For `custom`, `PLANE_DEPTH` interpolates between the bounding-box extremes along the chosen normal (same idea as `render_atlas`).

Common custom normals (this atlas):

| View | Example normal |
|------|----------------|
| Frontal | `[1, 0, 0]` or `[-1, 0, 0]` |
| Horizontal | `[0, 1, 0]` or `[0, -1, 0]` |
| Sagittal | `[0, 0, 1]` or `[0, 0, -1]` |

---

## Example presets

**No slice — regions + probes only**

```json
{
  "BRAINREG_SUBDIR": "ds_MPX-R-0033_250606_133230_25_25_ch02_chan_2_red",
  "REGIONS_TO_SHOW": ["M2", "cc-ec-cing-dwm"],
  "CAMERA_DISTANCE_FACTOR": 4.0,
  "CAMERA_ROTATION_DEG": -45.0,
  "CAMERA_ELEVATION_DEG": -15.0,
  "SLICE_MODE": "none"
}
```

**Custom frontal slice**

```json
{
  "BRAINREG_SUBDIR": "ds_MPX-R-0033_250606_133230_25_25_ch02_chan_2_red",
  "REGIONS_TO_SHOW": ["M2", "cc-ec-cing-dwm"],
  "CAMERA_DISTANCE_FACTOR": 4.0,
  "CAMERA_ROTATION_DEG": -45.0,
  "CAMERA_ELEVATION_DEG": -15.0,
  "SLICE_MODE": "custom",
  "PLANE_DEPTH": 0.4,
  "CUSTOM_PLANE_NORMAL": [1.0, 0.0, 0.0]
}
```

**Hide root mesh**

```json
{
  "SHOW_ROOT": false
}
```

(Add alongside the other fields in the same preset object.)

---

## Output filenames

PNG names are built from preset values, for example:

```
sub-MPX-R-0033_dist-4.00_rot--45.0_el--15.0_slice-custom_depth-0.40_n-1.00_0.00_0.00.png
```

Use this to match a figure back to the preset that produced it.

---

## Not in presets yet

| Feature | Where it works today |
|---------|---------------------|
| `SUBJECT_POSE` (`on_base` / `on_bulb` / `on_side`) | [`render_atlas.py`](../scripts/render_atlas.py) only |
| `CLOSE_ACTORS` / coloured slice cap | `render_atlas.py` only |
| `MESH_MODE` root vs regions | `render_atlas.py` only |

To batch these, add fields to JSON and read them in `brainreg_viewer.render_one()` using the same order as `render_atlas`: add meshes → pose → camera → slice.

---

## Tips

- Duplicate a preset object to try a small change (e.g. `PLANE_DEPTH` or `CAMERA_ROTATION_DEG`).
- Use `--only-subject` or `--only-subdir` to render a subset while iterating.
- Camera numbers tuned in `render_atlas` transfer to presets, but `brainreg_viewer` uses frontal azimuth `180°` internally — you may need to offset rotation compared to `render_atlas`'s `_BASE_FRONTAL_AZIMUTH_DEG`.
