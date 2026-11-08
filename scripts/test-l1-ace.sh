#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gem5_src="$repo_root/CHAOS/gem5"
gem5_build_name="${GEM5_BUILD_NAME:-ARM_X86_HOST}"
gem5_build_rel="build/$gem5_build_name"
gem5_build_dir="$gem5_src/$gem5_build_rel"
gem5_bin="${GEM5_OPT:-$gem5_build_dir/gem5.opt}"
config="$repo_root/configs/se/arm_chaos.py"
workload_src="$repo_root/workloads/directed/l1_ace_workload.c"
out_root="${L1_ACE_OUT:-$repo_root/m5out/l1-ace-test-arm}"
jobs="${JOBS:-2}"
arm_cc="${ARM_CC:-aarch64-linux-gnu-gcc}"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
    conda_env="${GEM5_CONDA_ENV:-py312}"
    conda_prefix=""
    if [[ -n "${CONDA_EXE:-}" ]]; then
        conda_root="$(cd "$(dirname "$CONDA_EXE")/.." && pwd)"
        if [[ -d "$conda_root/envs/$conda_env" ]]; then
            conda_prefix="$conda_root/envs/$conda_env"
        fi
    fi
    if [[ -z "$conda_prefix" && -d "$HOME/miniconda3/envs/$conda_env" ]]; then
        conda_prefix="$HOME/miniconda3/envs/$conda_env"
    fi
    if [[ -n "$conda_prefix" ]]; then
        export CONDA_PREFIX="$conda_prefix"
        export PATH="$conda_prefix/bin:$PATH"
        export LD_LIBRARY_PATH="$conda_prefix/lib:${LD_LIBRARY_PATH:-}"
        export PYTHON_CONFIG="$conda_prefix/bin/python3-config"
    else
        # shellcheck disable=SC1091
        source "$repo_root/init-env.sh" "$conda_env"
    fi
fi

mkdir -p "$out_root/bin"

if [[ ! -f "$gem5_build_dir/gem5.build/config" ]]; then
    echo "[configure] ARM target, x86 host build directory"
    (cd "$gem5_src" && scons defconfig "$gem5_build_rel" build_opts/ARM)
fi

echo "[build] gem5 ARM target (native x86 host executable)"
(cd "$gem5_src" && scons "$gem5_build_rel/gem5.opt" -j"$jobs" \
    "ISA_CONSTR_CCFLAGS=${ISA_CONSTR_CCFLAGS:--g0}" \
    "ISA_EXEC_CCFLAGS=${ISA_EXEC_CCFLAGS:--g0}" \
    --debug-fission --limit-ld-memory-usage)

echo "[build] directed AArch64 L1 ACE workload"
"$arm_cc" -O2 -static -fno-pie -no-pie -Wall -Wextra -Werror \
    -I"$gem5_src/include" \
    "$workload_src" "$gem5_src/util/m5/src/abi/arm64/m5op.S" \
    -o "$out_root/bin/l1_ace_workload"

if ! file "$gem5_bin" | grep -q 'x86-64'; then
    echo "FAIL: gem5 host executable is not x86-64: $gem5_bin" > /dev/stderr
    file "$gem5_bin" > /dev/stderr
    exit 1
fi
if ! file "$out_root/bin/l1_ace_workload" | grep -q 'ARM aarch64'; then
    echo "FAIL: workload is not AArch64" > /dev/stderr
    file "$out_root/bin/l1_ace_workload" > /dev/stderr
    exit 1
fi

run_case() {
    local name="$1"
    local iterations="$2"
    local out_dir="$out_root/$name"
    mkdir -p "$out_dir"
    echo "[run] $name ($iterations iterations)"
    "$gem5_bin" --outdir="$out_dir" "$config" \
        --cpu=O3 \
        --cmd="$out_root/bin/l1_ace_workload" \
        --workload_args="$name $iterations" \
        --l1_ace --l1_ace_window=workitem --l1_ace_work_id=11 \
        >"$out_dir/gem5.log" 2>&1
}

stat_value() {
    local case_name="$1"
    local cache_name="$2"
    local stat_suffix="$3"
    awk -v cache="$cache_name" -v suffix="$stat_suffix" \
        '$1 ~ (cache "\\.l1Ace\\." suffix "$") { value=$2 } END {
            if (value == "") exit 1; print value
        }' "$out_root/$case_name/stats.txt"
}

run_case reuse 128
run_case stream 1
run_case dead 1
run_case pressure 4096

reuse_ratio="$(stat_value reuse l1d-cache-0 aceRatio)"
stream_ratio="$(stat_value stream l1d-cache-0 aceRatio)"
dead_ratio="$(stat_value dead l1d-cache-0 aceRatio)"
pressure_ratio="$(stat_value pressure l1d-cache-0 aceRatio)"
dead_reads="$(stat_value dead l1d-cache-0 trackedDemandReads)"
dead_writes="$(stat_value dead l1d-cache-0 trackedDemandWrites)"
reuse_fills="$(stat_value reuse l1d-cache-0 trackedFills)"
pressure_fills="$(stat_value pressure l1d-cache-0 trackedFills)"

for case_name in reuse dead pressure stream; do
    if ! grep -qE "stream=$case_name .*status=PASS" \
        "$out_root/$case_name/gem5.log"; then
        echo "FAIL: $case_name workload result did not match expected output" \
            > /dev/stderr
        exit 1
    fi
    for cache_name in l1i-cache-0 l1d-cache-0; do
        begins="$(stat_value "$case_name" "$cache_name" windowBegins)"
        ends="$(stat_value "$case_name" "$cache_name" windowEnds)"
        cycles="$(stat_value "$case_name" "$cache_name" measuredCycles)"
        bit_cycles="$(stat_value "$case_name" "$cache_name" aceBitCycles)"
        ratio="$(stat_value "$case_name" "$cache_name" aceRatio)"
        awk -v case_name="$case_name" -v cache_name="$cache_name" \
            -v begins="$begins" -v ends="$ends" -v cycles="$cycles" \
            -v bits="$bit_cycles" -v ratio="$ratio" 'BEGIN {
            if (begins != 1 || ends != 1 || cycles <= 0) {
                printf("FAIL: invalid %s %s ROI (begins=%g ends=%g cycles=%g)\n",
                       case_name, cache_name, begins, ends, cycles) > "/dev/stderr"
                exit 1
            }
            expected = bits / (64 * 1024 * 8 * cycles)
            difference = ratio > expected ? ratio - expected : expected - ratio
            if (ratio < 0 || ratio > 1 || difference > 5e-9) {
                printf("FAIL: invalid %s %s L1 ACE formula " \
                       "(bits=%g cycles=%g ratio=%.10g expected=%.10g)\n",
                       case_name, cache_name, bits, cycles, ratio, expected) \
                       > "/dev/stderr"
                exit 1
            }
        }'
    done
done

awk -v reuse="$reuse_ratio" -v stream="$stream_ratio" 'BEGIN {
    if (!(reuse > stream)) {
        printf("FAIL: reuse L1D ACE ratio %g is not above stream ratio %g\n",
               reuse, stream) > "/dev/stderr"
        exit 1
    }
}'

awk -v reuse="$reuse_ratio" -v pressure="$pressure_ratio" 'BEGIN {
    if (!(reuse > pressure)) {
        printf("FAIL: reuse L1D ACE ratio %g is not above pressure ratio %g\n",
               reuse, pressure) > "/dev/stderr"
        exit 1
    }
}'

awk -v reads="$dead_reads" -v writes="$dead_writes" 'BEGIN {
    # Classic caches cannot filter wrong-path requests by seqNum, so a
    # store-only stream can still expose a few speculative demand reads past
    # the end marker. Require the stream to be write dominated instead of
    # claiming it has exactly zero reads.
    if (writes <= 0 || reads > writes / 1000) {
        printf("FAIL: dead-write stream reads=%g writes=%g\n", reads, writes) \
            > "/dev/stderr"
        exit 1
    }
}'

awk -v reuse="$reuse_fills" -v pressure="$pressure_fills" 'BEGIN {
    if (!(pressure > reuse)) {
        printf("FAIL: pressure fills %g are not above reuse fills %g\n",
               pressure, reuse) > "/dev/stderr"
        exit 1
    }
}'

printf '\nL1 ACE direction and formula checks passed\n'
printf '  reuse L1D ratio:       %s\n' "$reuse_ratio"
printf '  dead-write L1D ratio:  %s\n' "$dead_ratio"
printf '  pressure L1D ratio:    %s\n' "$pressure_ratio"
printf '  stream L1D ratio:      %s\n' "$stream_ratio"
printf '  dead demand reads:     %s\n' "$dead_reads"
printf '  dead demand writes:    %s\n' "$dead_writes"
printf '  reuse fills:           %s\n' "$reuse_fills"
printf '  pressure fills:        %s\n' "$pressure_fills"
printf '  outputs:               %s\n' "$out_root"
