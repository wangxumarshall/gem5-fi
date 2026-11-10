#!/usr/bin/env bash
# Full SiliFuzz reproduction pipeline on this machine.
#
#   FUZZ_SECONDS=180 ./scripts/run_scale.sh
#
# Steps: fuzz the two proxies, generate ifuzz sequences, fix everything into
# snapshots, run a 128-core sweep, and run 4-core / 2-minute fleet windows.
# All artifacts land in work/ and evidence/.
set -euo pipefail
cd "$(dirname "$0")/.."

FUZZ_SECONDS=${FUZZ_SECONDS:-180}
IFUZZ_N=${IFUZZ_N:-100000}
JOBS=${JOBS:-32}
WINDOWS=${WINDOWS:-4}
WINDOW_SECONDS=${WINDOW_SECONDS:-120}
SWEEP_SECONDS=${SWEEP_SECONDS:-300}

mkdir -p work/corpus work/corpus-proxy evidence

echo "== 1. libFuzzer proxies (${FUZZ_SECONDS}s each)"
./bin/capstone_fuzz -max_total_time="$FUZZ_SECONDS" -max_len=64 \
  -print_final_stats=1 work/corpus-proxy/capstone \
  > evidence/capstone-fuzz.log 2>&1 || true
./bin/unicorn_fuzz -max_total_time="$FUZZ_SECONDS" -max_len=128 \
  -print_final_stats=1 work/corpus-proxy/unicorn \
  > evidence/unicorn-fuzz.log 2>&1 || true
echo "capstone entries: $(find work/corpus-proxy/capstone -type f | wc -l)"
echo "unicorn entries:  $(find work/corpus-proxy/unicorn -type f | wc -l)"

echo "== 2. ifuzz generation"
./bin/ifuzzgen -n "$IFUZZ_N" -seed 2026 -min-insns 1 -max-insns 32 \
  -out work/cand/ifuzz-big 2>&1 | tee evidence/ifuzz-gen.log

echo "== 3. snapshot fixing"
./bin/sf_fix --in work/cand/ifuzz-big --out work/corpus/ifuzz --source ifuzz \
  --jobs "$JOBS" --spread --ref-cores 0,32,64,96 --rejected work/rej/ifuzz \
  --stats evidence/ifuzz-fix.json 2>&1 | tee evidence/ifuzz-fix.log
./bin/sf_fix --in work/corpus-proxy/capstone --out work/corpus/capstone \
  --source capstone --jobs 8 --ref-cores 0,32,64,96 \
  --rejected work/rej/capstone --stats evidence/capstone-fix.json \
  2>&1 | tee evidence/capstone-fix.log
./bin/sf_fix --in work/corpus-proxy/unicorn --out work/corpus/unicorn \
  --source unicorn --jobs 8 --ref-cores 0,32,64,96 \
  --rejected work/rej/unicorn --stats evidence/unicorn-fix.json \
  2>&1 | tee evidence/unicorn-fix.log

echo "corpus size: $(find work/corpus -name '*.sfs' | wc -l)"

echo "== 4. 128-core sweep"
./bin/sf_checker --corpus work/corpus --cores 0-127 --seconds "$SWEEP_SECONDS" \
  --mode sweep --out evidence/sweep 2>&1 | tee evidence/sweep.log

echo "== 5. 4-core / 2-minute fleet windows"
rm -rf work/fleet
python3 tools/fleet.py --corpus work/corpus --db work/fleet/results.db \
  --out-root work/fleet/runs --cores 0-127 --window-cores 4 \
  --window-seconds "$WINDOW_SECONDS" --windows "$WINDOWS" \
  | tee evidence/fleet.log

echo "done"
