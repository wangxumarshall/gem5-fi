#!/bin/bash
# PosParity detection-matrix experiment (paper §6.2 prototype validation).
# Design: fault {none, byte_lane_skew(rand k), all_zero, bit_flip} x validator
# {off, on} + panic-mode spot check + 5-seed stability (42/1/2/3/4) + the
# unipar adversarial-data regression arm (Critical-1 guard). All arms are
# REAL gem5 runs of the ptrskew/unipar probes on the O3 store->load
# forwarding path.
#
# ---------------------------------------------------------------------------
# EXPECTED RESULTS (corrected post Task-4 fix; the brief's pre-fix table is
# superseded — detection is the SNAPSHOT dual-weighted-aggregate model, which
# is PROBABILISTIC against lane permutations, not a hard 100%):
#
#   arm 1 golden+validator ON : fails=0, numTagged==numVerified>0,
#                               numMismatches=0 (zero false positives).
#   arm 2 skew+validator OFF  : SDC escapes silently: ptr_corrupt>0 / guest
#                               page-fault panic / "clean" exit with fails>0.
#                               This is the status-quo (no detection) arm —
#                               ANY of those outcomes is the expected result.
#   arm 3 skew+validator ON   : detection rate = numMismatches /
#                               numStructuralByteLaneSkew, expected ≈ 1-O(2^-10)
#                               for pointer-like data (theory: escape 2^-12 odd
#                               k, 2^-10 k=2/6, 2^-5 k=4 on UNIFORM random
#                               data; the probe's fixed slot values are
#                               deterministic per (word,k) — none of the probe
#                               words is on an escape hyperplane, but stack-
#                               spill forwards carry varying data where an
#                               escape CAN occur). DEVIATIONS BELOW 100% ARE
#                               REAL DATA: report as measured, explain via the
#                               escape-hyperplane math. NOTE: 4-byte forwards
#                               (FwdSize=4) have their own, larger escape
#                               probabilities (fewer lanes = weaker constraint).
#   arm 4 all_zero+validator  : escape iff original (W1,W2)==(0x40,0xC0)
#                               (prob 2^-13 random data; heap-pointer slots
#                               effectively never) -> expect numMismatches ==
#                               numStructuralAllZero.
#   arm 5 bit_flip+validator  : numMismatches == numBitFlips EXACTLY (the only
#                               hard-100% arm; odd-weight theorem, exhaustively
#                               verified 1,284,032 cases).
#   arm 6 panic mode          : gem5 panic "CHAOSPosParity: positional-parity
#                               mismatch" -> fail-fast, RC=134, no stats.txt.
#   arm 7 unipar adversarial  : uniform-parity word 0x0102040810204080 (the
#                               exact data that broke the OLD check 100% of the
#                               time) under fixed k=1 and k=4 (k=4 = weakest
#                               theoretical case, 2^-5 on random data): expect
#                               detection on the probe's own forwards (none of
#                               ror_1..ror_7 of this word is in the 17-perm
#                               adversarial escape set — Task 4 verified all 7
#                               rotations in-simulator).
#
# RUNNER QUIRKS (Task 4 verified):
#   * bit-flip knobs: --fault bit_flip --lsq-fwd-bits N (there is NO
#     --lsq-fault).
#   * ALL runs use explicit nonzero --seed (seed 0 seeds CHAOSLSQFwd from
#     std::random_device — nondeterministic).
#   * --max-faults 0 = unlimited (default 1 would cap injections at one).
#   * Guest crashes under heavy injection are LEGITIMATE SDC outcomes (a
#     skewed stack spill / pointer deref). gem5 aborts WITHOUT dumping
#     stats.txt, so count-mode arms use an adaptive --max-tick cap: on abort
#     at tick T, retry with cap T-500000 (deterministic same-seed rerun) to
#     capture the stats accumulated before the lethal event. The o3_chaos_
#     smoke.py cap is applied via m5.simulate(max_tick) (Root has no
#     max_tick param in this gem5).
# ---------------------------------------------------------------------------
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
GEM5="$REPO/CHAOS/gem5/build/ARM/gem5.opt"
PROBE="/tmp/ptrskew_rebuilt"    # rebuilt from ptrskew_kernel.c (host aarch64)
UPROBE="/tmp/unipar_rebuilt"    # rebuilt from unipar_probe.c
CFG="$HERE/o3_chaos_smoke.py"
OUT=/tmp/posparity
PROB=0.15                       # per-forward injection probability
ITERS=2000                      # ptrskew iters (main loop ~2000 forwards)
UITERS=5000                     # unipar iters (tiny loop)
SEEDS="42 1 2 3 4"
mkdir -p $OUT

# Rebuild both probes with the host (aarch64-native) gcc.
# unipar is built -O0 AND with volatile buf (defense in depth): at -O2 with a
# non-volatile buf, GCC load/store elimination deleted the probe loop body
# entirely (verified by disassembly — main had zero memory instructions), so
# the adversarial word never traveled the forwarding path and the arm-7 cells
# only measured loader/glibc startup forwards (review Critical 1).
taskset -c 0-31 gcc -static -O2 -o $PROBE  $HERE/ptrskew_kernel.c || echo "[warn] ptrskew rebuild failed, using existing $PROBE"
taskset -c 0-31 gcc -static -O0 -o $UPROBE $HERE/unipar_probe.c   || echo "[warn] unipar rebuild failed, using existing $UPROBE"
# Defense-in-depth gate: refuse to run arm 7 with a probe whose loop body was
# optimized away (no store+reload in main => all "detections" would be vacuous).
if ! objdump -d $UPROBE | awk '/<main>:/,/^$/' | grep -qE '\b(st|ld)[rp]?\b'; then
  echo "[FATAL] $UPROBE main has no store/load instructions — probe loop optimized away; aborting." >&2
  exit 1
fi

# statsgrep DIR PATTERN — one line of "name value" pairs from stats.txt.
sg() { grep -E "$2" $1/stats.txt 2>/dev/null | tr -s ' ' | sed 's/ system\.system\.//' | tr '\n' ';' ; }

# run TAG [--nocap] gem5-args...
#   Runs the config; on guest abort (no stats) retries with an adaptive cap
#   (crash_tick - 500k, then a TIGHT retry at crash_tick - 100k when the
#   first retry captured 0 injections — a single lethal injection lands
#   shortly before the crash, so the coarse window can straddle it) to
#   capture pre-crash stats. Prints a one-line summary of the
#   posparity/lsqfi counters + guest outcome.
#   NOTE on clocks: cpu->curCycle() = tick/500 (2GHz, 1ps tick resolution).
run() {
  local tag=$1; shift
  local nocap=0
  if [ "$1" = "--nocap" ]; then nocap=1; shift; fi
  local dir=$OUT/$tag
  local out log cap=60000000 rc t inj crash_t=0
  for attempt in 1 2 3; do
    rm -rf "$dir"; mkdir -p "$dir"
    out=$OUT/$tag.out
    if [ $nocap -eq 1 ]; then
      timeout 900 taskset -c 0-31 "$GEM5" -d "$dir" "$CFG" "$@" > "$out" 2>&1
    else
      timeout 900 taskset -c 0-31 "$GEM5" -d "$dir" "$CFG" --max-tick $cap "$@" > "$out" 2>&1
    fi
    rc=$?
    # Success for stats purposes: stats.txt non-empty.
    if [ -s "$dir/stats.txt" ]; then
      inj=$(grep -m1 -oE 'numFaultsInjected\s+[0-9]+' "$dir/stats.txt" | grep -oE '[0-9]+')
      if [ "${inj:-0}" = "0" ] && [ $attempt -eq 2 ] && [ "$crash_t" -gt 1000000 ]; then
        # First retry window straddled the (single, lethal) injection —
        # tighten the window (crash tick remembered from the crashing
        # attempt; the retry's own .out has no abort line) before
        # declaring the cell empty.
        cap=$(( crash_t - 100000 ))
        echo "  [$tag] retry captured 0 injections -> tight retry with cap $cap (attempt 3)"
        continue
      fi
      local guest cause
      guest=$(grep -oE '(iters=[0-9]+ ptr_corrupt=[0-9]+ val_mismatch=[0-9]+ fails=[0-9]+|intact=[0-9]+/[0-9]+)' "$out" | head -1)
      cause=$(grep -E 'Exiting @ tick' "$out" | head -1 | sed 's/^\[smoke\] //')
      echo "  [$tag] rc=$rc ${cause:-GUEST-ABORTED-BEFORE-CAP} ${guest:+| $guest}"
      echo "    [posparity] $(sg $dir 'numTagged|numVerified|numMismatches')"
      echo "    [lsqfi]     $(sg $dir 'numHooksCalled|numFaultsInjected|numBitFlips|numStructural')"
      return 0
    fi
    # Aborted without stats. If this was the nocap arm or a posparity panic,
    # report the abort as the outcome (panic arm: expected). Else adaptive retry.
    if grep -q "CHAOSPosParity: positional-parity mismatch" "$out"; then
      echo "  [$tag] POSPARITY-PANIC (fail-fast): $(grep -m1 'panic: CHAOSPosParity' "$out" | sed 's/^.*panic: //')"
      echo "    $(grep -m1 'Program aborted at tick' "$out")"
      return 0
    fi
    if [ $nocap -eq 1 ]; then
      echo "  [$tag] GUEST-ABORTED (SDC manifested, no validator): $(grep -m1 -oE 'Page table fault when accessing virtual address 0x[0-9a-f]+' "$out")"
      echo "    $(grep -m1 'Program aborted at tick' "$out") | injections_logged=$(wc -l < "$dir/lsq_fwd_injections.log" 2>/dev/null || echo 0)"
      return 0
    fi
    t=$(grep -m1 -oE 'Program aborted at tick [0-9]+' "$out" | grep -oE '[0-9]+')
    if [ -z "$t" ] || [ "$t" -lt 1500000 ]; then
      echo "  [$tag] ABORTED-UNRECOVERABLE (no stats, no parseable abort tick or too early): rc=$rc"
      echo "    $(grep -m1 -E 'panic:|Page table|Killed' "$out" | head -1)"
      return 1
    fi
    crash_t=$t
    cap=$(( t - 500000 ))
    echo "  [$tag] guest aborted at tick $t -> retrying with cap $cap (attempt $((attempt+1)))"
  done
  echo "  [$tag] FAILED after adaptive retry"
  return 1
}

BASE_ARGS="--binary $PROBE --iters $ITERS --no-fi --first-clock 2000 --max-faults 0"
UBASE_ARGS="--binary $UPROBE --iters $UITERS --no-fi --first-clock 2000 --max-faults 0"

echo "=== PosParity detection matrix (validator: dual weighted mod-256 aggregates) ==="
echo "=== probe=ptrskew (load-use-as-pointer, core-179 D1 chain) unless noted   ==="
echo "=== seeds: $SEEDS | prob=$PROB | iters=$ITERS (ptrskew) / $UITERS (unipar) ==="

for SEED in $SEEDS; do
  echo "--- seed $SEED ---"
  echo "[1] golden, validator ON (false-positive control):"
  run s${SEED}_golden_on $BASE_ARGS --seed $SEED --posparity
  echo "[2] skew(k rand), validator OFF (status quo: SDC escapes silently):"
  run s${SEED}_skew_off --nocap $BASE_ARGS --seed $SEED \
      --lsq-fwd-prob $PROB --lsq-structural byte_lane_skew --lsq-skew 0
  echo "[3] skew(k rand), validator ON:"
  run s${SEED}_skew_on $BASE_ARGS --seed $SEED \
      --lsq-fwd-prob $PROB --lsq-structural byte_lane_skew --lsq-skew 0 --posparity
  echo "[4] all_zero, validator ON:"
  run s${SEED}_zero_on $BASE_ARGS --seed $SEED \
      --lsq-fwd-prob $PROB --lsq-structural all_zero --posparity
  echo "[5] bit_flip(3 bits), validator ON:"
  run s${SEED}_bit_on $BASE_ARGS --seed $SEED \
      --lsq-fwd-prob $PROB --fault bit_flip --lsq-fwd-bits 3 --posparity
done

echo "[6] panic mode spot check (skew k=1, action=panic, seed 42):"
run panic_skew $BASE_ARGS --seed 42 \
    --lsq-fwd-prob 0.20 --lsq-structural byte_lane_skew --lsq-skew 1 \
    --posparity --posparity-action panic

echo "[7] unipar adversarial-data arm (0x0102040810204080, Critical-1 guard):"
for SEED in $SEEDS; do
  echo "--- unipar seed $SEED, k=1 (prob 0.20 unlimited) ---"
  run u${SEED}_k1 $UBASE_ARGS --seed $SEED \
      --lsq-fwd-prob 0.20 --lsq-structural byte_lane_skew --lsq-skew 1 --posparity
  echo "--- unipar seed $SEED, k=4 (prob 0.20 unlimited; weakest case) ---"
  run u${SEED}_k4 $UBASE_ARGS --seed $SEED \
      --lsq-fwd-prob 0.20 --lsq-structural byte_lane_skew --lsq-skew 4 --posparity
  echo "--- unipar seed $SEED, k=1 (max-faults 1: single skew, guest survives) ---"
  run u${SEED}_k1_mf1 $UBASE_ARGS --max-faults 1 --seed $SEED \
      --lsq-fwd-prob 0.05 --lsq-structural byte_lane_skew --lsq-skew 1 --posparity
  echo "--- unipar seed $SEED, k=4 (max-faults 1) ---"
  run u${SEED}_k4_mf1 $UBASE_ARGS --max-faults 1 --seed $SEED \
      --lsq-fwd-prob 0.05 --lsq-structural byte_lane_skew --lsq-skew 4 --posparity
done

echo "=== done; per-run artifacts under $OUT/<tag>{,.out} ==="
