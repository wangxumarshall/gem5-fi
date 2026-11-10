#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gem5_src="$repo_root/CHAOS/gem5"
gem5_build_name="${GEM5_BUILD_NAME:-ARM_X86_HOST}"
gem5_build_rel="build/$gem5_build_name"
gem5_build_dir="$gem5_src/$gem5_build_rel"
gem5_bin="${GEM5_OPT:-$gem5_build_dir/gem5.opt}"
config="$repo_root/configs/se/arm_chaos.py"
workload_src="$repo_root/workloads/directed/rf_ace_workload.c"
out_root="${RF_ACE_OUT:-$repo_root/m5out/rf-ace-test-arm}"
jobs="${JOBS:-2}"
arm_cc="${ARM_CC:-aarch64-linux-gnu-gcc}"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
    # init-env.sh is intended for interactive shells.  In CI/non-interactive
    # shells conda's shell hook may not be loaded, so use the known environment
    # directly when it is available and retain init-env.sh as a fallback.
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

echo "[build] directed AArch64 RF ACE workload"
"$arm_cc" -O2 -static -fno-pie -no-pie -Wall -Wextra -Werror \
    -I"$gem5_src/include" \
    "$workload_src" "$gem5_src/util/m5/src/abi/arm64/m5op.S" \
    -o "$out_root/bin/rf_ace_workload"

if ! file "$gem5_bin" | grep -Eq 'x86-64|ARM aarch64'; then
    echo "FAIL: gem5 executable is neither x86-64 nor ARM aarch64: $gem5_bin" > /dev/stderr
    file "$gem5_bin" > /dev/stderr
    exit 1
fi
if ! file "$out_root/bin/rf_ace_workload" | grep -q 'ARM aarch64'; then
    echo "FAIL: workload is not AArch64" > /dev/stderr
    file "$out_root/bin/rf_ace_workload" > /dev/stderr
    exit 1
fi

run_case() {
    local output_name="$1"
    local stream="$2"
    local iterations="$3"
    local granularity="$4"
    local out_dir="$out_root/$output_name"
    mkdir -p "$out_dir"
    echo "[run] $output_name: $stream/$granularity ($iterations iterations)"
    "$gem5_bin" --outdir="$out_dir" "$config" \
        --cpu=O3 \
        --cmd="$out_root/bin/rf_ace_workload" \
        --workload_args="$stream $iterations" \
        --rf_ace --rf_ace_window=workitem --rf_ace_work_id=7 \
        --rf_ace_granularity="$granularity" \
        >"$out_dir/gem5.log" 2>&1
}

stat_value() {
    local case_name="$1"
    local stat_suffix="$2"
    awk -v suffix="$stat_suffix" \
        '$1 ~ ("rfAce\\." suffix "$") { value=$2 } END {
            if (value == "") exit 1; print value
        }' "$out_root/$case_name/stats.txt"
}

run_case chain chain 20000 whole
run_case dead dead 20000 whole
run_case pressure pressure 20000 whole
run_case squash squash 200 whole
run_case bit-width32 width32 20000 bit
run_case bit-width64 width64 20000 bit
run_case whole-width32 width32 20000 whole
run_case whole-width64 width64 20000 whole

chain_ratio="$(stat_value chain intAceRatio)"
dead_ratio="$(stat_value dead intAceRatio)"
pressure_ratio="$(stat_value pressure intAceRatio)"
squash_discards="$(stat_value squash intSquashDiscards)"
squash_writes="$(stat_value squash intTrackedWrites)"
dead_writes_count="$(stat_value dead intTrackedWrites)"
bit_width32_ratio="$(stat_value bit-width32 intAceRatio)"
bit_width64_ratio="$(stat_value bit-width64 intAceRatio)"
bit_width32_total="$(stat_value bit-width32 intAceBitCycles)"
bit_width64_total="$(stat_value bit-width64 intAceBitCycles)"
bit_width32_low="$(stat_value bit-width32 intAceBitCyclesLow32)"
bit_width64_low="$(stat_value bit-width64 intAceBitCyclesLow32)"
bit_width32_high="$(stat_value bit-width32 intAceBitCyclesHigh32)"
bit_width64_high="$(stat_value bit-width64 intAceBitCyclesHigh32)"
whole_width32_ratio="$(stat_value whole-width32 intAceRatio)"
whole_width64_ratio="$(stat_value whole-width64 intAceRatio)"

for case_name in chain dead pressure squash; do
    if ! grep -qE "stream=$case_name .*status=PASS" \
        "$out_root/$case_name/gem5.log"; then
        echo "FAIL: $case_name workload result did not match expected output" \
            > /dev/stderr
        exit 1
    fi
    begins="$(stat_value "$case_name" windowBegins)"
    ends="$(stat_value "$case_name" windowEnds)"
    cycles="$(stat_value "$case_name" measuredCycles)"
    writes="$(stat_value "$case_name" intTrackedWrites)"
    awk -v name="$case_name" -v begins="$begins" -v ends="$ends" \
        -v cycles="$cycles" -v writes="$writes" 'BEGIN {
        if (begins != 1 || ends != 1 || cycles <= 0 || writes <= 0) {
            printf("FAIL: invalid %s ROI (begins=%g ends=%g cycles=%g writes=%g)\n",
                   name, begins, ends, cycles, writes) > "/dev/stderr"
            exit 1
        }
    }'
done

for case_name in bit-width32 bit-width64 whole-width32 whole-width64; do
    stream="${case_name#*-}"
    if ! grep -qE "stream=$stream .*status=PASS" \
        "$out_root/$case_name/gem5.log"; then
        echo "FAIL: $case_name workload result did not match expected output" \
            > /dev/stderr
        exit 1
    fi
    expected_granularity=0
    if [[ "$case_name" == bit-* ]]; then
        expected_granularity=1
    fi
    actual_granularity="$(stat_value "$case_name" bitGranularity)"
    if [[ "$actual_granularity" != "$expected_granularity" ]]; then
        echo "FAIL: $case_name granularity flag is $actual_granularity, expected $expected_granularity" \
            > /dev/stderr
        exit 1
    fi
done

for case_name in chain dead pressure squash bit-width32 bit-width64 \
                 whole-width32 whole-width64; do
    bit_cycles="$(stat_value "$case_name" intAceBitCycles)"
    measured_cycles="$(stat_value "$case_name" measuredCycles)"
    ratio="$(stat_value "$case_name" intAceRatio)"
    awk -v name="$case_name" -v bits="$bit_cycles" \
        -v cycles="$measured_cycles" -v ratio="$ratio" 'BEGIN {
        expected = bits / (256 * 64 * cycles)
        difference = ratio > expected ? ratio - expected : expected - ratio
        if (ratio < 0 || ratio > 1 || difference > 5e-9) {
            printf("FAIL: invalid %s RF ACE formula " \
                   "(bits=%g cycles=%g ratio=%.10g expected=%.10g)\n",
                   name, bits, cycles, ratio, expected) > "/dev/stderr"
            exit 1
        }
    }'
done

awk -v total32="$bit_width32_total" -v low32="$bit_width32_low" \
    -v high32="$bit_width32_high" -v total64="$bit_width64_total" \
    -v low64="$bit_width64_low" -v high64="$bit_width64_high" 'BEGIN {
    if (total32 != low32 + high32 || total64 != low64 + high64) {
        printf("FAIL: low/high bit-cycle totals do not balance " \
               "(W: %g != %g + %g; X: %g != %g + %g)\n",
               total32, low32, high32, total64, low64, high64) \
               > "/dev/stderr"
        exit 1
    }
}'

awk -v chain="$chain_ratio" -v dead="$dead_ratio" 'BEGIN {
    if (!(chain > dead)) {
        printf("FAIL: dependency chain ratio %g is not above dead-write ratio %g\n",
               chain, dead) > "/dev/stderr"; exit 1
    }
}'

awk -v pressure="$pressure_ratio" -v chain="$chain_ratio" 'BEGIN {
    if (!(pressure < chain)) {
        printf("FAIL: pressure ratio %g is not below dependency ratio %g\n",
               pressure, chain) > "/dev/stderr"; exit 1
    }
}'

awk -v discards="$squash_discards" 'BEGIN {
    if (!(discards > 0)) {
        print "FAIL: wrong-path stream produced no squash discards" > "/dev/stderr"
        exit 1
    }
}'

awk -v narrow="$bit_width32_ratio" -v wide="$bit_width64_ratio" 'BEGIN {
    if (!(narrow < wide)) {
        printf("FAIL: bit-level W ratio %g is not below X ratio %g\n",
               narrow, wide) > "/dev/stderr"; exit 1
    }
}'

awk -v narrow="$bit_width32_high" -v wide="$bit_width64_high" 'BEGIN {
    if (!(narrow < wide)) {
        printf("FAIL: W high-bit cycles %g are not below X high-bit cycles %g\n",
               narrow, wide) > "/dev/stderr"; exit 1
    }
}'

awk -v narrow="$whole_width32_ratio" -v wide="$whole_width64_ratio" 'BEGIN {
    scale = narrow > wide ? narrow : wide
    difference = narrow > wide ? narrow - wide : wide - narrow
    if (scale == 0 || difference / scale > 0.02) {
        printf("FAIL: whole-word W/X ratios differ by more than 2%% (%g vs %g)\n",
               narrow, wide) > "/dev/stderr"; exit 1
    }
}'

# The wrong-path block contains 192 writes per iteration. They must not appear
# as committed tracked writes; allow ordinary loop/control differences.
awk -v squash="$squash_writes" -v dead="$dead_writes_count" 'BEGIN {
    if (squash > dead) {
        printf("FAIL: squashed writes leaked into committed count (%g > %g)\n",
               squash, dead) > "/dev/stderr"; exit 1
    }
}'

printf '\nRF ACE direction and formula checks passed\n'
printf '  chain ratio:          %s\n' "$chain_ratio"
printf '  dead-write ratio:     %s\n' "$dead_ratio"
printf '  pressure ratio:       %s\n' "$pressure_ratio"
printf '  squash discards:      %s\n' "$squash_discards"
printf '  squash tracked writes:%s\n' "$squash_writes"
printf '  bit W/X ratios:        %s / %s\n' \
    "$bit_width32_ratio" "$bit_width64_ratio"
printf '  bit W/X high cycles:   %s / %s\n' \
    "$bit_width32_high" "$bit_width64_high"
printf '  whole W/X ratios:      %s / %s\n' \
    "$whole_width32_ratio" "$whole_width64_ratio"
printf '  outputs:              %s\n' "$out_root"
