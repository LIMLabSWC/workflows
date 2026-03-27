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
# Load brainglobe and ensure atlas is available (so we fail fast if not)
# ------------------------------------------------------------------------------
module purge
module load brainglobe/2025-07-06

echo "Ensuring atlas is installed: ${ATLAS}"
python - <<PY
from brainglobe_atlasapi import BrainGlobeAtlas
BrainGlobeAtlas("${ATLAS}")
print("Atlas ready: ${ATLAS}")
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

