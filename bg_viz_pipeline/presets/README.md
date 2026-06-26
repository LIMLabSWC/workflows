# Viewer presets (`viewer_presets.json`)

JSON array consumed by [`batch_render.py`](../scripts/batch_render.py). Each object is
converted to a settings dict by ``core.settings_from_preset()`` (shared
camera/slice/pose/mesh fields with the ``SETTINGS`` dict in
`interactive_render.py`, plus batch-only keys below; JSON keys are UPPER_SNAKE).

Edit the file, then from the repo root:

```bash
python -m bg_viz_pipeline.scripts.batch_render
```

Script usage and workflow: [`scripts/README.md`](../scripts/README.md).

---

## Required fields

| Field | Type | Description |
|-------|------|-------------|
| `BRAINREG_SUBDIR` | string | Folder name under `BASE_DIR` in `batch_render.py` (e.g. `ds_MPX-R-0033_250606_...`) |
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
| `BASE_FRONTAL_AZIMUTH_DEG` | number | `180` | What `CAMERA_ROTATION_DEG = 0` means (`base_frontal_azimuth_deg: 0.0` in interactive `SETTINGS`) |
| `SHOW_ROOT` | bool | `true` | Show whole-brain outline behind regions |
| `ROOT_ALPHA` | number | `0.2` | Root mesh opacity when `SHOW_ROOT` is true |
| `REGION_ALPHA` | number | `0.2` | Highlighted atlas region opacity |
| `MAX_POINTS` | int | `5000` | Cap on brainmapper cells plotted |
| `SUBJECT_POSE` | string | `"on_base"` | `"on_base"`, `"on_bulb"`, or `"on_side"` |
| `CLOSE_ACTORS` | bool | `false` | Open cut vs solid cap (`true` + `SLICE_CAP_COLOR` for capped cut) |
| `SLICE_CAP_COLOR` | string or `null` | none | Cut-face colour when `CLOSE_ACTORS` is true (defaults to `"salmon"` if capped) |
| `MESH_MODE` | string | `"regions"` | `"root"` or `"regions"` (interactive-style atlas mesh) |
| `REGION_MODE` | string | `"leaves"` | `"leaves"` or `"all"` when using region meshes |
| `PLOTTER_AXES` | int | `9` | vedo axes mode (`0` = off; `8` or `9` = labelled cube axes) |
| `SHADER_STYLE` | string | `"plastic"` | `"cartoon"` or `"plastic"` |
| `ATLAS_NAME` | string | from `batch_render.py` | Override atlas if needed |

---

## Slice modes

| `SLICE_MODE` | Plane |
|--------------|-------|
| `"none"` | No cut |
| `"frontal"` | Atlas frontal plane (+x) |
| `"horizontal"` | Atlas horizontal plane (+y) |
| `"sagittal"` | Atlas sagittal plane (+z) |
| `"custom"` | Uses `CUSTOM_PLANE_NORMAL` and `PLANE_DEPTH` |

For `custom`, `PLANE_DEPTH` interpolates between the bounding-box extremes along the chosen normal (same idea as `interactive_render`).

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

**Match interactive camera base (azimuth 0 instead of batch default 180)**

```json
{
  "BASE_FRONTAL_AZIMUTH_DEG": 0.0
}
```

(Add alongside the other fields in the same preset object.)

**Hide root mesh**

```json
{
  "SHOW_ROOT": false
}
```

---

## Output filenames

PNG names are built from preset values, for example:

```
sub-MPX-R-0033_dist-4.00_rot--45.0_el--15.0_slice-custom_depth-0.40_n-1.00_0.00_0.00.png
```

Use this to match a figure back to the preset that produced it.

---

## Tips

- Duplicate a preset object to try a small change (e.g. `PLANE_DEPTH` or `CAMERA_ROTATION_DEG`).
- Use `--only-subject` or `--only-subdir` to render a subset while iterating.
- When copying from `interactive_render`, use the key map in [`scripts/README.md`](../scripts/README.md#configuration-reference) (`camera_rotation_deg` → `CAMERA_ROTATION_DEG`, etc.). Include `BASE_FRONTAL_AZIMUTH_DEG` if you use a non-default `base_frontal_azimuth_deg`.
- Run `list_regions` to print a ready-made `REGIONS_TO_SHOW` list for a subject.
