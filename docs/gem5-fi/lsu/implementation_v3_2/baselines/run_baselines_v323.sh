#!/usr/bin/env bash
# Reproduce the no-fault W1-W8 baselines with the branch-root gem5 binary.
set -uo pipefail
ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
IMPL="$ROOT/docs/gem5-fi/lsu/implementation_v3_2"
WL="$IMPL/workloads"
GEM5="$ROOT/build/ARM/gem5.opt"
mkdir -p "$IMPL/baselines_v3_2_3"
cd "$ROOT" || exit 2

for name in agu_addrmodes sq_forward lq_lifetime sq_drain load_response store_path replay_dependency alignment; do
  out="$IMPL/baselines_v3_2_3/$name"
  mkdir -p "$out"
  cmd=("$GEM5" "--outdir=$out" "configs/se/lsu_proxy.py" "--cmd=$WL/$name" \
       "--cpu" "O3" "--variant" "B0")
  printf '%s\n' "${cmd[@]}" > "$out/command.txt"
  "${cmd[@]}" > "$out/stdout.log" 2> "$out/stderr.log"
  rc=$?
  expected="$(tr -d '[:space:]' < "$WL/$name.golden")"
  python3 "$WL/oracle_check.py" "$expected" "$out/stdout.log" > "$out/oracle.log" 2>&1
  orc=$?
  tick="$(grep -m1 '^finalTick' "$out/stats.txt" 2>/dev/null | awk '{print $2}')"
  python3 - "$out" "$name" "$rc" "$orc" "$expected" "$tick" <<'PY'
import hashlib, json, os, platform, subprocess, sys
from pathlib import Path
out, name, rc, orc, expected, tick = sys.argv[1:7]
root = Path(out).resolve().parents[5]
def sha(p):
    h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
meta = {
  "workload": name,
  "command": Path(out, "command.txt").read_text().splitlines(),
  "exit_code": int(rc),
  "oracle_exit": int(orc),
  "oracle_expected": expected,
  "oracle": Path(out, "oracle.log").read_text().strip().splitlines(),
  "final_tick": int(tick) if tick else None,
  "gem5_binary": str(root/"build/ARM/gem5.opt"),
  "gem5_binary_sha256": sha(root/"build/ARM/gem5.opt"),
  "git_commit": subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip(),
  "gcc": subprocess.check_output(["gcc","--version"],text=True).splitlines()[0],
  "binary_sha256": sha(Path(root/"docs/gem5-fi/lsu/implementation_v3_2/workloads")/name),
  "stats_sha256": sha(Path(out,"stats.txt")),
  "config_ini_sha256": sha(Path(out,"config.ini")),
}
Path(out,"run_meta.json").write_text(json.dumps(meta,indent=2))
print(name, "exit", rc, "oracle", orc, "tick", tick)
PY
done
