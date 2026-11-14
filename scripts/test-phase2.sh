#!/usr/bin/env bash
# Phase-2 one-shot gate: avalanche, RL, power patterns, McPAT, FI, correlation.
#
#   bash scripts/test-phase2.sh
#   EPISODES=120 FI_RUNS=12 JOBS=4 bash scripts/test-phase2.sh
#
# Every step writes a log under m5out/phase2-gate/ and a JSONL status line.
# The final audit (scripts/verify-phase2.py) binds the five Phase-2 milestones
# to artifacts and success assertions.
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
GATE="$ROOT/m5out/phase2-gate"
mkdir -p "$GATE"
: > "$GATE/steps.jsonl"

EPISODES="${EPISODES:-200}"
FI_RUNS="${FI_RUNS:-20}"
JOBS="${JOBS:-4}"

run_step() {
    local name="$1"; shift
    echo "=== $name ==="
    if "$@" > "$GATE/$name.log" 2>&1; then
        printf '{"step":"%s","status":"PASS"}\n' "$name" >> "$GATE/steps.jsonl"
        echo "PASS $name"
    else
        printf '{"step":"%s","status":"FAIL"}\n' "$name" >> "$GATE/steps.jsonl"
        echo "FAIL $name (tail follows)"
        tail -40 "$GATE/$name.log" >&2 || true
        exit 1
    fi
}

run_step unit-tests python3 -m pytest -q \
    tests/test_sdcfuzz_avalanche.py \
    tests/test_sdcfuzz_power.py \
    tests/test_sdcfuzz_rl.py \
    tests/test_sdcfuzz_power_sdc.py

run_step avalanche python3 -m sdcfuzz.phase2 avalanche --iterations 40
run_step rl python3 -m sdcfuzz.phase2 rl-train --episodes "$EPISODES"
run_step rl-validate python3 -m sdcfuzz.phase2 rl-validate --runs "$FI_RUNS" --jobs "$JOBS"
run_step power-gen python3 -m sdcfuzz.phase2 power-gen
run_step power-run python3 -m sdcfuzz.phase2 power-run
run_step fi python3 -m sdcfuzz.phase2 fi --runs "$FI_RUNS" --jobs "$JOBS"
run_step mcpat-select python3 -m sdcfuzz.phase2 mcpat-select
run_step correlate python3 -m sdcfuzz.phase2 correlate
run_step audit python3 scripts/verify-phase2.py

python3 - "$GATE" <<'PY'
import json
import sys
import time
from pathlib import Path

gate = Path(sys.argv[1])
steps = [json.loads(line) for line in
         (gate / "steps.jsonl").read_text().splitlines() if line.strip()]
milestones_path = gate / "phase2_milestones.json"
milestones = json.loads(milestones_path.read_text()) if milestones_path.exists() else {}
payload = {
    "schema": "sdcfuzz.phase2.gate.v1",
    "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "steps": steps,
    "steps_passed": sum(1 for step in steps if step["status"] == "PASS"),
    "steps_total": len(steps),
    "milestones": milestones.get("milestones", {}),
    "overall": "PASS" if all(step["status"] == "PASS" for step in steps) else "FAIL",
}
(gate / "phase2_gate.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps({"steps": f"{payload['steps_passed']}/{payload['steps_total']}",
                  "overall": payload["overall"]}, indent=2))
PY
