# `bg_viz_pipeline/slurm`

SLURM helper scripts for **Phase 1: registration** with `brainreg`.

## Start Here

Run the workflow with:

```bash
./slurm/submit_brainreg.sh
```

Do **not** start it with:

```bash
sbatch ./slurm/submit_brainreg.sh
```

`submit_brainreg.sh` is a **submitter** script, not the actual compute job. Its job is to prepare the input list and then call `sbatch` itself for the real array job.

## What the workflow does

For every input image under `PROJECT_DIR/data/`, the SLURM array runs `brainreg` and writes results under:

- `PROJECT_DIR/brainreg_outputs_<atlas>/`

Each subject output is expected to contain, among other files:

- `registered_atlas.tiff`
- atlas-aligned outputs used by later segmentation and visualization steps

## The three scripts

```text
brainreg_config.sh
    Shared configuration only.
    Defines PROJECT_DIR, DATA_DIR, LIST_FILE, OUTPUT_DIR, ATLAS,
    and all brainreg parameters.

submit_brainreg.sh
    Run this manually from the shell.
    1. Loads the config
    2. Loads the brainglobe module
    3. After module load, points BrainGlobe at BRAINGLOBE_DIR (~/.brainglobe)
    4. Checks that directory for <ATLAS>_v*
    5. Scans DATA_DIR for .tif/.tiff files
    6. Skips samples that already have registered_atlas.tiff
    7. Writes the remaining inputs to LIST_FILE
    8. Calls sbatch to launch the SLURM array job

sbatch_brainreg_use_cases.sh
    Run by SLURM, not by hand.
    1. Reads one input path from LIST_FILE using SLURM_ARRAY_TASK_ID
    2. Creates that sample's output directory
    3. Runs brainreg for that one sample
```

## Inputs and outputs

- Inputs: `PROJECT_DIR/data/**/*.tif` and `PROJECT_DIR/data/**/*.tiff`
- Symlinked `.tif` and `.tiff` inputs under `data/` are also followed and included
- Job list written by the submitter: `PROJECT_DIR/brainreg_filelist.txt`
- Outputs: `PROJECT_DIR/brainreg_outputs_<atlas>/<stem>/...`

## Expected layout

Create a project folder where the data and outputs live together, then copy or symlink this `slurm/` folder into it.

Example:

```text
project/
├── data/
├── brainreg_outputs_<atlas>/
└── slurm/
    ├── brainreg_config.sh
    ├── submit_brainreg.sh
    └── sbatch_brainreg_use_cases.sh
```

## Atlases are local only

The submitter **does not download** an atlas. The previous `BrainGlobeAtlas("${ATLAS}")` check was meant to fetch a missing catalogue atlas from gin; on HPC login nodes that HTTP call has no timeout and hangs, and custom atlases are not in the catalogue anyway. The submitter only lists `BRAINGLOBE_DIR/<ATLAS>_v*` and exits if the folder is missing.

Before you submit:

1. Set `ATLAS` in `brainreg_config.sh` to the BrainGlobe name **without** the `_v*` suffix.
2. Make sure `BRAINGLOBE_DIR/<ATLAS>_v<version>/` already exists (default `BRAINGLOBE_DIR` is `~/.brainglobe`). Custom and catalogue atlases use the same layout.

To add a catalogue atlas, copy it from the module cache or install it on a machine that can reach gin, then copy the folder in:

```bash
# shared HPC catalogue (read-only examples)
# /ceph/apps/application_data/brainglobe/<ATLAS>_v*/

cp -a /ceph/apps/application_data/brainglobe/<ATLAS>_v<version> ~/.brainglobe/
# or, off-cluster:  brainglobe install -a <ATLAS>
# then copy ~/.brainglobe/<ATLAS>_v* onto the cluster
```

`module load brainglobe` points BrainGlobe at `/ceph/apps/application_data/brainglobe`. Both the submitter and the array job then call `apply_user_brainglobe_dir` so `brainreg` sees `BRAINGLOBE_DIR` (your custom atlases) instead of only the shared cache.

## How to use

1. Put this `slurm/` folder inside your project folder, or symlink it there.
2. Edit `slurm/brainreg_config.sh`.
3. Set `PROJECT_DIR` to your project folder.
4. Set `ATLAS` and install that atlas under `BRAINGLOBE_DIR` (see above).
5. Submit the workflow by running `./slurm/submit_brainreg.sh`.
6. Monitor the generated SLURM output/error files as usual.

## Common mistake

If you run:

```bash
sbatch ./slurm/submit_brainreg.sh
```

you are asking SLURM to schedule the **submitter** itself. That is not how this workflow is designed to be launched, and it can break how the config file is found.

Use:

```bash
./slurm/submit_brainreg.sh
```

instead.

## Notes

- Keep `brainreg_config.sh`, `submit_brainreg.sh`, and `sbatch_brainreg_use_cases.sh` together.
- `submit_brainreg.sh` sources `brainreg_config.sh` from its own directory.
- `sbatch_brainreg_use_cases.sh` is intended to be launched by `submit_brainreg.sh`, not directly.

