# brainreg

Brain registration (brainreg) and probe visualization for use-case / paper workflows.

## Contents

- **brainreg_config.sh** — Paths, atlas, and brainreg parameters (edit for your data).
- **submit_brainreg.sh** — Scans input dir for TIFs, skips already-done, submits SLURM array.
- **sbatch_brainreg_use_cases.sh** — SLURM job script; runs brainreg for one image.
- **visualize_probe.py** — Renders probe `.npy` tracks in brainrender and exports HTML.

## Running

1. Edit `brainreg_config.sh` (ROOT, ATLAS, etc.).
2. From this directory: `./submit_brainreg.sh` to submit the array.
3. For probe viz: `python visualize_probe.py <atlas> <tracks_dir> <out.html> [--regions ...]`.

Requires brainglobe environment (e.g. `module load brainglobe/2025-07-06`) and SLURM for the batch jobs.
