#!/usr/bin/env bash
# P0 G0-10 资源守卫最小单实例验证测试（总方针 §8.5 允许的"为验证安全机制所必需的最小单实例测试"）
# 测试项：
#   T1 gate 正常放行（资源健康时）
#   T2 acquire 获取锁成功
#   T3 acquire 重复获取被拒绝（陈旧锁保护）
#   T4 clear-stale 错误 PID 被拒绝
#   T5 clear-stale 正确 PID 处置成功
#   T6 acquire → release 正常周期
#   T7 run 守卫执行 + 并发重复启动被拒绝 + 采样日志与完成事件
set -u
cd /home/sdc/gem5-fi-ding
G="python3 tools/lsu_guard.py"
LOG=docs/gem5-fi/lsu/evidence/P0/guard_verify_t7.log
rm -f "$LOG"

echo "===== T1: gate（期望 exit 0, ok=true） ====="
$G gate | tail -5; echo "T1_EXIT=${PIPESTATUS[0]}"

echo "===== T2: acquire build 锁（期望 exit 0） ====="
$G acquire --type build --desc "guard-verify-T2"; echo "T2_EXIT=$?"

echo "===== T3: 重复 acquire（期望 REFUSED, exit 3=陈旧锁） ====="
$G acquire --type build --desc "guard-verify-T3" 2>&1; echo "T3_EXIT=$?"

DEAD_PID=$(python3 -c "import json;print(json.load(open('runs/lsu/guard/build.lock'))['pid'])")
echo "锁内 PID=$DEAD_PID"

echo "===== T4: clear-stale 错误 PID（期望 REFUSED, exit 2） ====="
$G clear-stale --type build --confirm-dead-pid 999999 2>&1; echo "T4_EXIT=$?"

echo "===== T5: clear-stale 正确 PID（期望 CLEARED, exit 0） ====="
$G clear-stale --type build --confirm-dead-pid "$DEAD_PID" 2>&1; echo "T5_EXIT=$?"

echo "===== T6: acquire → release 周期（期望 exit 0, 0） ====="
$G acquire --type build --desc "guard-verify-T6" >/dev/null; echo "T6a_EXIT=$?"
$G release --type build; echo "T6b_EXIT=$?"

echo "===== T7: run 守卫执行 + 并发重复启动拒绝 ====="
# 后台启动受守卫任务（sleep 8，2 秒采样）
$G run --type build --desc "guard-verify-T7" --log "$LOG" --interval 2 -- sleep 8 > /tmp/guard_t7_run.out 2>&1 &
RUN_WRAPPER=$!
sleep 3
echo "--- T7a: 守卫运行中的锁内容 ---"
cat runs/lsu/guard/build.lock
echo "--- T7b: 并发第二个 run（期望 GATE BLOCKED/ACQUIRE REFUSED, 非零退出） ---"
$G run --type build --desc "guard-verify-T7-dup" --log /tmp/guard_t7_dup.log --interval 2 -- sleep 1 2>&1 | tail -8
echo "T7b_EXIT=${PIPESTATUS[0]}"
wait $RUN_WRAPPER; echo "T7_run_EXIT=$?"
echo "--- T7c: 守卫事件日志尾部 ---"
tail -5 runs/lsu/guard/guard_events.log
echo "--- T7d: 采样日志（前2条+末1条） ---"
head -2 "$LOG"; tail -1 "$LOG"
echo "--- T7e: 锁应已释放 ---"
ls runs/lsu/guard/build.lock 2>&1 || echo "build.lock 已释放（符合预期）"
echo "===== 验证脚本结束 ====="
