#!/usr/bin/env bash
#------------------------------------------------------------------------------
# slurm_wrapper_rat_template_25um.sh
#
# Purpose
# -------
# A lightweight SLURM "wrapper" job that:
#   1) Loads the template-builder environment/module
#   2) Configures QBatch defaults (so modelbuild.sh submits SLURM jobs correctly)
#   3) Calls the actual build script (rat_build_template_25um.sh)
#
# What this wrapper is NOT
# ------------------------
# This wrapper does not perform the registrations itself.
# It only submits the registration jobs (via modelbuild.sh/QBatch) and exits.
# The real work happens in the SLURM jobs that get submitted (separate job IDs).
#
# Maxed settings
# -------------
# - Wrapper job runtime: 10 days (SLURM -t)
# - QBatch-submitted jobs runtime: 10 days (QBATCH_OPTIONS --time)
#
# How to submit
# -------------
#   sbatch slurm_wrapper_rat_template_25um.sh
#
# How to override parameters at submit-time (examples)
# ---------------------------------------------------
#   sbatch --export=ALL,TEMP_NAME=...,AVE_TYPE=... slurm_wrapper_rat_template_25um.sh
#   sbatch --export=ALL,ATLAS_DIR=...,SPECIES=... slurm_wrapper_rat_template_25um.sh
#
# Notes on logging
# ----------------
# This wrapper logs only wrapper-level actions (module load, parameter echoing,
# calling the build script). Progress of actual ANTs stages will appear in the
# SLURM output of the submitted jobs, not necessarily in this wrapper's log.
#------------------------------------------------------------------------------

#SBATCH -J rat_template_25um
#SBATCH -p cpu
#SBATCH -N 1
#SBATCH --mem=16G
#SBATCH -n 2
#SBATCH -t 10-00:00:00
#SBATCH -o slurm.%x.%N.%j.out
#SBATCH -e slurm.%x.%N.%j.err
#SBATCH --mail-type=FAIL
#SBATCH --mail-user=v.plattner@ucl.ac.uk

set -euo pipefail

echo "[$(date)] Wrapper started on $(hostname), SLURM job $SLURM_JOB_ID"

#------------------------------------------------------------------------------
# 1) ENVIRONMENT
#
# Loads the software stack needed for modelbuild.sh / ANTs / helper scripts.
# (Exact module path is site-specific.)
#------------------------------------------------------------------------------
module use /ceph/neuroinformatics/neuroinformatics/modules/modulefiles
module load template-builder/temp-2024-12-02
echo "[$(date)] Loaded template-builder module"

#------------------------------------------------------------------------------
# 2) PARTITION INFO (INFO ONLY)
#
# Prints the partition max walltime into the wrapper log.
# This does not affect scheduling; it is just a sanity check in logs.
#------------------------------------------------------------------------------
echo "[$(date)] Partition max walltime (cpu): $(scontrol show partition cpu | awk -F= '/MaxTime=/{print $2}' | head -n1)"

#------------------------------------------------------------------------------
# 3) QBATCH CONFIGURATION
#
# QBatch is a helper that submits many jobs to a scheduler (here: SLURM).
# modelbuild.sh uses QBatch to fan out work into many SLURM jobs.
#
# IMPORTANT CONCEPTS
# ------------------
# - QBatch itself is not the scheduler; SLURM is.
# - QBatch reads environment variables (QBATCH_*) to decide how to submit jobs.
# - These variables affect how many jobs are created, what resources they request,
#   and where they are submitted.
#
# In short: these settings control the *shape* of the job graph and job requests.
#------------------------------------------------------------------------------
export QBATCH_SYSTEM="slurm"
export QBATCH_QUEUE="cpu"

#------------------------------------------------------------------------------
# 3a) Job packing / parallelism controls
#
# QBATCH_PPJ (jobs per node, as seen by QBatch)
#   - Controls how many independent jobs QBatch *tries* to pack into a single node
#     allocation.
#   - Here we use PPJ=1 because each job already requests so much RAM (270G) that
#     in practice it "owns" a whole big‑mem node; extra PPJ would not actually fit.
#
# QBATCH_CORES
#   - How many CPU cores each QBatch-submitted job requests/assumes.
#   - This is passed through to SLURM as --cpus-per-task and to ANTs via
#     OMP_NUM_THREADS / ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS / MKL_NUM_THREADS.
#   - Setting this high (e.g. 24 on enc3 big‑mem nodes) makes each registration
#     multi-threaded and uses all CPUs on the node you already paid for in RAM.
#
# QBATCH_CHUNKSIZE
#   - Controls how many "units of work" are grouped into one submitted job.
#   - Larger chunksize => fewer (bigger) jobs.
#   - Smaller chunksize => more (smaller) jobs.
#   - This affects:
#       (a) how many SLURM jobs you create (submission limits risk),
#       (b) runtime per job (timeout risk if too big),
#       (c) overhead (many small jobs increases overhead).
#
# CHUNKSIZE 1 = one unit of work per submitted job (max granularity).
#------------------------------------------------------------------------------
export QBATCH_PPJ=1
export QBATCH_CORES=24
export QBATCH_CHUNKSIZE=1

#------------------------------------------------------------------------------
# 3b) Resource requests for each QBatch-submitted job
#
# QBATCH_MEM
#   - Memory request per submitted job (string). QBatch uses this to size jobs.
#
# QBATCH_OPTIONS
#   - Literal additional options appended to the sbatch command.
#   - Here:
#       --mem=270G requests 270GB RAM per job
#       --time=10-00:00:00 requests 10 days walltime per job
#
# NOTE ON EMAIL
#   - This wrapper has email via #SBATCH --mail-type=FAIL.
#   - QBATCH_OPTIONS also passes --mail-type=FAIL so sub-job failures are mailed.
#------------------------------------------------------------------------------
QBATCH_MEM_DEFAULT="270G"
QBATCH_MEM="${QBATCH_MEM:-$QBATCH_MEM_DEFAULT}"
export QBATCH_MEM
export QBATCH_OPTIONS="--cpus-per-task=${QBATCH_CORES} --mem=${QBATCH_MEM} --time=10-00:00:00 \
--export=ALL,OMP_NUM_THREADS=${QBATCH_CORES},ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=${QBATCH_CORES},MKL_NUM_THREADS=${QBATCH_CORES} \
--mail-type=FAIL --mail-user=v.plattner@ucl.ac.uk"


echo "[$(date)] QBatch settings:"
echo "  SYSTEM=${QBATCH_SYSTEM}"
echo "  QUEUE=${QBATCH_QUEUE}"
echo "  PPJ=${QBATCH_PPJ}"
echo "  CORES=${QBATCH_CORES}"
echo "  CHUNKSIZE=${QBATCH_CHUNKSIZE}"
echo "  MEM=${QBATCH_MEM}"
echo "  OPTIONS=${QBATCH_OPTIONS}"

#------------------------------------------------------------------------------
# 4) TEMPLATE BUILDER PARAMETERS
#
# These defaults describe where your atlas-forge project lives and which
# template subfolder to build.
#
# You can override any of these at submission time via:
#   sbatch --export=ALL,VAR=value ...
#
# The wrapper resolves:
#   atlas dir:   ${ATLAS_DIR}/${SPECIES}
#   build script ${ATLAS_DIR}/${SPECIES}/scripts/rat_build_template_25um.sh
#------------------------------------------------------------------------------
ATLAS_DIR_DEFAULT="/ceph/akrami/_projects"
SPECIES_DEFAULT="rat_atlas"
TEMP_NAME_DEFAULT="swc_female_rat_template_res-25um_n-15"
AVE_TYPE_DEFAULT="efficient_trimean"

# Allow overrides via environment (sbatch --export=ALL,...)
ATLAS_DIR="${ATLAS_DIR:-$ATLAS_DIR_DEFAULT}"
SPECIES="${SPECIES:-$SPECIES_DEFAULT}"
TEMP_NAME="${TEMP_NAME:-$TEMP_NAME_DEFAULT}"
AVE_TYPE="${AVE_TYPE:-$AVE_TYPE_DEFAULT}"

#------------------------------------------------------------------------------
# 5) BUILD SCRIPT RESOLUTION
#
# BUILD_SCRIPT is the path to rat_build_template_25um.sh. Default:
#   <atlas_dir>/<species>/scripts/rat_build_template_25um.sh
# Keep both scripts together (or symlink); override BUILD_SCRIPT if needed.
#------------------------------------------------------------------------------
BUILD_SCRIPT_DEFAULT="${ATLAS_DIR}/${SPECIES}/scripts/rat_build_template_25um.sh"
BUILD_SCRIPT="${BUILD_SCRIPT:-$BUILD_SCRIPT_DEFAULT}"

echo "[$(date)] Using:"
echo "  ATLAS_DIR   = ${ATLAS_DIR}"
echo "  SPECIES     = ${SPECIES}"
echo "  TEMPLATE    = ${TEMP_NAME}"
echo "  AVERAGE     = ${AVE_TYPE}"
echo "  BUILD_SCRIPT= ${BUILD_SCRIPT}"

if [[ ! -f "$BUILD_SCRIPT" ]]; then
  echo "ERROR: BUILD_SCRIPT does not exist: $BUILD_SCRIPT" >&2
  exit 1
fi

#------------------------------------------------------------------------------
# 6) RUN TEMPLATE BUILD (DISPATCH JOBS)
#
# This calls the build script, which in turn calls modelbuild.sh.
# modelbuild.sh typically:
#   - checks inputs
#   - generates job scripts / dependency graph
#   - submits many SLURM jobs via QBatch
#   - exits (submission success != template completion)
#------------------------------------------------------------------------------
bash "$BUILD_SCRIPT" \
  --atlas-dir "${ATLAS_DIR}/${SPECIES}" \
  --template-name "$TEMP_NAME" \
  --average-type "$AVE_TYPE"

status=$?
echo "[$(date)] Build script exited with status ${status}"
exit ${status}
