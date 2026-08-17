#!/usr/bin/env bash
#
# One-shot submitter: discovers TIFs under PROJECT_DIR/data, skips images that
# already have registered_atlas.tiff, writes the job list, and submits a
# SLURM array. Sources brainreg_config.sh; launches sbatch_brainreg_use_cases.sh
# per task. Run from anywhere; we cd to script dir before sbatch so the job
# finds the config via SLURM_SUBMIT_DIR.
#
set -euo pipefail

# ------------------------------------------------------------------------------
# Setup: find config and load shared variables
# ------------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/brainreg_config.sh"

mkdir -p "${OUTPUT_DIR}"

# ------------------------------------------------------------------------------
# Fail fast if ATLAS is not already on disk. Do not construct BrainGlobeAtlas:
# even with check_latest=False, a missing/unseen local folder still calls
# gin.g-node.org (no HTTP timeout) and hangs on cluster login nodes.
# ------------------------------------------------------------------------------
module purge
module load brainglobe/2025-07-06
apply_user_brainglobe_dir

echo "Ensuring atlas is installed locally: ${ATLAS}"
python - <<PY
from pathlib import Path
from brainglobe_atlasapi.config import read_config

name = "${ATLAS}"
root = Path(read_config()["default_dirs"]["brainglobe_dir"])
found = sorted(p.name for p in root.glob(name + "_v*") if p.is_dir())
if len(found) != 1:
    installed = sorted(p.name for p in root.glob("*_v*") if p.is_dir())
    listing = "\n  ".join(installed) if installed else "(none)"
    raise SystemExit(
        f"Atlas not found locally: {name}\n"
        f"Looked for: {root}/{name}_v*\n"
        f"Installed in {root}:\n  {listing}\n"
        "This submitter does not download atlases. Copy <ATLAS>_v* into "
        f"{root} first (see slurm/README.md)."
    )
print(f"Atlas ready: {root / found[0]}")
PY

# ------------------------------------------------------------------------------
# Build job list: one line per TIF that does not yet have registered_atlas.tiff.
# Follow symlinks so both real files and symlinked inputs under DATA_DIR are
# discovered.
# ------------------------------------------------------------------------------
> "${LIST_FILE}"

while IFS= read -r f; do
    base="$(basename "$f")"
    stem="${base%.*}"

    if [[ -f "${OUTPUT_DIR}/${stem}/registered_atlas.tiff" ]]; then
        echo "SKIP existing: $stem"
    else
        echo "$f" >> "${LIST_FILE}"
    fi
done < <(
    find -L "${DATA_DIR}" -type f \( -iname "*.tif" -o -iname "*.tiff" \) | sort
)

N=$(wc -l < "${LIST_FILE}")

echo "Atlas: ${ATLAS}"
echo "Output dir: ${OUTPUT_DIR}"
echo "Submitting ${N} registrations"

# ------------------------------------------------------------------------------
# Submit SLURM array from script directory so SLURM_SUBMIT_DIR = script dir
# and the job can source brainreg_config.sh from there
# ------------------------------------------------------------------------------
if [[ "${N}" -gt 0 ]]; then
    ( cd "${SCRIPT_DIR}" && sbatch --array=1-"${N}" ./sbatch_brainreg_use_cases.sh )
else
    echo "Nothing to do."
fi

