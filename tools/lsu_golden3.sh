#!/usr/bin/env bash
# lsu_golden3.sh — SE 负载 golden 3× 稳定性验证（G0-05/G0-07/G0-09，ENGINEERING_ONLY）
#
# 9 个 SE 负载各跑 3 次无注入 B0 golden（守卫 experiment 锁严格串行），
# 提取每次的 oracle 输出 hash + sim_ticks + wall 时间，汇总：
#   ① 三次 hash 一致性（G0-07 golden 重复稳定）
#   ② 与 V1.0 GOLDENS 对照（tools/lsu_campaign.py GOLDENS 表）
#   ③ wall 时间（G0-09 timeout 10× 规则的 golden 基准数据）
set -uo pipefail
WLS="mini_check agu_addrmodes sq_forward cache_dirtyevict prefetch_stride stream_chase beebs_kernels gap_bfs sqlite_like"
GOLDEN_DIR=runs/lsu/golden
EVDIR=docs/gem5-fi/lsu/evidence/P1/golden
mkdir -p "$GOLDEN_DIR" "$EVDIR"
SUMMARY="$EVDIR/golden3_summary.tsv"
echo -e "workload\trun\thash\tsimTicks\twall_s" > "$SUMMARY"

for WL in $WLS; do
  for I in 1 2 3; do
    OUT="$GOLDEN_DIR/$WL/g$I"
    rm -rf "$OUT"
    T0=$(date +%s)
    python3 tools/lsu_guard.py run --type experiment \
        --desc "GOLDEN3 $WL run$I/3 (ENGINEERING_ONLY, no injection)" \
        --log "runs/lsu/guard/golden_${WL}_g${I}_rsrc.log" --interval 60 --max-seconds 600 -- \
        build/ARM/gem5.opt --outdir="$OUT" configs/se/lsu_proxy.py \
        --cmd "workloads/directed/$WL" --cpu O3 --variant B0 \
        > "/tmp/golden_${WL}_g${I}.out" 2>&1
    RC=$?
    T1=$(date +%s)
    HASH=$(grep -oE "^[0-9a-f]{16}$" "/tmp/golden_${WL}_g${I}.out" | head -1)
    TICKS=$(grep -oE "^simTicks\s+[0-9]+" "$OUT/stats.txt" 2>/dev/null | grep -oE "[0-9]+$")
    echo -e "$WL\tg$I\t${HASH:-NONE}\t${TICKS:-NA}\t$((T1-T0))" >> "$SUMMARY"
    echo "[$(date +%H:%M:%S)] $WL g$I: rc=$RC hash=${HASH:-NONE} ticks=${TICKS:-NA} wall=$((T1-T0))s"
  done
done

echo "=== golden 3× 一致性汇总 ==="
python3 - "$SUMMARY" <<'EOF'
import sys
from collections import defaultdict
rows = [l.rstrip("\n").split("\t") for l in open(sys.argv[1])][1:]
by_wl = defaultdict(list)
for wl, run, h, ticks, wall in rows:
    by_wl[wl].append((run, h, ticks, wall))
V1_GOLDENS = {  # tools/lsu_campaign.py GOLDENS（V1.0，对照用）
    "mini_check": "07568da9f3ad5665", "agu_addrmodes": "728e604ffcec539d",
    "sq_forward": "1f4cbf14327717df", "cache_dirtyevict": "062e5124df3667f9",
    "prefetch_stride": "629727c0ad9ca8ef", "stream_chase": "50ab96a7fe8f6ec2",
    "beebs_kernels": "a10b9827edd8a9fb", "gap_bfs": "030921682b3731f2",
    "sqlite_like": "33f836327a416d35"}
ok = True
print(f"{'workload':<18}{'3x一致':<8}{'=V1.0':<8}{'hash':<18}{'maxwall(s)':<10}")
for wl, runs in by_wl.items():
    hashes = {h for _, h, _, _ in runs}
    consistent = len(hashes) == 1 and "NONE" not in hashes
    match_v1 = hashes == {V1_GOLDENS.get(wl)}
    maxwall = max(int(w) for _, _, _, w in runs)
    flag = "OK" if (consistent and match_v1) else "DIFF!"
    if flag != "OK":
        ok = False
    h = next(iter(hashes)) if consistent else str(hashes)
    print(f"{wl:<18}{('PASS' if consistent else 'FAIL'):<8}{('PASS' if match_v1 else 'FAIL'):<8}{h:<18}{maxwall:<10}")
print("\nGOLDEN3 OVERALL: " + ("PASS — 9 负载 × 3 全一致且等于 V1.0 golden" if ok else "FAIL/差异见上"))
EOF
