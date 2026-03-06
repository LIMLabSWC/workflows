#!/usr/bin/env bash

ROOT="${HOME}/brainglobe_workingdir/use_cases_for_paper"
IN_ROOT="${ROOT}/data"
LIST_FILE="${ROOT}/brainreg_filelist.txt"

ATLAS="whs_sd_swc_female_rat_39um"
OUT_ROOT="${ROOT}/brainreg_outputs_${ATLAS}"

BACKEND="niftyreg"
ORIENTATION="psl"

VOXEL_SIZES=("25" "25" "25")

AFFINE_N_STEPS=6
AFFINE_USE_N_STEPS=6
FREEFORM_N_STEPS=6
FREEFORM_USE_N_STEPS=5

BENDING_ENERGY_WEIGHT="0.45"
GRID_SPACING=4

SMOOTHING_SIGMA_REF="0.5"
SMOOTHING_SIGMA_FLOAT="0.7"

HIST_N_BINS_FLOAT=128
HIST_N_BINS_REF=128

SAVE_ORIG_ORIENTATION=(--save-original-orientation)
N_FREE_CPUS=2
