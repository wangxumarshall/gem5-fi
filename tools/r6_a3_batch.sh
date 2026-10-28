#!/usr/bin/env bash
# =============================================================================
# tools/r6_a3_batch.sh — R6-A3 正式批次驱动（30 个非 F6 RunID × seed1/2/3）
#
# 规则（与工作令一致）：
#   * 每格独占锁 + 独立输出目录 + 原子 manifest + .done（r6_a_run_one.sh）；
#   * 最多 2 个格并发（每个格内部 1 个 gem5）；
#   * **任一格失败（非 0 退出 / 缺 .done）立即停止启动新格**，已在跑的格安全收尾；
#   * 全新输出目录（OUT_TAG=_r6a3），绝不覆盖旧证据；
#   * 所有动作写入 runs/lsu/r6_a3_batch.log（主检出证据根）。
#
# 用法：tools/r6_a3_batch.sh            # 正常运行
#       tools/r6_a3_batch.sh --dry-run  # 只打印计划
# =============================================================================
set -uo pipefail

REPO=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
RUNS=/home/sdc/gem5-fi-ding/runs/lsu
LOG="$RUNS/r6_a3_batch.log"
TAG="_r6a3"
MAXJOBS=2

RUNIDS=(
  A01-F0-W3 A01-F0-W9 A01-F1-W3 A01-F1-W9 A01-F2-W3 A01-F2-W9
  A02-F0-W3 A02-F0-W9 A02-F2-W3 A02-F2-W9
  A03-F5-W3 A03-F5-W10
  A04-F0-W3 A04-F0-W0 A04-F2-W3 A04-F2-W0
  A05-F0-W3 A05-F2-W3
  A06-F0-W3 A06-F0-W5 A06-F2-W3 A06-F2-W5
  A07-F0-W3 A07-F0-W5 A07-F4-W3 A07-F4-W5
  A08-F0-W3 A08-F0-W5 A08-F2-W3 A08-F2-W5
)
SEEDS=(1 2 3)

if [ "${1:-}" = "--dry-run" ]; then
  n=0
  for r in "${RUNIDS[@]}"; do for s in "${SEEDS[@]}"; do
    echo "$r seed$s -> $RUNS/r6_a${TAG}_${r}_s${s}"; n=$((n+1)); done; done
  echo "TOTAL=$n"; exit 0
fi

mkdir -p "$RUNS"
log() { echo "[$(date -Is)] $*" | tee -a "$LOG" >&2; }

log "BATCH START tag=$TAG runids=${#RUNIDS[@]} seeds=${#SEEDS[@]} maxjobs=$MAXJOBS"
log "binary=$(sha256sum "$REPO/CHAOS/gem5/build/ARM/gem5.opt" | awk '{print $1}') head=$(git -C "$REPO" rev-parse HEAD)"

pids=()
names=()
failed=0
running=0

launch() {
  local rid="$1" seed="$2"
  local out="$RUNS/r6_a${TAG}_${rid}_s${seed}"
  if [ -e "$out/.done" ]; then
    log "SKIP $rid s$seed (already .done present)"
    return 0
  fi
  OUT_TAG="$TAG" setsid "$REPO/tools/r6_a_run_one.sh" "$rid" "$seed" \
      >>"$LOG" 2>&1 &
  pids+=($!); names+=("$rid|$seed")
  log "LAUNCH $rid s$seed pid=$!"
}

wait_one() {
  local pid="${pids[0]}"; local nm="${names[0]}"
  wait "$pid"; local rc=$?
  pids=("${pids[@]:1}"); names=("${names[@]:1}")
  running=$((running-1))
  local rid="${nm%%|*}"; local seed="${nm##*|}"
  local out="$RUNS/r6_a${TAG}_${rid}_s${seed}"
  if [ "$rc" -ne 0 ] || [ ! -e "$out/.done" ]; then
    failed=1
    log "FAIL $rid s$seed rc=$rc done=$([ -e "$out/.done" ] && echo yes || echo no) — STOP LAUNCHING NEW CELLS"
  else
    log "OK $rid s$seed"
  fi
}

for r in "${RUNIDS[@]}"; do
  for s in "${SEEDS[@]}"; do
    [ "$failed" = "1" ] && break 2
    while [ "$running" -ge "$MAXJOBS" ]; do wait_one; done
    launch "$r" "$s"
    running=$((running+1))
  done
done
while [ "$running" -gt 0 ]; do wait_one; done

if [ "$failed" = "1" ]; then
  log "BATCH STOPPED WITH FAILURE (in-flight cells allowed to finish)"
  exit 1
fi

# ---- completion census: every cell must have .done + manifest FINISHED ----
missing=0
for r in "${RUNIDS[@]}"; do for s in "${SEEDS[@]}"; do
  out="$RUNS/r6_a${TAG}_${r}_s${s}"
  if [ ! -e "$out/.done" ]; then log "MISSING .done $r s$s"; missing=$((missing+1)); fi
done; done
log "BATCH COMPLETE missing=$missing"
[ "$missing" -eq 0 ] || exit 1
