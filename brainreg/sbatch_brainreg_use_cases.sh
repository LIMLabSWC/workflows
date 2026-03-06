#!/usr/bin/env bash
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --cpus-per-task=2
#SBATCH --mem=40G
#SBATCH -t 1-00:00:00
#SBATCH -o slurm.%x.%N.%A_%a.out
#SBATCH -e slurm.%x.%N.%A_%a.err
#SBATCH --job-name=brainreg_uc

set -euo pipefail

echo "HOST: $(hostname)"
echo "START: $(date -Is)"

SUBMIT_DIR="${SLURM_SUBMIT_DIR:?SLURM_SUBMIT_DIR not set}"
source "${SUBMIT_DIR}/brainreg_config.sh"

mkdir -p "${OUT_ROOT}"

module purge
module load brainglobe/2025-07-06

command -v brainreg >/dev/null || {
    echo "ERROR: brainreg not found"
    exit 1
}

TASK_ID="${SLURM_ARRAY_TASK_ID}"
IMG_PATH="$(sed -n "${TASK_ID}p" "${LIST_FILE}")"

if [[ -z "${IMG_PATH}" ]]; then
    echo "ERROR: no file for task ${TASK_ID}"
    exit 1
fi

IMG_BASENAME="$(basename "${IMG_PATH}")"
IMG_STEM="${IMG_BASENAME%.*}"
OUT_DIR="${OUT_ROOT}/${IMG_STEM}"
mkdir -p "${OUT_DIR}"

echo "------------------------------------------------------------"
echo "TASK:     ${TASK_ID}"
echo "ATLAS:    ${ATLAS}"
echo "INPUT:    ${IMG_PATH}"
echo "OUTPUT:   ${OUT_DIR}"
echo "------------------------------------------------------------"

set -x

brainreg \
  "${IMG_PATH}" \
  "${OUT_DIR}" \
  --atlas "${ATLAS}" \
  --backend "${BACKEND}" \
  --voxel-sizes "${VOXEL_SIZES[0]}" "${VOXEL_SIZES[1]}" "${VOXEL_SIZES[2]}" \
  --orientation "${ORIENTATION}" \
  --affine-n-steps "${AFFINE_N_STEPS}" \
  --affine-use-n-steps "${AFFINE_USE_N_STEPS}" \
  --freeform-n-steps "${FREEFORM_N_STEPS}" \
  --freeform-use-n-steps "${FREEFORM_USE_N_STEPS}" \
  --grid-spacing "${GRID_SPACING}" \
  --bending-energy-weight "${BENDING_ENERGY_WEIGHT}" \
  --smoothing-sigma-r "${SMOOTHING_SIGMA_REF}" \
  --smoothing-sigma-f "${SMOOTHING_SIGMA_FLOAT}" \
  --histogram-n-bins-r "${HIST_N_BINS_REF}" \
  --histogram-n-bins-f "${HIST_N_BINS_FLOAT}" \
  "${SAVE_ORIG_ORIENTATION[@]}" \
  --n-free-cpus "${N_FREE_CPUS}"

set +x

echo "DONE: ${IMG_PATH}"
echo "END:  $(date -Is)"
