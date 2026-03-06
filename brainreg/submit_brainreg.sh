#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/brainreg_config.sh"

mkdir -p "${OUT_ROOT}"


module purge
module load brainglobe/2025-07-06

echo "Ensuring atlas is installed: ${ATLAS}"
python - <<PY
from brainglobe_atlasapi import BrainGlobeAtlas
BrainGlobeAtlas("${ATLAS}")
print("Atlas ready: ${ATLAS}")
PY


> "${LIST_FILE}"

while IFS= read -r f; do
    base="$(basename "$f")"
    stem="${base%.*}"

    if [[ -f "${OUT_ROOT}/${stem}/registered_atlas.tiff" ]]; then
        echo "SKIP existing: $stem"
    else
        echo "$f" >> "${LIST_FILE}"
    fi
done < <(
    find "${IN_ROOT}" -type f \( -iname "*.tif" -o -iname "*.tiff" \) | sort
)

N=$(wc -l < "${LIST_FILE}")

echo "Atlas: ${ATLAS}"
echo "Output root: ${OUT_ROOT}"
echo "Submitting ${N} registrations"

if [[ "${N}" -gt 0 ]]; then
    sbatch --array=1-"${N}" "${SCRIPT_DIR}/sbatch_brainreg_use_cases.sh"
else
    echo "Nothing to do."
fi
