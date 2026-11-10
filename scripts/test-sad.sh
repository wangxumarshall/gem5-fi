#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gem5_src="$repo_root/CHAOS/gem5"
build_rel="build/${GEM5_BUILD_NAME:-ARM}"
gem5_bin="${GEM5_OPT:-$gem5_src/$build_rel/gem5.opt}"
out_root="${SAD_OUT:-$repo_root/m5out/sad-test}"
arm_cc="${ARM_CC:-$(command -v aarch64-linux-gnu-gcc \
    || command -v aarch64-openEuler-linux-gcc)}"
config="$repo_root/configs/se/arm_chaos.py"
workload="$repo_root/workloads/directed/sad_workload.c"

if [[ -z "$arm_cc" ]]; then
    echo "FAIL: no AArch64 cross compiler (set ARM_CC)" > /dev/stderr
    exit 1
fi

if [[ ! -x "$gem5_bin" || -n "$(find "$gem5_src/src" -newer "$gem5_bin" -print -quit)" ]]; then
    if [[ ! -f "$gem5_src/$build_rel/gem5.build/config" ]]; then
        (cd "$gem5_src" && scons defconfig "$build_rel" build_opts/ARM)
    fi
    (cd "$gem5_src" && scons "$build_rel/gem5.opt" -j"${JOBS:-8}" \
        "ISA_CONSTR_CCFLAGS=${ISA_CONSTR_CCFLAGS:--g0}" \
        "ISA_EXEC_CCFLAGS=${ISA_EXEC_CCFLAGS:--g0}" \
        --debug-fission --limit-ld-memory-usage)
fi

mkdir -p "$out_root/bin"
"$arm_cc" -O2 -static -fno-pie -no-pie -Wall -Wextra -Werror \
    -I"$gem5_src/include" "$workload" \
    "$gem5_src/util/m5/src/abi/arm64/m5op.S" \
    -o "$out_root/bin/sad_workload"

file "$out_root/bin/sad_workload" | grep -Fq 'ARM aarch64'

run_case() {
    local name="$1"
    local mode="$2"
    local iterations="$3"
    shift 3
    local out_dir="$out_root/$name"
    mkdir -p "$out_dir"
    "$gem5_bin" --outdir="$out_dir" "$config" --cpu=O3 \
        --cmd="$out_root/bin/sad_workload" \
        --workload_args="$mode $iterations" "$@" \
        >"$out_dir/gem5.log" 2>&1
    grep -Fq 'status=PASS' "$out_dir/gem5.log"
}

run_case nop nop 400 --sad --sad_window=workitem --sad_work_id=7
run_case rob rob 400 --sad --sad_window=workitem --sad_work_id=7
run_case lsq lsq 200 --sad --sad_window=workitem --sad_work_id=7
run_case prf prf 400 --sad --sad_window=workitem --sad_work_id=7
run_case nop-disabled nop 400
run_case rob-unmatched rob 400 --sad --sad_work_id=99

# Cycle mode must not be reset by m5 work-item markers: run the same body
# with markers disabled so [100, 200) is the actual sampled window.
mkdir -p "$out_root/rob-cycle"
"$gem5_bin" --outdir="$out_root/rob-cycle" "$config" --cpu=O3 \
    --cmd="$out_root/bin/sad_workload" \
    --workload_args="rob 400 no-markers" \
    --sad --sad_window=cycle --sad_start_cycle=5000 --sad_end_cycle=5100 \
    >"$out_root/rob-cycle/gem5.log" 2>&1
grep -Fq 'status=PASS' "$out_root/rob-cycle/gem5.log"

python3 - "$out_root" <<'PY'
import math
import pathlib
import sys

root = pathlib.Path(sys.argv[1])


def stats(name):
    values = {}
    for line in (root / name / 'stats.txt').read_text().splitlines():
        fields = line.split()
        if len(fields) >= 2 and '.sad.' in fields[0]:
            values[fields[0].split('.sad.')[1]] = float(fields[1])
    return values


resources = ['rob', 'iq', 'lq', 'sq', 'intPrf', 'vecPrf', 'fu']

for name in ['nop', 'rob', 'lsq', 'prf']:
    s = stats(name)
    assert s['windowBegins'] == s['windowEnds'] == 1, (name, s)
    assert s['samples'] > 0, (name, s)
    assert s['measuredCycles'] == s['samples'], (name, s)
    assert s['issuedOps'] > 0, (name, s)
    for resource in resources:
        ratio = s[f'ratio::{resource}']
        used = s[f'usedSum::{resource}']
        capacity = s[f'capacity::{resource}']
        assert math.isfinite(ratio) and 0 <= ratio <= 1, (name, resource, ratio)
        expected = used / (s['samples'] * capacity) if capacity else 0
        assert abs(ratio - expected) < 1e-7, (name, resource, ratio, expected)
    expected = s['issuedOps'] / (s['samples'] * s['issueWidth'])
    assert abs(s['issueRatio'] - expected) < 1e-7, (name, s)
    print(f"{name:13s} samples={s['samples']:.0f} "
          f"rob={s['ratio::rob']:.6f} lq={s['ratio::lq']:.6f} "
          f"sq={s['ratio::sq']:.6f} prf={s['ratio::intPrf']:.6f} "
          f"fu={s['ratio::fu']:.6f} issue={s['issueRatio']:.6f}")

nop, rob, lsq, prf = (stats(name) for name in ['nop', 'rob', 'lsq', 'prf'])
assert rob['ratio::rob'] > 1.5 * nop['ratio::rob'], (
    'rob mode must raise ROB SAD', nop['ratio::rob'], rob['ratio::rob'])
assert lsq['ratio::lq'] > nop['ratio::lq'], (
    'lsq mode must raise load-queue SAD', nop['ratio::lq'], lsq['ratio::lq'])
assert lsq['ratio::sq'] > nop['ratio::sq'], (
    'lsq mode must raise store-queue SAD', nop['ratio::sq'], lsq['ratio::sq'])
assert prf['ratio::intPrf'] > nop['ratio::intPrf'], (
    'prf mode must raise integer PRF SAD',
    nop['ratio::intPrf'], prf['ratio::intPrf'])

for name in ['nop-disabled', 'rob-unmatched']:
    s = stats(name)
    assert s['samples'] == 0 and s['windowBegins'] == 0, (name, s)
    assert all(s[f'ratio::{resource}'] == 0 for resource in resources), (name, s)

cycle = stats('rob-cycle')
assert 0 < cycle['samples'] <= 100, cycle
assert cycle['windowBegins'] == cycle['windowEnds'] == 0
print(f"SAD window, formula, direction, disabled and cycle-mode checks passed "
      f"(cycle samples={cycle['samples']:.0f})")
PY

printf 'outputs: %s\n' "$out_root"
