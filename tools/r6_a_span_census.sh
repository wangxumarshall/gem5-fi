#!/usr/bin/env bash
# =============================================================================
# tools/r6_a_span_census.sh — A 单元 addrpath F0 eligible-stream census
#
# 无注入（span=1e6 大于任何 golden 流，F0 抽签永不落地），读取 CHAOSAddrPath
# 退出摘要的 attempted/eligible 作为实测 golden 流长；结果写入
# runs/lsu/r6_a_census/<model>_<workload>/run.out，并打印一行 TSV。
#
# 用法：tools/r6_a_span_census.sh [pair ...]
#   pair 形如 A01:agu_addrmodes（默认跑下面全部 A 单元 F0 对）
# =============================================================================
set -uo pipefail

REPO=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
MAIN=/home/sdc/gem5-fi-ding
BIN="$REPO/CHAOS/gem5/build/ARM/gem5.opt"
ROOT="$MAIN/runs/lsu/r6_a_census"
mkdir -p "$ROOT"

mode_flags() {
    case "$1" in
        A01) echo "--addrpath_mode a01_bit" ;;
        A02) echo "--addrpath_mode a02_2bit" ;;
        A04) echo "--agu_pre_mode a04_subst" ;;
        A05) echo "--agu_pre_mode a05_shift" ;;
        A08) echo "--agu_pre_mode a08_subst" ;;
        A06) echo "--agu_pre_mode a06_size --agu_size_to 2 --agu_size_to_load 8" ;;
        *) return 1 ;;
    esac
}

PAIRS=("$@")
if [ ${#PAIRS[@]} -eq 0 ]; then
    PAIRS=(A01:agu_addrmodes A01:gap_bfs A02:agu_addrmodes A02:gap_bfs \
           A04:agu_addrmodes A04:mini_check A05:agu_addrmodes A08:agu_addrmodes)
fi

for pair in "${PAIRS[@]}"; do
    model="${pair%%:*}"; wl="${pair##*:}"
    out="$ROOT/${model}_${wl}"
    if [ -e "$out/.done" ]; then
        echo "SKIP(done) $model $wl"
        continue
    fi
    mkdir -p "$out"
    flags=$(mode_flags "$model") || { echo "SKIP(unknown model) $model"; continue; }
    timeout 600 "$BIN" --outdir "$out" "$REPO/configs/se/lsu_proxy.py" \
        --cmd "$REPO/workloads/directed/$wl" --cpu O3 --chaos_addrpath \
        --addrpath_lsu_tier F0 --addrpath_warmup_events 1 \
        --addrpath_span_events 1000000 $flags \
        >"$out/run.out" 2>"$out/run.err"
    rc=$?
    line=$(grep -o "CHAOS_LSU_TRIGGER: injector=CHAOSAddrPath tier=F0 attempted=[0-9]* eligible=[0-9]* injected=[0-9]*" "$out/run.out" | tail -1)
    if [ -z "$line" ]; then
        echo "FAIL $model $wl rc=$rc (no summary; see $out/run.err)"
        continue
    fi
    attempted=$(sed -n 's/.*attempted=\([0-9]*\).*/\1/p' <<<"$line")
    eligible=$(sed -n 's/.*eligible=\([0-9]*\).*/\1/p' <<<"$line")
    injected=$(sed -n 's/.*injected=\([0-9]*\).*/\1/p' <<<"$line")
    if [ "$injected" != "0" ]; then
        echo "FAIL $model $wl injected=$injected (census must not fire)"
        continue
    fi
    printf '%s\n' "$rc" > "$out/.done"
    printf '%s\t%s\t%s\t%s\n' "$model" "$wl" "$attempted" "$eligible"
done
