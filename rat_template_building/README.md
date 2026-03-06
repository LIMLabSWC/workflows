# rat_template_building

SLURM workflow for building a 25 µm rat brain template with modelbuild.sh (ANTs, QBatch).

## Contents

- **rat_build_template_25um.sh** — Build driver: parses args, `cd`s into the template working dir, checks list files, runs `modelbuild.sh` (rigid → similarity → affine → nlin) with 10‑day walltimes. Logs to a timestamped file in the working dir.
- **slurm_wrapper_rat_template_25um.sh** — SLURM wrapper: loads the template-builder module, sets QBatch env vars, then runs the build script. Does not run registrations itself; it submits the jobs and exits.

## Layout

- Atlas-forge root: `<atlas_dir>` (e.g. `ATLAS_DIR/SPECIES`).
- Templates: `<atlas_dir>/templates/<template_name>`.
- Each template dir must contain:
  - `brain_paths_flipped_res-25um.txt`
  - `mask_paths_flipped_res-25um.txt`
  - `modelbuild.sh` (from your atlas-forge/template-builder setup).

## Running

1. **Deploy scripts**  
   Copy or symlink both scripts to the same location (or where the wrapper can find the build script). The wrapper’s default `BUILD_SCRIPT` is `<atlas_dir>/<species>/scripts/rat_build_template_25um.sh`. If you put them elsewhere, override at submit time:  
   `sbatch --export=ALL,BUILD_SCRIPT=/path/to/rat_build_template_25um.sh slurm_wrapper_rat_template_25um.sh`

2. **Submit the wrapper** (from the directory that contains the wrapper, or use an absolute path):
   ```bash
   sbatch slurm_wrapper_rat_template_25um.sh
   ```

3. **Override defaults** (optional):
   ```bash
   sbatch --export=ALL,ATLAS_DIR=/path,SPECIES=rat_atlas,TEMP_NAME=swc_female_rat_template_res-25um_n-15,AVE_TYPE=efficient_trimean slurm_wrapper_rat_template_25um.sh
   ```

## Dependencies

- SLURM, QBatch, and a `template-builder` module (or equivalent) providing `modelbuild.sh` and ANTs. Module path and defaults in the wrapper are site-specific (e.g. UCL Neuroinformatics).
