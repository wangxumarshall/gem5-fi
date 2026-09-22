#!/bin/bash
# verify_task2_1.sh — SDC-ED Task 2.1 验证（参数化无行为变化 + profile 覆盖 + 回归）
# 用法: bash smoke_test/tools/verify_task2_1.sh
set -e
REPO=/home/sdc/wangxu/gem5-fi-fuzz
GEM5=$REPO/CHAOS/gem5/build/ARM/gem5.opt
CFG=$REPO/smoke_test/configs/two_level_taishan.py
OUT=$REPO/artifacts/sdc-ed-verify/task2-1
mkdir -p "$OUT"

echo "=== [1] 默认参数（无 --cov-profile）：应与旧硬编码数值完全一致 ==="
$GEM5 --silent-redirect -d "$OUT/default" $CFG \
  --binary $REPO/workloads/harp/sample_seq --mode baseline --cov 2>/dev/null
grep -E "ibrIntAdd|ibrIntMul|ibrFpAdd|ibrFpMul|irfAvfInt |irfAvfCommitInt|sqAvf|roiCycles" \
  "$OUT/default/stats.txt" | head -12

echo
echo "=== [2] --cov-profile taishan-v110（同值 profile：应与 [1] 逐字节一致）==="
$GEM5 --silent-redirect -d "$OUT/profiled" $CFG \
  --binary $REPO/workloads/harp/sample_seq --mode baseline --cov \
  --cov-profile $REPO/configs/cpu-profiles/taishan-v110.yaml 2>/dev/null
for s in ibrIntAdd ibrIntMul ibrFpAdd ibrFpMul sqAvf irfAvfInt irfAvfCommitInt roiCycles; do
  a=$(grep "$s " "$OUT/default/stats.txt" | awk '{print $2}')
  b=$(grep "$s " "$OUT/profiled/stats.txt" | awk '{print $2}')
  [ "$a" = "$b" ] && echo "  OK  $s = $a" || echo "  MISMATCH $s: default=$a profiled=$b"
done

echo
echo "=== [3] --cov-profile kunpeng920（ROB 128 等差异化实例：跑通即证参数面贯通）==="
$GEM5 --silent-redirect -d "$OUT/kunpeng" $CFG \
  --binary $REPO/workloads/harp/sample_seq --mode baseline --cov \
  --cov-profile $REPO/configs/cpu-profiles/kunpeng920.yaml 2>/dev/null
grep -E "ibrIntAdd |ibrFpAdd " "$OUT/kunpeng/stats.txt" | head -2

echo
echo "=== [4] 回归锚：无 --cov 的默认路径 ==="
$GEM5 --silent-redirect -d "$OUT/regress" $CFG \
  --binary $REPO/workloads/directed/reg_chain --mode baseline 2>/dev/null
grep -o "f247ef3fe6f02cfd" "$OUT/regress/simout" && echo "REGRESSION ANCHOR PASS" || \
  { echo "REGRESSION FAIL"; grep -iE "sum|checksum" "$OUT/regress/simout" | tail -3; }
