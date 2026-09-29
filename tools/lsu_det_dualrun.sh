#!/usr/bin/env bash
# lsu_det_dualrun.sh — 家族确定性双跑驱动（G0-02 连续验证，ENGINEERING_ONLY）
#
# 用法:
#   tools/lsu_det_dualrun.sh <RUN_ID> <ITEM_ID> <INJ_LOG> <WORKLOAD_BIN> <SEED_FLAG> <SPAN_FLAG> -- <注入参数...>
# 例:
#   tools/lsu_det_dualrun.sh S01-F0-W5 ITEM-071 lsq_fwd_injections.log sq_forward \
#       --rng_seed --lsqfwd_span_events -- \
#       --chaos_lsqfwd --lsq_struct_mode byte_flip --lsqfwd_lsu_tier F0 \
#       --lsqfwd_warmup_events 0 --lsqfwd_span_events AUTO --max_faults 1
#
# F0 span=AUTO：先跑守卫计数 pass（span=INT64_MAX 永不触发 → 读全流 eligible 数 N），
# 再以 span=N 双跑——“窗口均匀”在 span=N 时精确等于 Excel F0“全流均匀”语义
# （在线无偏单点抽样不存在，两遍法是唯一精确实现；F-012）。
#
# 退出码：0=DETERMINISM PASS，1=比较 FAIL，2=vacuous（未注入），3=运行/参数失败。
set -uo pipefail
RID=$1; ITEM=$2; INJLOG=$3; WL=$4; SEEDFLAG=$5; SPANFLAG=$6
shift 6; [ "${1:-}" = "--" ] && shift
INJARGS=("$@")

if [ "$SPANFLAG" != "none" ] && ! printf '%s\n' "${INJARGS[@]}" | grep -qx "AUTO"; then
  echo "用法错误：注入参数中需含 'AUTO'（$SPANFLAG 的值）以启用 F0 计数" >&2
  exit 3
fi

SEED=$(python3 tools/lsu_seed.py --run-id "$RID" --phase engineering --sample-index 0) || exit 3
GSHA=$(sha256sum build/ARM/gem5.opt | cut -d' ' -f1)
WSHA=$(sha256sum "workloads/directed/$WL" | cut -d' ' -f1)
PSHA=$(sha256sum configs/se/lsu_proxy.py | cut -d' ' -f1)
GIT=$(git rev-parse HEAD)
DETDIR=runs/lsu/det/$RID
EVDIR=docs/gem5-fi/lsu/evidence/P1/det
mkdir -p "$DETDIR" "$EVDIR"

# ---- Pass 0: 计数（span=INT64_MAX 永不触发，读全流 eligible 数）----
N=""
if [ "$SPANFLAG" != "none" ]; then
  CNTARGS=()
  for a in "${INJARGS[@]}"; do [ "$a" = "AUTO" ] && CNTARGS+=("9223372036854775807") || CNTARGS+=("$a"); done
  echo "=== 计数 pass（$(date +%H:%M:%S)，span=INT64_MAX 永不注入）==="
  rm -rf "$DETDIR/count"
  python3 tools/lsu_guard.py run --type experiment \
      --desc "DET-count $RID (ENGINEERING_ONLY, F0 stream census)" \
      --log "runs/lsu/guard/det_${RID}_count_rsrc.log" --interval 60 --max-seconds 600 -- \
      build/ARM/gem5.opt --outdir="$DETDIR/count" configs/se/lsu_proxy.py \
      --cmd "workloads/directed/$WL" --cpu O3 --variant B0 \
      "${CNTARGS[@]}" "$SEEDFLAG" "$SEED" \
      > "/tmp/det_${RID}_count.out" 2>&1
  CNT_RC=$?
  N=$(grep -oE "CHAOS_LSU_TRIGGER: .*eligible=[0-9]+" "/tmp/det_${RID}_count.out" | grep -oE "[0-9]+$" | head -1)
  if [ -z "$N" ] || [ "$N" -le 0 ]; then
    echo "计数失败：无 eligible 事件或触发层摘要缺失（CNT_RC=$CNT_RC）"; exit 3
  fi
  echo "全流 eligible 事件数 N=$N → 正式 span=$N"
else
  echo "（legacy 家族：无 span 参数，跳过计数 pass）"
  SPANNOTE="legacy 时钟窗机制（lsuTier 参数 wire-ready 未消费），无 span/计数 pass"
fi

# ---- 冻结 manifest（含计数结果）----
FINALARGS=()
for a in "${INJARGS[@]}"; do FINALARGS+=("$a"); done
# 替换 AUTO -> N（INJARGS 原数组保留 AUTO 的位置）
MANIFEST="$EVDIR/${RID}_eng_det_manifest.json"
cat > "$MANIFEST" <<EOF
{
  "frozen": true,
  "purpose": "ENGINEERING_ONLY 家族确定性双跑（G0-02）——不进入正式统计",
  "item": "$ITEM", "run_id": "$RID",
  "phase": "engineering", "sample_index": 0, "seed": $SEED,
  "seed_rule": "sha256('lsu-fi-v1|$RID|engineering|0') 低64位 digest[24:32] 大端（tools/lsu_seed.py）",
  "identity": {"git_commit": "$GIT", "gem5_opt_sha256": "$GSHA",
               "lsu_proxy_sha256": "$PSHA",
               "workload": "workloads/directed/$WL", "workload_sha256": "$WSHA"},
  "config": {"cpu": "O3", "variant": "B0", "checkpoint": "none (SE)"},
  "f0_span_rule": "${SPANNOTE:-两遍法（F-012）：计数 pass（span=INT64_MAX）实测全流 eligible=$N，正式 span=$N == Excel F0 全流均匀语义}",
  "injector_args": $(python3 -c "
import json, sys
args = sys.argv[1:-1] if len(sys.argv) > 1 else []
if 'AUTO' in args:
    args[args.index('AUTO')] = sys.argv[-1]
print(json.dumps(args, ensure_ascii=False))" "${INJARGS[@]}" "$SEEDFLAG" "$SEED" "$N"),
  "timeout": {"wall_seconds_per_run": 600, "mechanism": "lsu_guard --max-seconds"},
  "runs": {"count": "$DETDIR/count", "run1": "$DETDIR/run1", "run2": "$DETDIR/run2"},
  "serial_execution": "守卫 experiment 锁严格串行（count→run1→run2）"
}
EOF
echo "manifest 冻结: $MANIFEST (seed=$SEED, span=$N)"

# ---- 双跑 ----
RUNARGS=()
for a in "${INJARGS[@]}"; do [ "$a" = "AUTO" ] && RUNARGS+=("$N") || RUNARGS+=("$a"); done
for N_RUN in 1 2; do
  rm -rf "$DETDIR/run$N_RUN"
  echo "=== run$N_RUN 启动（$(date +%H:%M:%S)）==="
  python3 tools/lsu_guard.py run --type experiment \
      --desc "DET $RID run$N_RUN-of-2 (ENGINEERING_ONLY, G0-02)" \
      --log "runs/lsu/guard/det_${RID}_run${N_RUN}_rsrc.log" --interval 60 --max-seconds 600 -- \
      build/ARM/gem5.opt --outdir="$DETDIR/run$N_RUN" configs/se/lsu_proxy.py \
      --cmd "workloads/directed/$WL" --cpu O3 --variant B0 \
      "${RUNARGS[@]}" "$SEEDFLAG" "$SEED" \
      > "/tmp/det_${RID}_run${N_RUN}.out" 2>&1
  echo "run$N_RUN 守卫退出码 $?（exit_code 进 C5）"
  tail -1 "/tmp/det_${RID}_run${N_RUN}.out"
done

echo "=== 语义比较 ==="
python3 tools/lsu_det_compare.py --run-id "$RID" --log-name "$INJLOG" \
    --r1 "$DETDIR/run1" --r2 "$DETDIR/run2" \
    --g1 "/tmp/det_${RID}_run1.out" --g2 "/tmp/det_${RID}_run2.out" \
    2>&1 | tee "$EVDIR/${RID}_det_report.txt"
exit "${PIPESTATUS[0]}"
