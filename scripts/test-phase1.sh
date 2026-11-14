#!/usr/bin/env bash
# Phase-1 acceptance gate: every ACE/IBR/SAD/AutoµSens regression in one run.
#
# The gate is intentionally strict: any failed step makes the whole run fail,
# and every step keeps its full log under PHASE1_OUT.  It uses the native
# AArch64 gem5 build by default; override with GEM5_OPT.
set -uo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

export ARM_CC="${ARM_CC:-$(command -v aarch64-openEuler-linux-gcc \
    || command -v aarch64-linux-gnu-gcc)}"
export GEM5_OPT="${GEM5_OPT:-$repo_root/CHAOS/gem5/build/ARM/gem5.opt}"
out_root="${PHASE1_OUT:-$repo_root/m5out/phase1-gate}"
mkdir -p "$out_root"
: > "$out_root/steps.tsv"

if [[ -z "$ARM_CC" ]]; then
    echo "FAIL: no AArch64 cross compiler; set ARM_CC" >&2
    exit 1
fi
if [[ ! -x "$GEM5_OPT" ]]; then
    echo "FAIL: gem5 binary not executable: $GEM5_OPT" >&2
    exit 1
fi

failures=0
run_step() {
    local name="$1"
    shift
    echo "=== $name ==="
    "$@" >"$out_root/$name.log" 2>&1
    local rc=$?
    printf '%s\t%s\n' "$name" "$rc" >> "$out_root/steps.tsv"
    echo "$name rc=$rc"
    if [[ $rc -ne 0 ]]; then
        failures=$((failures + 1))
    fi
    return 0
}

# Pure-Python contracts first: they fail in seconds, before any gem5 run.
run_step pytest python3 -m pytest \
    tests/test_nsga2.py \
    tests/test_sdcfuzz_coverage.py \
    tests/test_sdcfuzz_generator.py \
    tests/test_sdcfuzz_operand_heuristic.py \
    tests/test_coverage_report.py -q

# AutoµSens: structure map, per-structure targeting, Pareto knee validation.
run_step autousens python3 scripts/test-autousens.py \
    --gem5 "$GEM5_OPT" --outdir "$out_root/autousens" --cc "$ARM_CC"

# 19-template ACE/IBR matrix + structure coverage rollup.
run_step templates python3 scripts/test-template-coverage.py \
    --gem5 "$GEM5_OPT" --outdir "$out_root/coverage" --cc "$ARM_CC"

# SAD occupancy (ROB/IQ/LQ/SQ/PRF/FU/issue).
run_step sad env SAD_OUT="$out_root/sad" bash scripts/test-sad.sh

# Direction/formula regressions for the three metric families.
run_step rf-ace env RF_ACE_OUT="$out_root/rf-ace" \
    bash scripts/test-rf-ace.sh
run_step l1-ace env L1_ACE_OUT="$out_root/l1-ace" \
    bash scripts/test-l1-ace.sh
run_step fu-ibr env FU_IBR_OUT="$out_root/fu-ibr" \
    bash scripts/test-fu-ibr.sh

# Cross-metric correctness: atomics, mixed widths, ROI snapshot.
run_step correctness python3 scripts/test-ace-ibr-correctness.py \
    --gem5 "$GEM5_OPT"

# Roll the measured matrix up into JSON/CSV/Markdown and attach SAD.
run_step coverage-report python3 -m sdcfuzz.coverage_report \
    --matrix "$out_root/coverage/coverage_matrix.json" \
    --outdir "$out_root/report" --sad-run "$out_root/sad/rob"

python3 - "$out_root" "$failures" <<'PY'
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

out = Path(sys.argv[1])
failures = int(sys.argv[2])
steps = []
for line in (out / "steps.tsv").read_text().splitlines():
    name, rc = line.split("\t")
    steps.append({"name": name, "returncode": int(rc),
                  "log": str(out / f"{name}.log")})
try:
    commit = subprocess.run(["git", "rev-parse", "HEAD"],
                            cwd=out.parents[1], text=True,
                            capture_output=True, check=True).stdout.strip()
except Exception:
    commit = None
report = {
    "schema": "sdcfuzz.phase1.gate.v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "commit": commit,
    "gem5": os.environ.get("GEM5_OPT"),
    "failures": failures,
    "passed": failures == 0,
    "steps": steps,
}
(out / "phase1_gate.json").write_text(
    json.dumps(report, indent=2, sort_keys=True) + "\n")
print(f"phase1 gate: {'PASS' if failures == 0 else 'FAIL'} "
      f"({len(steps) - failures}/{len(steps)} steps)")
for step in steps:
    print(f"  {step['name']:16s} rc={step['returncode']}")
print(f"summary: {out / 'phase1_gate.json'}")
PY

exit "$failures"
