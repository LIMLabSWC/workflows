# BrainGlobe workflow for registration, segmentation, and visualization

Brain registration (`brainreg`), segmentation post-processing, and
visualization for use-case / paper workflows.

This workflow has three phases:

1. **Registration (SLURM):** run `brainreg` to create per-subject output folders with `registered_atlas.tiff`.
2. **Segmentation + probe annotations (Napari):** open the registered subject outputs, add probe tracks/injections, and save into the subject’s `segmentation/` folder.
3. **Visualization (Python):** render probe HTML and/or atlas+region PNG views from `segmentation/atlas_space/`.

## Project folder layout

SLURM scripts, data, and outputs are kept together in one project folder
(e.g. your NFS project directory). The SLURM config expects:

- `PROJECT_DIR/data` — input TIFs (any subdirs)
- `PROJECT_DIR/brainreg_outputs_<atlas>/` — registration outputs

Copy/symlink the `bg_viz_pipeline/slurm/` folder into your project folder
(preserving the `slurm/` subfolder), and edit `slurm/brainreg_config.sh` to
set `PROJECT_DIR`.

## Phase 1 (Registration, SLURM)
See [`bg_viz_pipeline/slurm/README.md`](slurm/README.md) for details of how
the SLURM scripts work and how to run them.

At a minimum:
- edit `slurm/brainreg_config.sh`
- run `./slurm/submit_brainreg.sh`

## Phase 2 (Segmentation + probe annotations, Napari)
For each registered subject folder created by Phase 1:
1. Open the subject in `napari` using your brainrender/segmentation workflow.
2. Add probe tracks/injections.
3. Save back into the subject's `segmentation/` folder in the locations
   expected by the Python visualizers:
   - `segmentation/atlas_space/tracks/*.npy`
   - optional `segmentation/atlas_space/regions/*.obj`

## Phase 3 (Visualization, Python)
From the `workflows` repo root (so the `bg_viz_pipeline/` package is
importable):

Detailed usage: [`scripts/README.md`](scripts/README.md)  
Preset JSON reference: [`presets/README.md`](presets/README.md)

1. **Interactive atlas explorer** (slice / camera / pose experiments):
   ```bash
   python -m bg_viz_pipeline.scripts.render_atlas
   ```
   Edit the config block at the top of `scripts/render_atlas.py`.

2. **Probe HTML:**
   ```bash
   python -m bg_viz_pipeline.scripts.probes_to_html <atlas> <brainreg_dir> <out.html> [--regions ...]
   ```

3. **Batch atlas + probe PNGs** — edit `presets/viewer_presets.json`, then:
   ```bash
   python -m bg_viz_pipeline.scripts.brainreg_viewer              # all presets
   python -m bg_viz_pipeline.scripts.brainreg_viewer --only-subject ROI-1
   python -m bg_viz_pipeline.scripts.brainreg_viewer --only-subdir ds_MPX-R-0033_...
   ```

Use a conda environment with BrainGlobe installed
(e.g. `brainglobe-env`; `pip install brainglobe`).