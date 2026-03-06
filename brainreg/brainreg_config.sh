#!/usr/bin/env bash
#
# Shared config for the brainreg workflow. Sourced by submit_brainreg.sh
# and sbatch_brainreg_use_cases.sh. Edit PROJECT_DIR and atlas/params for your run.
#

# ------------------------------------------------------------------------------
# Paths (all under PROJECT_DIR; scripts + data + output live in the same folder)
# ------------------------------------------------------------------------------
PROJECT_DIR="${HOME}/brainglobe_workingdir/use_cases_for_paper"
DATA_DIR="${PROJECT_DIR}/data"
LIST_FILE="${PROJECT_DIR}/brainreg_filelist.txt"

# ------------------------------------------------------------------------------
# Atlas and output directory
# ------------------------------------------------------------------------------
ATLAS="whs_sd_swc_female_rat_39um"
OUTPUT_DIR="${PROJECT_DIR}/brainreg_outputs_${ATLAS}"

# ------------------------------------------------------------------------------
# Backend and orientation
# ------------------------------------------------------------------------------
BACKEND="niftyreg"
ORIENTATION="psl"

# ------------------------------------------------------------------------------
# Voxel sizes (µm)
# ------------------------------------------------------------------------------
VOXEL_SIZES=("25" "25" "25")

# ------------------------------------------------------------------------------
# Registration steps (affine and freeform)
# ------------------------------------------------------------------------------
AFFINE_N_STEPS=6
AFFINE_USE_N_STEPS=6
FREEFORM_N_STEPS=6
FREEFORM_USE_N_STEPS=5

# ------------------------------------------------------------------------------
# Freeform / bending energy
# ------------------------------------------------------------------------------
BENDING_ENERGY_WEIGHT="0.45"
GRID_SPACING=4

# ------------------------------------------------------------------------------
# Smoothing (reference and floating images)
# ------------------------------------------------------------------------------
SMOOTHING_SIGMA_REF="0.5"
SMOOTHING_SIGMA_FLOAT="0.7"

# ------------------------------------------------------------------------------
# Histogram bins for registration
# ------------------------------------------------------------------------------
HIST_N_BINS_FLOAT=128
HIST_N_BINS_REF=128

# ------------------------------------------------------------------------------
# Other options
# ------------------------------------------------------------------------------
SAVE_ORIG_ORIENTATION=(--save-original-orientation)
N_FREE_CPUS=2
