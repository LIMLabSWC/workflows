#!/usr/bin/env bash
#------------------------------------------------------------------------------
# rat_build_template_25um.sh
#
# Purpose
# -------
# Runs modelbuild.sh inside a specific template working directory.
#
# What this script does
# ---------------------
# - Parses CLI args: atlas dir, template name, average type
# - cd into the template working directory (templates/<template-name>)
# - Validates presence of expected input list files:
#     brain_paths_flipped_res-25um.txt
#     mask_paths_flipped_res-25um.txt
# - Redirects stdout/stderr to a timestamped log file (via tee)
# - Calls modelbuild.sh with:
#     stages: rigid, similarity, affine, nlin
#     max walltimes: 240h each (10 days)
#
# Important logging note
# ----------------------
# The log produced here captures output from:
#   - this script
#   - modelbuild.sh job-generation/submission
#
# The long-running registration progress will typically appear in the SLURM
# output logs of the submitted jobs (job IDs printed by modelbuild.sh/QBatch).
#------------------------------------------------------------------------------

set -euo pipefail

start_time=$(date +%s)

#------------------------------------------------------------------------------
# 1) DEFAULTS
#------------------------------------------------------------------------------
average_type="mean"

#------------------------------------------------------------------------------
# 2) USAGE / HELP
#------------------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $0 --atlas-dir <path> --template-name <string> [--average-type <string>]

Options:
  --atlas-dir <path>       Path to the atlas-forge directory [REQUIRED]
  --template-name <string> Subfolder within templates/ (e.g., swc_female_rat_template_res-25um_n-15) [REQUIRED]
  --average-type <string>  mean|trimmed_mean|efficient_trimean (default: mean)
  --help                   Show this help
EOF
  exit 1
}

[[ "${1:-}" == "--help" ]] && usage

#------------------------------------------------------------------------------
# 3) ARGUMENT PARSING
#------------------------------------------------------------------------------
atlas_dir=""
template_name=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --atlas-dir)      atlas_dir="$2"; shift 2 ;;
    --template-name)  template_name="$2"; shift 2 ;;
    --average-type)   average_type="$2"; shift 2 ;;
    --help)           usage ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      ;;
  esac
done

if [[ -z "$atlas_dir" || -z "$template_name" ]]; then
  echo "Error: --atlas-dir and --template-name are required." >&2
  usage
fi

echo "atlas-dir: ${atlas_dir}"
echo "template-name: ${template_name}"
echo "average-type: ${average_type}"

#------------------------------------------------------------------------------
# 4) RESOLVE WORKING DIRECTORY
#
# Convention:
#   atlas-forge root: <atlas_dir>
#   templates live in: <atlas_dir>/templates
#   template working dir: <atlas_dir>/templates/<template_name>
#------------------------------------------------------------------------------
templates_dir="${atlas_dir}/templates"
working_dir="${templates_dir}/${template_name}"

if [[ ! -d "$working_dir" ]]; then
  echo "ERROR: Working directory does not exist: ${working_dir}" >&2
  exit 1
fi

cd "$working_dir"
echo "Working directory: ${working_dir}"

#------------------------------------------------------------------------------
# 5) AVERAGING PROGRAM SELECTION
#
# average_type controls how the "average template" is formed each iteration.
# Some averaging modes are implemented in ANTs tools, others via python helpers.
#
# Logic (unchanged):
# - mean => average_prog="ANTs"
# - trimmed_mean or efficient_trimean => average_prog="python"
#------------------------------------------------------------------------------
average_prog="ANTs"
if [[ "$average_type" == "trimmed_mean" || "$average_type" == "efficient_trimean" ]]; then
  average_prog="python"
fi
echo "average-prog: ${average_prog}"

#------------------------------------------------------------------------------
# 6) INPUT LIST FILES
#
# These files are lists of images/masks (one path per line) used by modelbuild.sh.
# Naming is project-convention specific.
#------------------------------------------------------------------------------
brain_list="${working_dir}/brain_paths_flipped_res-25um.txt"
mask_list="${working_dir}/mask_paths_flipped_res-25um.txt"

if [[ ! -f "$brain_list" ]]; then
  echo "ERROR: Missing brain list: ${brain_list}" >&2
  exit 2
fi
if [[ ! -f "$mask_list" ]]; then
  echo "ERROR: Missing mask list: ${mask_list}" >&2
  exit 2
fi

#------------------------------------------------------------------------------
# 7) LOGGING SETUP
#
# This redirects all subsequent stdout/stderr to BOTH:
#   - terminal
#   - a timestamped log file in the working directory
#
# Important: this captures the dispatcher output. The actual long-running work
# happens in SLURM jobs submitted by modelbuild.sh/QBatch, which have separate
# SLURM output files.
#------------------------------------------------------------------------------
log_file="${working_dir}/rat_build_template.$(date +%Y%m%d_%H%M%S).log"
echo "Logging to: ${log_file}"
exec > >(tee -a "$log_file") 2>&1

echo "[$(date)] Starting modelbuild..."

#------------------------------------------------------------------------------
# 8) MODELBUILD EXECUTION
#
# Stages:
#   rigid      -> coarse alignment
#   similarity -> adds scale (often)
#   affine     -> full affine alignment
#   nlin       -> nonlinear deformable registration
#
# Walltime parameters:
#   These are passed to modelbuild.sh so it can request appropriate times for
#   the jobs it submits (often via QBatch).
#
# Partition max is 10 days => 240 hours.
# Here all stage walltimes are set to 240 hours (unchanged from your script).
#------------------------------------------------------------------------------
bash modelbuild.sh \
  --output-dir "$working_dir" \
  --starting-target first \
  --stages rigid,similarity,affine,nlin \
  --masks "$mask_list" \
  --average-type "$average_type" \
  --average-prog "$average_prog" \
  --reuse-affines \
  --walltime-short "240:00:00" \
  --walltime-linear "240:00:00" \
  --walltime-nonlinear "240:00:00" \
  --no-dry-run \
  "$brain_list"

echo "[$(date)] Finished building the template!"

#------------------------------------------------------------------------------
# 9) WRITE EXECUTION TIME
#
# This measures how long THIS SCRIPT ran (i.e., dispatcher runtime).
# It does not necessarily equal the full end-to-end cluster runtime, because
# the heavy work continues in the submitted SLURM jobs after this script exits.
#------------------------------------------------------------------------------
end_time=$(date +%s)
execution_time=$((end_time - start_time))
hours=$((execution_time / 3600))
minutes=$(((execution_time % 3600) / 60))
formatted_time=$(printf "%02d:%02d" "$hours" "$minutes")

echo "Execution time: $formatted_time" | tee "${working_dir}/execution_time.txt"
