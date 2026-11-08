#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gem5_src="$repo_root/CHAOS/gem5"
build_rel="build/${GEM5_BUILD_NAME:-ARM_X86_HOST}"
gem5_bin="${GEM5_OPT:-$gem5_src/$build_rel/gem5.opt}"
out_root="${FU_IBR_OUT:-$repo_root/m5out/fu-ibr-test-arm}"
arm_cc="${ARM_CC:-aarch64-linux-gnu-gcc}"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
    conda_prefix="$HOME/miniconda3/envs/${GEM5_CONDA_ENV:-py312}"
    if [[ -d "$conda_prefix" ]]; then
        export CONDA_PREFIX="$conda_prefix"
        export PATH="$conda_prefix/bin:$PATH"
        export LD_LIBRARY_PATH="$conda_prefix/lib:${LD_LIBRARY_PATH:-}"
        export PYTHON_CONFIG="$conda_prefix/bin/python3-config"
    else
        source "$repo_root/init-env.sh" "${GEM5_CONDA_ENV:-py312}"
    fi
fi

mkdir -p "$out_root/bin"
if [[ ! -f "$gem5_src/$build_rel/gem5.build/config" ]]; then
    (cd "$gem5_src" && scons defconfig "$build_rel" build_opts/ARM)
fi
(cd "$gem5_src" && scons "$build_rel/gem5.opt" -j"${JOBS:-1}" \
    "ISA_CONSTR_CCFLAGS=${ISA_CONSTR_CCFLAGS:--g0}" \
    "ISA_EXEC_CCFLAGS=${ISA_EXEC_CCFLAGS:--g0}" \
    --debug-fission --limit-ld-memory-usage)
"$arm_cc" -O2 -static -fno-pie -no-pie -Wall -Wextra -Werror \
    -I"$gem5_src/include" "$repo_root/workloads/directed/fu_ibr_workload.c" \
    "$gem5_src/util/m5/src/abi/arm64/m5op.S" -o "$out_root/bin/fu_ibr_workload"
file "$gem5_bin" | grep -Eq 'x86-64|ARM aarch64'
file "$out_root/bin/fu_ibr_workload" | grep -Fq 'ARM aarch64'

run_case() {
    local name="$1"; shift
    local workload_args="${name%%-*} 1000"
    if [[ "$name" == *-cycle ]]; then
        workload_args+=" no-markers"
    elif [[ "$name" == *-paired ]]; then
        workload_args+=" mismatched-end"
    fi
    mkdir -p "$out_root/$name"
    "$gem5_bin" --outdir="$out_root/$name" "$repo_root/configs/se/arm_chaos.py" \
        --cpu=O3 --cmd="$out_root/bin/fu_ibr_workload" \
        --workload_args="$workload_args" "$@" \
        >"$out_root/$name/gem5.log" 2>&1
    grep -Fq 'status=PASS' "$out_root/$name/gem5.log"
}
for name in alu64 alu32 mul64 mul32 div64 sparse; do
    run_case "$name" --fu_ibr --fu_ibr_work_id=7
done
run_case alu64-disabled
run_case alu64-unmatched --fu_ibr --fu_ibr_work_id=99
run_case alu64-cycle --fu_ibr --fu_ibr_window=cycle \
    --fu_ibr_start_cycle=100 --fu_ibr_end_cycle=200
run_case alu64-paired --fu_ibr --rf_ace --l1_ace

python3 - "$out_root" <<'PY'
import math
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
def stats(name):
    result = {}
    for line in (root / name / 'stats.txt').read_text().splitlines():
        fields = line.split()
        if fields and '.fuIbr.' in fields[0]:
            result[fields[0].split('.fuIbr.')[1]] = float(fields[1])
    return result

for name, group, width, ports in [('alu64', 'intAlu', 64, 2),
                                 ('alu32', 'intAlu', 32, 2),
                                 ('mul64', 'intMult', 64, 3),
                                 ('mul32', 'intMult', 32, 3),
                                 ('div64', 'intDiv', 64, 2),
                                 ('sparse', 'intAlu', 64, 2)]:
    s = stats(name)
    assert s['windowBegins'] == s['windowEnds'] == 1, (name, s)
    assert s['measuredCycles'] > 0
    for g in ['intAlu', 'intMult', 'intDiv']:
        units, inputs = {'intAlu': (6, 2), 'intMult': (2, 3),
                         'intDiv': (2, 2)}[g]
        assert s[f'unitCount::{g}'] == units, (name, g, s)
        bits, maximum, ratio = (s[f'{k}::{g}'] for k in
                                ['inputBits', 'maxInputBits', 'ibrRatio'])
        assert maximum == units * inputs * 64 * s['measuredCycles']
        assert math.isfinite(ratio) and 0 <= ratio <= 1, (name, g, ratio)
        assert abs(ratio - (bits / maximum if maximum else 0)) < 1e-8
    assert s[f'issuedOps::{group}'] >= 64000
    if group != 'intAlu':
        # The ROI is sampled at issue time, so a few wrong-path 64-bit
        # MADD/MSUB issues that speculatively pass the end marker can be
        # counted (see fu-ibr-implementation.md). The 64000 directed ops must
        # still carry exactly `width` bits each; every extra chunk must be a
        # whole 64-bit issue, and extras cannot exceed the issue count.
        ops = s[f'issuedOps::{group}']
        bits = s[f'inputBits::{group}']
        directed_bits = 64000 * width * ports
        stray = (bits - directed_bits) / (64 * ports)
        assert bits >= directed_bits, (name, group, bits, directed_bits)
        assert stray == int(stray) and 0 <= stray <= ops - 64000, (
            name, group, bits, ops, stray)
    print(f"{name}: {group} IBR={s[f'ibrRatio::{group}']:.8f}, "
          f"bits={s[f'inputBits::{group}']:.0f}, cycles={s['measuredCycles']:.0f}")

for group, wide, narrow in [('intAlu', 'alu64', 'alu32'),
                             ('intMult', 'mul64', 'mul32')]:
    a, b = stats(wide), stats(narrow)
    assert a[f'inputBits::{group}'] > b[f'inputBits::{group}'] * 1.9
    assert a[f'ibrRatio::{group}'] > b[f'ibrRatio::{group}'] * 1.9

for name in ['alu64-disabled', 'alu64-unmatched']:
    s = stats(name)
    assert s['measuredCycles'] == 0 and s['windowBegins'] == 0
    assert all(s[f'inputBits::{g}'] == 0 for g in ['intAlu', 'intMult', 'intDiv'])
s = stats('alu64-cycle')
assert s['measuredCycles'] == 100 and s['windowBegins'] == s['windowEnds'] == 0
assert stats('alu64')['ibrRatio::intAlu'] > stats('sparse')['ibrRatio::intAlu']

paired = stats('alu64-paired')
assert paired['windowBegins'] == paired['windowEnds'] == 1, paired
assert paired['issuedOps::intAlu'] >= 64000, paired

all_stats = {}
for line in (root / 'alu64-paired' / 'stats.txt').read_text().splitlines():
    fields = line.split()
    if len(fields) >= 2:
        try:
            all_stats[fields[0]] = float(fields[1])
        except ValueError:
            pass

def matching(suffix):
    values = [value for name, value in all_stats.items() if name.endswith(suffix)]
    assert values, suffix
    return values

assert matching('.rfAce.windowBegins') == [1]
assert matching('.rfAce.windowEnds') == [1]
assert matching('.rfAce.intTrackedWrites')[0] > 1000
# The hierarchy also instantiates the L1 ACE stats group on L2 (disabled), so
# name the two measured caches instead of matching every '.l1Ace.' suffix.
for cache in ['l1i-cache-0', 'l1d-cache-0']:
    assert matching(f'{cache}.l1Ace.windowBegins') == [1], cache
    assert matching(f'{cache}.l1Ace.windowEnds') == [1], cache
    assert matching(f'{cache}.l1Ace.measuredCycles')[0] > 1000, cache
print('IBR width, utilization, formula, disabled, work-ID, cycle-window and ROI-pairing checks passed')
PY
printf 'outputs: %s\n' "$out_root"
