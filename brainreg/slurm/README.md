# brainreg/slurm

SLURM scripts for **Phase 1: registration** with `brainreg`.

## What this does (Phase 1)
For every input image under `PROJECT_DIR/data/`, the SLURM array runs `brainreg` and writes results under:
- `PROJECT_DIR/brainreg_outputs_<atlas>/`

Each subject output is expected to contain (among other files):
- `registered_atlas.tiff`
- an atlas-aligned folder structure that later drives segmentation + visualization.

## Script map
```
brainreg_config.sh
       │
       │  Defines PROJECT_DIR, DATA_DIR, LIST_FILE, OUTPUT_DIR, ATLAS, and all
       │  brainreg parameters. No execution; only sourced by the other two.
       │
       ├──────────────────────────────────────────────────────────────────┐
       │                                                                  │
       ▼                                                                  ▼
submit_brainreg.sh                                          sbatch_brainreg_use_cases.sh
       │                                                                  │
       │  1. Loads config from the script directory and finds inputs      │  Run by SLURM as array job
       │  2. Loads brainglobe module + ensures atlas is available         │
       │  3. Finds all .tif/.tiff under DATA_DIR                          │  3. Runs brainreg for that image
       │  4. Skips images that already have registered_atlas.tiff         │     into OUTPUT_DIR/<stem>/
       │  5. Writes remaining paths to LIST_FILE (one per line)           │
       │  6. cd to script dir and submits sbatch --array=1-N              │
       │                                                                  │
```

## Inputs and outputs
- Inputs: `PROJECT_DIR/data/**/*.tif` and `PROJECT_DIR/data/**/*.tiff`
- Job list: `PROJECT_DIR/brainreg_filelist.txt` (written by `submit_brainreg.sh`)
- Outputs: `PROJECT_DIR/brainreg_outputs_<atlas>/<stem>/...`

## How to use
1. Create a project folder where your **data + output live together**, and copy/symlink this `slurm/` folder into it.
   - Example expected paths after copying:
     - `project/data/...`
     - `project/brainreg_outputs_<atlas>/...`
2. Edit:
   - `slurm/brainreg_config.sh`
   - set `PROJECT_DIR` to your project folder
3. Run:
   - `./slurm/submit_brainreg.sh`

### Notes
- `submit_brainreg.sh` uses the script directory to source `brainreg_config.sh`, so the config must remain alongside these SLURM scripts.
- `sbatch_brainreg_use_cases.sh` uses `SLURM_SUBMIT_DIR` (the directory you `sbatch` from) to source the same config.

