#!/usr/bin/env bash
# =============================================================================
# tools/r6_a4_batch.sh — R6-A4 正式补救批次（仅 25 个未合格样本）
#
# 规则（用户 2026-10-28 裁决）：
#   * 只重跑 R6-A3 未合格的 25 个 (RunID, seed)；已合格的 65 格一律不碰。
#   * 每格独占 flock + 全新目录 + 原子 manifest + .done（r6_a_run_one.sh）；
#   * 最多 2 个格并发（每格内部 1 个 gem5）；
#   * 任一格失败立即停止启动新格，已在跑的格安全收尾；
#   * 输出目录 tag=_r6a4，绝不覆盖 r6a3/更早证据；
#   * 每格 TIMEOUT 按 repeat census 实测运行时间 ×2 决定（默认 300 保持历史口径）。
#
# 用法：tools/r6_a4_batch.sh            # 正常运行
#       tools/r6_a4_batch.sh --dry-run  # 只打印计划
# =============================================================================
set -uo pipefail

REPO=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
RUNS=/home/sdc/gem5-fi-ding/runs/lsu
LOG="$RUNS/r6_a4_batch.log"
TAG="_r6a4"
MAXJOBS=2

# 25 个样本：RunID:seed 逐一列出（顺序即启动优先级）
PAIRS=(
  # A01 真实 Masked 终局（checker 白名单 + 重跑）
  A01-F1-W3:2 A01-F2-W3:2
  # W9/F2 缺 census（gap_bfs 真实 repeat census 后）
  A01-F2-W9:1 A01-F2-W9:2 A01-F2-W9:3
  A02-F2-W9:1 A02-F2-W9:2 A02-F2-W9:3
  # F2 NO_FIRE（按子模型过滤后 eligible 重标定 repeat）
  A04-F2-W3:1 A04-F2-W3:3 A04-F2-W0:1 A04-F2-W0:3
  A05-F2-W3:1 A05-F2-W3:2 A05-F2-W3:3
  A06-F2-W3:3 A06-F2-W5:3
  A08-F2-W3:1 A08-F2-W3:2 A08-F2-W3:3
  A08-F2-W5:1 A08-F2-W5:2 A08-F2-W5:3
  # A07-b 真实时序终局
  A07-F0-W3:1 A07-F0-W3:2
)

# [R6-A4] per-cell SE budget (seconds).  Census-measured runtime ×2 margin;
# F2 cells that repeat a filtered stream thousands of times need more than
# the historic 300s.  Values are recorded in each manifest (timeout_seconds).
timeout_for() {
  case "$1" in
    A08-F2-*) echo 1800 ;;
    A0[4-6]-F2-*) echo 1200 ;;
    A0[12]-F2-W9) echo 900 ;;
    *) echo 300 ;;
  esac
}

if [ "${1:-}" = "--dry-run" ]; then
  n=0
  for p in "${PAIRS[@]}"; do
    rid="${p%%:*}"; s="${p##*:}"
    echo "$rid seed$s timeout=$(timeout_for "$rid") -> $RUNS/r6_a${TAG}_${rid}_s${s}"; n=$((n+1))
  done
  echo "TOTAL=$n"
  exit 0
fi

mkdir -p "$RUNS"
log() { echo "[$(date -Is)] $*" | tee -a "$LOG" >&2; }

# 证据保护：任何目标目录已存在即拒绝整批启动（绝不覆盖）。
for p in "${PAIRS[@]}"; do
  rid="${p%%:*}"; s="${p##*:}"
  out="$RUNS/r6_a${TAG}_${rid}_s${s}"
  if [ -e "$out" ]; then
    log "REFUSED: $out already exists — 保护证据，先人工检查（不删除、不覆盖）"
    exit 6
  fi
done

log "BATCH START tag=$TAG samples=${#PAIRS[@]} maxjobs=$MAXJOBS"
log "binary=$(sha256sum "$REPO/CHAOS/gem5/build/ARM/gem5.opt" | awk '{print $1}') head=$(git -C "$REPO" rev-parse HEAD)"

pids=()
names=()
failed=0
running=0

launch() {
  local rid="$1" seed="$2"
  local out="$RUNS/r6_a${TAG}_${rid}_s${seed}"
  OUT_TAG="$TAG" TIMEOUT="$(timeout_for "$rid")" setsid \
      "$REPO/tools/r6_a_run_one.sh" "$rid" "$seed" >>"$LOG" 2>&1 &
  pids+=($!); names+=("$rid|$seed")
  running=$((running+1))
  log "LAUNCH $rid s$seed pid=$! timeout=$(timeout_for "$rid")"
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

for p in "${PAIRS[@]}"; do
  rid="${p%%:*}"; s="${p##*:}"
  while [ "$running" -ge "$MAXJOBS" ]; do wait_one; done
  if [ "$failed" -ne 0 ]; then
    log "ABORT: a cell failed; not launching any new cells"
    break
  fi
  launch "$rid" "$s"
done

while [ "$running" -gt 0 ]; do wait_one; done
log "BATCH END failed=$failed"
exit "$failed"
