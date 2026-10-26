#!/bin/bash
# [LSU][P4-FIX-VALIDATE] 修复轮小样本验证运行器（阶段1 n=2 / 阶段2 n=30）。
# 用法：tools/lsu_p4fix_validate.sh stage1|stage2 [classes...]
# 约束：绝不写 runs/（outdir 全部 /tmp/lsu_p4fix_val/）；gem5 并发 ≤4；
#       只用本 worktree 的二进制与 configs（绝不触碰主仓冻结二进制）。
set -u
WT=$(cd "$(dirname "$0")/.." && pwd)
BIN=$WT/CHAOS/gem5/build/ARM/gem5.opt
CFG=$WT/configs/se/lsu_proxy.py
[ -x "$BIN" ] || { echo "FATAL: worktree binary missing: $BIN"; exit 1; }
STAGE=${1:?stage1|stage2}
shift || true
BASE=/tmp/lsu_p4fix_val/$STAGE
mkdir -p "$BASE"
N=2; [ "$STAGE" = stage2 ] && N=30
PAR=4

run_one() {  # run_one <class> <idx> <outdir> [args...]
  local cls=$1 idx=$2 out=$3; shift 3
  mkdir -p "$out"
  ( timeout 300 "$BIN" --outdir="$out" "$CFG" "$@" \
      > "$out/stdout.txt" 2> "$out/stderr.txt"; echo $? > "$out/exit_code" ) &
  while [ "$(jobs -rp | wc -l)" -ge "$PAR" ]; do wait -n; done
}

summarize_one() {  # summarize_one <class> <idx> <outdir>
  local cls=$1 idx=$2 out=$3
  local ec=$(cat "$out/exit_code" 2>/dev/null || echo NA)
  local inj=""
  [ -f "$out/addrpath_injections.log" ] && inj=$(grep -c "^Tick:" "$out/addrpath_injections.log" 2>/dev/null)
  local f6mode=$(grep -m1 "CHAOS_LSU_F6MODE" "$out/stdout.txt" 2>/dev/null)
  local trig=$(grep -m1 "CHAOS_LSU_TRIGGER" "$out/stdout.txt" 2>/dev/null)
  local decl=$(grep -m1 "CHAOS_L0_DECLINE" "$out/stdout.txt" 2>/dev/null)
  local injline=$(grep -m1 "^Tick:" "$out/addrpath_injections.log" 2>/dev/null | cut -c1-220)
  local rejects=$(grep -c "REJECT" "$out/addrpath_injections.log" 2>/dev/null)
  local sizeofa=$(grep -c "sizeof(T) <= size" "$out/stderr.txt" "$out/stdout.txt" 2>/dev/null | paste -sd+ | bc 2>/dev/null)
  local blk=$(grep -c "getOffset(blkSize)" "$out/stderr.txt" "$out/stdout.txt" 2>/dev/null | paste -sd+ | bc 2>/dev/null)
  echo "[$cls s$idx] exit=$ec inj=${inj:-0} rejects=${rejects:-0} sizeof_assert=${sizeofa:-0} blk_assert=${blk:-0}"
  [ -n "$injline" ] && echo "    inj: $injline"
  [ -n "$f6mode" ] && echo "    $f6mode"
  [ -n "$decl" ] && echo "    $decl"
  [ -n "$trig" ] && echo "    $trig"
}

# ---- 类定义（与计划 Task 7 一致）----
ALL_CLASSES="a06s_store a06s_f6 geom f6e f6s"
CLASSES=${@:-$ALL_CLASSES}
SEEDBASE=202610150000

for cls in $CLASSES; do
  for i in $(seq 1 "$N"); do
    seed=$((SEEDBASE + i))
    out=$BASE/${cls}_s$i
    case $cls in
      a06s_store)  # A06S store 注入：F0 + a06s，agu_addrmodes（W3 载体）
        run_one $cls $i $out --cmd "$WT/workloads/directed/agu_addrmodes" --cpu O3 --variant B0 \
          --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a06s_store_size \
          --agu_size_to 2 --addrpath_lsu_tier F0 --addrpath_warmup_events 0 \
          --addrpath_span_events 1000 --addrpath_rng_seed $seed ;;
      a06s_f6)     # A06S load 拒斥（F6 armed 后遇 load）：F6 + a06s
        run_one $cls $i $out --cmd "$WT/workloads/directed/agu_addrmodes" --cpu O3 --variant B0 \
          --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a06s_store_size \
          --agu_size_to 2 --addrpath_lsu_tier F6 --addrpath_f6_event sq_forward \
          --addrpath_rng_seed $seed ;;
      geom)        # 翻译位翻转载入 64B 防护：a01_bit F0
        run_one $cls $i $out --cmd "$WT/workloads/directed/agu_addrmodes" --cpu O3 --variant B0 \
          --chaos_addrpath --addrpath_mode a01_bit --addrpath_lsu_tier F0 \
          --addrpath_warmup_events 0 --addrpath_span_events 1000 --addrpath_rng_seed $seed ;;
      f6e)         # F6 early-stress（语义=旧）
        run_one $cls $i $out --cmd "$WT/workloads/directed/sq_forward" --cpu O3 --variant B0 \
          --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a08_subst \
          --addrpath_lsu_tier F6 --addrpath_f6_event sq_forward \
          --addrpath_f6_mode early_stress --addrpath_rng_seed $seed ;;
      f6s)         # F6 steady-state（warmup=W，span 窗口内随机事件）
        run_one $cls $i $out --cmd "$WT/workloads/directed/sq_forward" --cpu O3 --variant B0 \
          --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a08_subst \
          --addrpath_lsu_tier F6 --addrpath_f6_event sq_forward \
          --addrpath_f6_mode steady_state --addrpath_warmup_events ${F6S_WARMUP:-1000} \
          --addrpath_span_events 1000 --addrpath_rng_seed $seed ;;
      *) echo "unknown class $cls"; exit 2 ;;
    esac
  done
done
wait

# ---- 汇总 ----
SUM=$BASE/summary.txt
: > "$SUM"
for cls in $CLASSES; do
  for i in $(seq 1 "$N"); do
    summarize_one $cls $i $BASE/${cls}_s$i
  done
done | tee "$SUM"

# ---- 同 seed 确定性抽验（每真跑类 s1 双跑对比）----
if [ "${DETERMINISM_CHECK:-1}" = "1" ]; then
  echo "==== determinism (rerun s1 with same seed) ====" | tee -a "$SUM"
  for cls in $CLASSES; do
    case $cls in
      a06s_store) ARGS="--cmd $WT/workloads/directed/agu_addrmodes --cpu O3 --variant B0 --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a06s_store_size --agu_size_to 2 --addrpath_lsu_tier F0 --addrpath_warmup_events 0 --addrpath_span_events 1000 --addrpath_rng_seed $((SEEDBASE+1))" ;;
      a06s_f6)    ARGS="--cmd $WT/workloads/directed/agu_addrmodes --cpu O3 --variant B0 --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a06s_store_size --agu_size_to 2 --addrpath_lsu_tier F6 --addrpath_f6_event sq_forward --addrpath_rng_seed $((SEEDBASE+1))" ;;
      geom)       ARGS="--cmd $WT/workloads/directed/agu_addrmodes --cpu O3 --variant B0 --chaos_addrpath --addrpath_mode a01_bit --addrpath_lsu_tier F0 --addrpath_warmup_events 0 --addrpath_span_events 1000 --addrpath_rng_seed $((SEEDBASE+1))" ;;
      f6e)        ARGS="--cmd $WT/workloads/directed/sq_forward --cpu O3 --variant B0 --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a08_subst --addrpath_lsu_tier F6 --addrpath_f6_event sq_forward --addrpath_f6_mode early_stress --addrpath_rng_seed $((SEEDBASE+1))" ;;
      f6s)        ARGS="--cmd $WT/workloads/directed/sq_forward --cpu O3 --variant B0 --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a08_subst --addrpath_lsu_tier F6 --addrpath_f6_event sq_forward --addrpath_f6_mode steady_state --addrpath_warmup_events ${F6S_WARMUP:-1000} --addrpath_span_events 1000 --addrpath_rng_seed $((SEEDBASE+1))" ;;
    esac
    out2=$BASE/${cls}_s1_rerun
    mkdir -p "$out2"
    timeout 300 "$BIN" --outdir="$out2" "$CFG" $ARGS > "$out2/stdout.txt" 2> "$out2/stderr.txt"
    echo $? > "$out2/exit_code"
    # stats.txt 的 host_*（hostSeconds/hostTickRate/hostInstRate/hostOpRate）
    # 是宿主实时性能指标，天然逐次波动——确定性判定排除之，只比仿真本体。
    grep -v "^host" "$BASE/${cls}_s1/stats.txt" 2>/dev/null > /tmp/p4fix_a.$$
    grep -v "^host" "$out2/stats.txt" 2>/dev/null > /tmp/p4fix_b.$$
    ea=$(cat "$BASE/${cls}_s1/exit_code"); eb=$(cat "$out2/exit_code")
    if cmp -s /tmp/p4fix_a.$$ /tmp/p4fix_b.$$ && [ "$ea" = "$eb" ]; then
      echo "[$cls] DETERMINISTIC (exit=$ea, sim-stats identical excl host_* lines)" | tee -a "$SUM"
    else
      echo "[$cls] *** NON-DETERMINISTIC *** (exit $ea vs $eb)" | tee -a "$SUM"
      diff /tmp/p4fix_a.$$ /tmp/p4fix_b.$$ | head -5 | tee -a "$SUM"
    fi
    rm -f /tmp/p4fix_a.$$ /tmp/p4fix_b.$$
  done
fi

# ---- a06 退役冒烟（config 期必须响亮失败）----
echo "==== retired a06_size config rejection ====" | tee -a "$SUM"
timeout 60 "$BIN" --outdir="$BASE/a06_retired_smoke" "$CFG" \
  --cmd "$WT/workloads/directed/agu_addrmodes" --cpu O3 --variant B0 \
  --chaos_addrpath --addrpath_mode byte7_zero --agu_pre_mode a06_size \
  --addrpath_lsu_tier F0 > "$BASE/a06_retired_smoke.out" 2>&1
rc=$?
if grep -q "invalid choice" "$BASE/a06_retired_smoke.out" && [ "$rc" -ne 0 ]; then
  echo "a06_size RETIRED-OK (argparse rejected, rc=$rc)" | tee -a "$SUM"
else
  echo "a06_size *** NOT REJECTED *** rc=$rc" | tee -a "$SUM"; grep -m2 "a06\|choice" "$BASE/a06_retired_smoke.out" | tee -a "$SUM"
fi
echo "summary -> $SUM"
