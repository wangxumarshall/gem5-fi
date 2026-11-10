#!/usr/bin/env bash
# Reproduce the upstream sdcfuzz "D13 vs random baseline" experiment (exp02).
#
# Run this ON the board (it reuses the upstream checkout and its gem5 build);
# it does not copy files and does not need the network.
#
#   ssh sdc-0103 'bash -s' < scripts/repro-d13-baseline.sh
#   # or, on the board:
#   RUNS=100 SEED=42 JOBS=3 ./repro-d13-baseline.sh [upstream-checkout]
#
# Preconditions (all checked below):
#   * upstream sdcfuzz checkout (default ~/wangxu/silifuzz) with
#     tools/sdc_experiment/sim_sweep.py and gem5_config/workloads/*d13*
#   * a gem5.opt discoverable by tools/sdc_experiment/gem5_env.py
#     (one of its candidate paths; a symlink is fine)
#   * ~/gem5-deps (runtime libraries for the gem5 binary)
#
# Outputs: $ROOT/output/experiments/$EXP/{sim_*.json,summary.json}
set -Eeuo pipefail

ROOT="${1:-${UPSTREAM_ROOT:-$HOME/wangxu/silifuzz}}"
EXP="${EXP:-exp02-d13-repro-$(date +%Y%m%d-%H%M%S)}"
RUNS="${RUNS:-100}"
SEED="${SEED:-42}"
JOBS="${JOBS:-3}"          # upstream MCE red line: gem5 fault injection <= 4

cd "$ROOT"

test -f tools/sdc_experiment/sim_sweep.py || {
    echo "FAIL: $ROOT is not the upstream sdcfuzz checkout" >&2; exit 1; }
test -f gem5_config/workloads/sdc_probe_workload_d13.c || {
    echo "FAIL: D13 workload missing under $ROOT/gem5_config/workloads" >&2; exit 1; }
test -d "$HOME/gem5-deps" || {
    echo "FAIL: ~/gem5-deps missing (gem5 runtime libraries)" >&2; exit 1; }

mapfile -t candidates < <(python3 - <<'PY'
import sys
sys.path.insert(0, ".")
from tools.sdc_experiment.gem5_env import GEM5_OPT
print(GEM5_OPT)
PY
)
gem5="${candidates[0]:-}"
if [[ ! -x "$gem5" ]]; then
    cat >&2 <<EOF
FAIL: gem5.opt not found (looked for "$gem5").
Create the symlink the upstream environment expects, e.g.:
  mkdir -p ~/wangxu/gem5-fi/CHAOS/gem5/build/ARM
  ln -sfn <an existing ARM gem5.opt> \\
      ~/wangxu/gem5-fi/CHAOS/gem5/build/ARM/gem5.opt
EOF
    exit 1
fi
echo "host=$(hostname) arch=$(uname -m) gem5=$gem5"
echo "exp=$EXP runs=$RUNS seed=$SEED jobs=$JOBS"

for MODE in bit struct; do
    for G in B D13; do
        echo "=== $G $MODE $(date +%H:%M:%S)"
        python3 tools/sdc_experiment/sim_sweep.py --group "$G" --mode "$MODE" \
            --runs "$RUNS" --seed "$SEED" --exp "$EXP" --jobs "$JOBS"
    done
done

python3 - "$EXP" <<'PY'
import json, sys
sys.path.insert(0, ".")
from tools.sdc_experiment.sim_sweep import fisher_exact

exp = sys.argv[1]
out = {}
for mode in ("bit", "struct"):
    B = json.load(open(f"output/experiments/{exp}/sim_B_{mode}.json"))
    D = json.load(open(f"output/experiments/{exp}/sim_D13_{mode}.json"))
    ratio = D["diverge_rate"] / B["diverge_rate"] if B["diverge_rate"] else float("inf")
    _, p = fisher_exact(D["clean_diverge"], D["n"] - D["clean_diverge"],
                        B["clean_diverge"], B["n"] - B["clean_diverge"])
    out[mode] = {"B": B, "D13": D, "D_over_B": round(ratio, 3), "fisher_p": p,
                 "verdict": "BEAT" if ratio >= 1.5 and p < 0.05 else
                            ("MARGINAL" if ratio >= 1.5 else "NOT_BEAT(诚实记录)")}
path = f"output/experiments/{exp}/summary.json"
json.dump(out, open(path, "w"), indent=2, ensure_ascii=False)
print(json.dumps({m: {"D_over_B": out[m]["D_over_B"],
                      "fisher_p": out[m]["fisher_p"],
                      "verdict": out[m]["verdict"]} for m in out},
                 ensure_ascii=False, indent=2))
print(f"saved -> {path}")
PY
