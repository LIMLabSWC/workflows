#!/usr/bin/env python3
"""
hpc_recommend.py
----------------

General-purpose Slurm "shape recommender" for the SWC cluster.

Goal
----
Given a job-name pattern (e.g. "modelbui", "brainreg") and a time window,
this script:

- Queries your past jobs via `sacct`
- Estimates typical / high-end memory usage
- Estimates typical CPU usage
- Suggests a safe Slurm job shape:
    --cpus-per-task=...
    --mem=...G
- Shows which node types can host that shape (based on current `sinfo`)

The recommendations are conservative:
- They use historical usage (MaxRSS, or ReqMem when MaxRSS is missing)
- They add a safety margin on top

This script is intentionally **general-purpose** and not ANTs-specific.

Usage
-----

    chmod +x hpc_tools/hpc_recommend.py

    # Look at "modelbui" jobs from last 30 days
    ./hpc_tools/hpc_recommend.py modelbui --days 30

    # Look at "brainreg" jobs from last 14 days
    ./hpc_tools/hpc_recommend.py brainreg

It assumes:
- You are on an SWC login node
- `sacct` and `sinfo` work in your environment
- You want to inspect jobs owned by the current `$USER`
"""

import argparse
import statistics
import subprocess
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional


# -----------------------------------------------------------------------------
# Shell helpers
# -----------------------------------------------------------------------------

def run(cmd: str) -> List[str]:
    """
    Run a shell command and return its stdout as a list of lines.

    The command is executed with `shell=True` since we sometimes rely on
    environment variables like $USER.
    """
    out = subprocess.check_output(cmd, shell=True, text=True)
    return out.strip().splitlines()


# -----------------------------------------------------------------------------
# Parsing utilities (memory, elapsed time)
# -----------------------------------------------------------------------------

def parse_mem(mem_str: str) -> Optional[float]:
    """
    Parse a Slurm-style memory string into gigabytes (float).

    Handles:
      - "8000K", "1024M", "64G"
      - plain numbers interpreted as MB
      - "0", "", "None" -> returns None
    """
    mem_str = (mem_str or "").strip()
    if not mem_str or mem_str in ("None", "0", "0K", "0M", "0G"):
        return None

    unit = mem_str[-1].upper()
    num_part = mem_str[:-1]

    try:
        val = float(num_part)
    except ValueError:
        return None

    if unit == "K":
        # convert KB -> GB
        return val / 1024.0 / 1024.0
    if unit == "M":
        # convert MB -> GB
        return val / 1024.0
    if unit == "G":
        # already in GB
        return val

    # No recognized unit; assume the whole string was MB
    try:
        return float(mem_str) / 1024.0
    except ValueError:
        return None


def parse_elapsed(elapsed: str) -> Optional[float]:
    """
    Parse Slurm elapsed time into hours (float).

    Handles:
      - "DD-HH:MM:SS"
      - "HH:MM:SS"
      - "00:00:00"
      - "Unknown", "NOTSET" -> None
    """
    elapsed = (elapsed or "").strip()
    if not elapsed or elapsed in ("Unknown", "NOTSET"):
        return None

    if "-" in elapsed:
        days_str, rest = elapsed.split("-")
        days = int(days_str)
    else:
        days, rest = 0, elapsed

    h_str, m_str, s_str = rest.split(":")
    h, m, s = int(h_str), int(m_str), int(s_str)
    hours = days * 24 + h + m / 60.0 + s / 3600.0
    return hours


# -----------------------------------------------------------------------------
# sacct querying and record building
# -----------------------------------------------------------------------------

def summarize_jobs(job_name: str, lookback_days: int) -> List[Dict[str, Any]]:
    """
    Query sacct for jobs matching `job_name` in the past `lookback_days` days.

    Returns a list of dicts with:
      - jobid
      - name
      - state
      - cpus
      - reqmem_g
      - maxrss_g
      - eff_mem_g  (MaxRSS if present, else ReqMem)
      - elapsed_h
    """
    since = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    cmd = (
        f"sacct -u $USER "
        f"-S {since} "
        f"-n -P "
        f'-o JobID,JobName%30,State,AllocCPUS,ReqMem,MaxRSS,Elapsed '
        f'| grep "{job_name}"'
    )

    lines = run(cmd)
    records: List[Dict[str, Any]] = []

    for line in lines:
        if not line.strip():
            continue

        parts = line.split("|")
        if len(parts) < 7:
            continue

        jobid, name, state, cpus, reqmem, maxrss, elapsed = parts[:7]

        # Skip still-running or pending jobs; they don't have final MaxRSS/Elapsed
        if state in ("RUNNING", "PENDING"):
            continue

        try:
            alloc_cpus = int(cpus)
        except ValueError:
            continue

        maxrss_g = parse_mem(maxrss)
        reqmem_g = parse_mem(reqmem)
        elapsed_h = parse_elapsed(elapsed)

        # Effective memory: prefer measured MaxRSS, fall back to requested memory
        eff_mem_g = maxrss_g if maxrss_g is not None else reqmem_g

        records.append(
            {
                "jobid": jobid,
                "name": name,
                "state": state,
                "cpus": alloc_cpus,
                "reqmem_g": reqmem_g,
                "maxrss_g": maxrss_g,
                "eff_mem_g": eff_mem_g,
                "elapsed_h": elapsed_h,
            }
        )

    return records


# -----------------------------------------------------------------------------
# Recommendation logic
# -----------------------------------------------------------------------------

def recommend_from_records(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Given job records, compute a conservative recommendation:

      - rec_cpus: suggested --cpus-per-task
      - rec_mem_g: suggested --mem (GB)

    Strategy:
      - Use effective memory (MaxRSS or ReqMem) to compute:
          * median
          * 90th percentile (if enough data)
      - Start from max(p90, median * 1.2)
      - Add another 20% buffer and round to nearest 4G
      - For CPUs, use the median but clamp to [1, 64]
    """
    if not records:
        return None

    good = [r for r in records if r["eff_mem_g"] is not None and r["cpus"] > 0]
    if not good:
        return None

    cpus_list = [r["cpus"] for r in good]
    mem_list = [r["eff_mem_g"] for r in good]

    cpus_med = int(statistics.median(cpus_list))
    mem_med = statistics.median(mem_list)

    if len(mem_list) >= 10:
        mem_p90 = statistics.quantiles(mem_list, n=10)[-1]
    else:
        mem_p90 = max(mem_list)

    # Memory recommendation: p90 plus safety, or median*1.2, whichever is larger.
    base = max(mem_p90, mem_med * 1.2)
    rec_mem = int(round(base * 1.2))  # additional 20% safety margin
    # Round to nearest 4G chunk to avoid over-granularity
    rec_mem = int(((rec_mem + 3) // 4) * 4)

    # CPU recommendation: median, clamped to a sane range
    rec_cpus = max(1, min(cpus_med, 64))

    return {
        "rec_cpus": rec_cpus,
        "rec_mem_g": rec_mem,
        "cpus_med": cpus_med,
        "mem_med": mem_med,
        "mem_p90": mem_p90,
        "n_jobs": len(good),
    }


# -----------------------------------------------------------------------------
# Node shape introspection (sinfo)
# -----------------------------------------------------------------------------

def list_node_shapes() -> List[Dict[str, Any]]:
    """
    Inspect the 'cpu' partition via sinfo and return per-node shapes:

      - node: node name (e.g. enc3-node1)
      - cpus: total CPUs on the node
      - mem_g: total memory in GB
      - state: node state (idle, mixed, allocated, ...)
    """
    try:
        lines = run('sinfo -N -p cpu -o "%N %C %m %T"')
    except subprocess.CalledProcessError:
        return []

    if not lines:
        return []

    # First line is header
    lines = lines[1:]

    shapes: List[Dict[str, Any]] = []
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue

        node = parts[0]
        c_str = parts[1]  # "alloc/idle/other/total"
        mem_mb = int(parts[2])
        state = parts[3]

        try:
            _, _, _, total = c_str.split("/")
            total_cpus = int(total)
        except Exception:
            continue

        shapes.append(
            {
                "node": node,
                "cpus": total_cpus,
                "mem_g": mem_mb / 1024.0,
                "state": state,
            }
        )

    return shapes


def nodes_that_fit(
    shapes: List[Dict[str, Any]], rec_cpus: int, rec_mem_g: int
) -> List[Dict[str, Any]]:
    """
    Filter node shapes down to those whose *total* resources are
    sufficient for (rec_cpus, rec_mem_g).

    Note: this uses *total* node capacity, not current free capacity.
    It answers: "Which node types is this shape even eligible for?"
    """
    ret: List[Dict[str, Any]] = []
    for s in shapes:
        if s["cpus"] >= rec_cpus and s["mem_g"] >= rec_mem_g:
            ret.append(s)
    return ret


# -----------------------------------------------------------------------------
# CLI entry point
# -----------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Recommend Slurm submit parameters from your past jobs on SWC.\n\n"
            "Example:\n"
            "  hpc_recommend.py modelbui --days 30\n"
            "  hpc_recommend.py brainreg --days 14"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "job_name",
        help="Substring of JobName to analyse (e.g. modelbui, brainreg, myscript.sh)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help="Lookback window in days (default: 14)",
    )

    args = parser.parse_args()

    records = summarize_jobs(args.job_name, args.days)
    if not records:
        print(f"No past jobs matching name '{args.job_name}' in last {args.days}d.")
        return

    print(f"Found {len(records)} jobs for pattern '{args.job_name}' in last {args.days}d.")

    rec = recommend_from_records(records)
    if not rec:
        print("Not enough usable data (no MaxRSS/ReqMem) to make a recommendation.")
        return

    print(f"\nUsing {rec['n_jobs']} jobs with usable memory data.")

    print("\n=== Usage summary (GB) ===")
    print(f"Median effective mem (MaxRSS or ReqMem): {rec['mem_med']:.1f} G")
    print(f"90th percentile:                       {rec['mem_p90']:.1f} G")
    print(f"Median AllocCPUS:                      {rec['cpus_med']}")

    print("\n=== Recommended Slurm shape ===")
    print(f"--cpus-per-task={rec['rec_cpus']}")
    print(f"--mem={rec['rec_mem_g']}G")

    print("\n# Example SBATCH block:")
    print("#SBATCH -p cpu")
    print(f"#SBATCH -J {args.job_name}")
    print("#SBATCH -c", rec["rec_cpus"])
    print(f"#SBATCH --mem={rec['rec_mem_g']}G")

    shapes = list_node_shapes()
    if not shapes:
        print("\nCould not query node shapes via sinfo.")
        return

    fits = nodes_that_fit(shapes, rec["rec_cpus"], rec["rec_mem_g"])

    if fits:
        print("\n=== Node types that can host this shape (by total resources) ===")
        for s in fits:
            print(f"{s['node']}: {s['cpus']} CPUs, {s['mem_g']:.0f}G RAM, state={s['state']}")
    else:
        print("\nNo nodes in 'cpu' partition have enough total CPUs+RAM for this shape.")


if __name__ == "__main__":
    main()

