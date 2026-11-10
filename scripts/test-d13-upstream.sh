#!/usr/bin/env bash
# Verify the vendored upstream D13 workload: provenance hashes, build, native
# golden run, gem5 golden run, and one CHAOSReg injection smoke.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
vendor="$repo_root/sdcfuzz/upstream/d13"
out_root="${D13_OUT:-$repo_root/m5out/d13-upstream}"
gem5_bin="${GEM5_OPT:-$repo_root/CHAOS/gem5/build/ARM/gem5.opt}"
config="$repo_root/configs/se/arm_chaos.py"
arm_cc="${ARM_CC:-$(command -v aarch64-openEuler-linux-gcc \
    || command -v aarch64-linux-gnu-gcc)}"

if [[ -z "$arm_cc" ]]; then
    echo "FAIL: no AArch64 cross compiler (set ARM_CC)" > /dev/stderr
    exit 1
fi
if [[ ! -x "$gem5_bin" ]]; then
    echo "FAIL: native gem5 not found/executable: $gem5_bin" > /dev/stderr
    exit 1
fi

check_sha() {
    local path="$1"
    local expected="$2"
    local actual
    actual="$(sha256sum "$path" | awk '{print $1}')"
    if [[ "$actual" != "$expected" ]]; then
        echo "FAIL: sha256 mismatch for $path" > /dev/stderr
        echo "  expected $expected" > /dev/stderr
        echo "  actual   $actual" > /dev/stderr
        exit 1
    fi
    echo "sha256 ok: $(basename "$path")"
}

echo "[verify] vendored upstream D13 provenance"
check_sha "$vendor/sdc_probe_workload_d13.c" \
    4143a4bdee3244452ce2747e590d6cbfbbb45117b23a3027d04a0eacc0067263
check_sha "$vendor/sdc_probe_workload_random.c" \
    fb461f72675c194b5a93aeeeab55f73f6fba5ad6cf4830146bc935d1c169c1be
check_sha "$vendor/LICENSE" \
    cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30

mkdir -p "$out_root/bin"
echo "[build] D13 and B baseline ($arm_cc)"
"$arm_cc" -static -O2 -Wall -Wextra -Werror \
    "$vendor/sdc_probe_workload_d13.c" -o "$out_root/bin/sdc_probe_workload_d13"
"$arm_cc" -static -O2 -Wall -Wextra -Werror \
    "$vendor/sdc_probe_workload_random.c" -o "$out_root/bin/sdc_probe_workload_random"
file "$out_root/bin/sdc_probe_workload_d13" | grep -Fq 'ARM aarch64'
file "$out_root/bin/sdc_probe_workload_random" | grep -Fq 'ARM aarch64'

d13_golden='SUM=118831515424667458 CRC=dbc8bf2a'
b_golden='SUM=10721424292087689827 CRC=6728fc4a'

echo "[run] D13 native golden"
d13_native="$("$out_root/bin/sdc_probe_workload_d13")"
printf '%s\n' "$d13_native"
grep -Fq "$d13_golden" <<<"$d13_native"

echo "[run] D13 native determinism"
d13_again="$("$out_root/bin/sdc_probe_workload_d13")"
if [[ "$d13_native" != "$d13_again" ]]; then
    echo "FAIL: D13 native output is not deterministic" > /dev/stderr
    exit 1
fi

echo "[run] B baseline native golden"
b_native="$("$out_root/bin/sdc_probe_workload_random")"
printf '%s\n' "$b_native"
grep -Fq "$b_golden" <<<"$b_native"

echo "[run] D13 under native gem5 (O3, no injection)"
mkdir -p "$out_root/gem5-baseline"
"$gem5_bin" --outdir="$out_root/gem5-baseline" "$config" --cpu=O3 \
    --cmd="$out_root/bin/sdc_probe_workload_d13" \
    >"$out_root/gem5-baseline/gem5.log" 2>&1
grep -Fq "$d13_golden" "$out_root/gem5-baseline/gem5.log"

echo "[run] D13 CHAOSReg single-injection smoke"
mkdir -p "$out_root/gem5-fi"
"$gem5_bin" --outdir="$out_root/gem5-fi" "$config" --cpu=O3 \
    --cmd="$out_root/bin/sdc_probe_workload_d13" \
    --chaos_reg --probability=1.0 --max_faults=1 \
    --first_clock=1000 --rng_seed=42 \
    >"$out_root/gem5-fi/gem5.log" 2>&1
if ! grep -Eq 'FaultType|numFaultsInjected +1' \
        "$out_root/gem5-fi/fault_injections.log" \
        "$out_root/gem5-fi/stats.txt" 2>/dev/null; then
    echo "FAIL: CHAOSReg did not record one injection" > /dev/stderr
    tail -20 "$out_root/gem5-fi/gem5.log" > /dev/stderr
    exit 1
fi
if grep -Fq 'FaultType' "$out_root/gem5-fi/fault_injections.log" 2>/dev/null; then
    grep -F 'FaultType' "$out_root/gem5-fi/fault_injections.log" | head -1
fi

echo
echo "D13 provenance, golden output, determinism, gem5 baseline and FI smoke passed"
echo "outputs: $out_root"
