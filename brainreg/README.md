# brainreg

Brain registration (brainreg) and probe visualization for use-case / paper workflows.

## Script map (how the three bash scripts work together)

```
brainreg_config.sh
       │
       │  Defines PROJECT_DIR, DATA_DIR, LIST_FILE, OUTPUT_DIR, ATLAS, and all
       │  brainreg parameters. No execution; only sourced by the other two.
       │
       ├──────────────────────────────────────────────────────────────────┐
       │                                                                  │
       ▼                                                                  ▼
submit_brainreg.sh                                              sbatch_brainreg_use_cases.sh
       │                                                                  │
       │  1. Sources config from SCRIPT_DIR (directory of submit script)  │  Run by SLURM as array job
       │  2. Loads brainglobe module, checks atlas                         │  (one process per image).
       │  3. Finds all .tif/.tiff under DATA_DIR                            │
       │  4. Skips images that already have OUTPUT_DIR/<stem>/registered_  │  1. Sources config from
       │     atlas.tiff                                                   │     SLURM_SUBMIT_DIR (must be
       │  5. Writes remaining paths to LIST_FILE (one per line)           │     the script dir; submit_brainreg
       │  6. cd to SCRIPT_DIR, then sbatch --array=1-N ./sbatch_...       │     does "cd SCRIPT_DIR" before
       │     so SLURM_SUBMIT_DIR = script dir                             │     sbatch to ensure this).
       │                                                                  │  2. Reads line SLURM_ARRAY_TASK_ID
       └─────────────────────────────────────────────────────────────────►│     from LIST_FILE → input image
             Submits array job; each task runs sbatch_brainreg_use_cases   │  3. Runs brainreg for that image
             and sources config from SUBMIT_DIR to get LIST_FILE, etc.    │     into OUTPUT_DIR/<stem>/
```

**Summary:** You run only `submit_brainreg.sh`. It uses `brainreg_config.sh` for paths and parameters, builds the list of images to process, and submits an array of `sbatch_brainreg_use_cases.sh` jobs. Each job sources the same config from the submit directory and processes one image.

## Layout: one project folder

Scripts, data, and output live in the **same folder** (e.g. your NFS project dir). Set `PROJECT_DIR` in `brainreg_config.sh` to that folder. The config then uses:

- `PROJECT_DIR/data` — input TIFs (any subdirs)
- `PROJECT_DIR/brainreg_filelist.txt` — job list (written by submit script)
- `PROJECT_DIR/brainreg_outputs_<atlas>/` — registration outputs

Copy or symlink the three bash scripts (and optionally `visualize_probe.py`) into that folder. You can run `submit_brainreg.sh` from any working directory; it will `cd` to the script directory before submitting so the SLURM job finds the config.

## Contents

- **brainreg_config.sh** — Set `PROJECT_DIR` (project dir), atlas, and brainreg parameters.
- **submit_brainreg.sh** — Scans `PROJECT_DIR/data` for TIFs, skips already-done, submits SLURM array.
- **sbatch_brainreg_use_cases.sh** — SLURM job script; runs brainreg for one image (sources config from `SLURM_SUBMIT_DIR`).
- **visualize_probe.py** — Renders probe `.npy` tracks in brainrender and exports HTML.

## Running

1. In your project folder: set `PROJECT_DIR` in `brainreg_config.sh` (e.g. `PROJECT_DIR="${HOME}/brainglobe_workingdir/use_cases_for_paper"`).
2. Run `./submit_brainreg.sh` (from the project folder or from anywhere; the script will submit from the directory where the scripts live).
3. For probe viz: `python visualize_probe.py <atlas> <tracks_dir> <out.html> [--regions ...]`.

Requires brainglobe environment (e.g. `module load brainglobe/2025-07-06`) and SLURM for the batch jobs.
