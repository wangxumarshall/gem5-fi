# FR07 真实 PRF-WB 数据边界 hook（v2）

> 2026-11-04，分支 `fsu`。目标：把 FR07 从 execute-post-write 代理升级为
> 工作簿要求的 “PRF 写入前修改 WB data” 真实边界；旧 proxy 证据保留。

## Task 1 — 位置审计与 proxy 排除（已完成，commit f7656299）

- [x] 源码/时序审计：`dyn_inst.cc:360-369`、`CHAOSFPU.cc:621-628/880-977`、
      `iew.cc:1290/1516-1530`。
- [x] FR07-F0-W1 三个旧 seed 标 `PROXY_EVIDENCE`，索引/矩阵/文档排除严格计数。

## Task 2 — 真实 hook 实现（本 commit）

- [x] `maybeArm`（execute 前选择）、`shadowForWrite`/`interceptScalarWrite`/
      `interceptVectorWrite`（写前 mask / shadow WB）、`finalizeWb`（mask 后
      写 PRF）、`noteProducerWakeup`、`noteSquash`、`noteCommit` 退休。
- [x] `CPU::getWritableReg/setReg`、`DynInst::execute/setSquashed`、
      `IEW::writebackInsts` 接线。
- [x] 事件字段 `injection_site/hook_version/producer_seq/dest_operand/
      arm_tick/writeback_tick/wakeup_*` 注册到两个字段表。
- [x] manifest schema、runner、ooo_proxy CLI 接线。
- [x] 真实 gem5 gate：FP32/FP64/NEON lane/双 bit 全 admitted；precision
      mismatch 与非 FP 负例 eligible=0；squash 真实事件链。
- [x] gate 报告 `docs/gem5-fi/fsu/FR07-PRF-WB-HOOK.md`。

## Task 3 — 正式 seed（待做）

- [ ] 预注册真实 hook 的 FR07-F0-W1 seed1/2/3（新 attempt，保留 proxy）。
- [ ] seed1 L0–L5 + audit.ok 后再 seed2/seed3。
- [ ] 通过后 FR07-F0-W3 / W5 走同一 hook；W5 每 suite seed 只计 1。

## 验证命令

```bash
python3 -m pytest tests/test_fsu_fr07_wb_hook.py tests/test_fsu_scope.py -q
python3 tools/fsu_seed_runner.py --manifest configs/fsu/FSU-FR07-F0-W1-HOOK-FP32-GATE.json \
  --seed 1 --out-root runs/fsu-gates/FR07-HOOK-GATE-FINAL
```
