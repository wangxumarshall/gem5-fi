# FSU FP04 子模型覆盖扩展计划（D3 后续）

> 依据：`docs/gem5-fi/fsu/FP04-W4-FREQUENCY-CLOSEOUT.md`、Subagent C 只读审计
> （2026-11-03）、`CHAOS/gem5/src/cpu/o3/CHAOSFPU/CHAOSFPU.{hh,cc,py}`。
> 原则：一任务一提交；先真实 workload/golden/eligible/链证据，后正式 RunID；
> 不宣布 COMPLETE。每个任务完成前必须引用真实命令输出。

## 0. 事实基线

- 正式频率批次已完成：F0/F1/F2/F3-W4 各 3/3，共 12/519；全部 fault `full`、
  audit PASS；但仅覆盖 `FP04-c / mant_lo`。
- FP64 六个 bitseg 已在 C++ 实现：
  `CHAOSFPU.cc:360-365`（sign/exp_hi/exp_lo/mant_hi/mant_mid/mant_lo），
  位区间见 `CHAOSFPU.cc:278-279`；未知 bitseg 会 panic（`:366-367`）。
- 当前 FSU 事件只发射 `lane_width=64`、`lane_offset=0`（`CHAOSFPU.cc:524-525`），
  `lane_mask` 为空；Vec 写路径只 XOR 低 8 字节（`CHAOSFPU.cc:402-413`）。
- `CHAOSFPU.py` 只有 `bitseg`，没有 precision/lane 参数（`:37-38`）。
- FP32 字段表、FP04-d lane result、NEON 全 128-bit lane 均未实现。
- B0 配置（ROB=40、IQ=32、3/3/3、8/8/8）未参数化；当前为 C3。
- 正式 RunID 集合来自工作簿 173 项（`tools/fsu_implementation_matrix.py`、
  `tests/test_fsu_implementation_matrix.py`）；新增正式 RunID 需先裁决
  gate/supplement 注册路径。

## 1. 任务 A：字段/lane 特征测试与缺口 strict xfail ✅

- 新文件 `tests/test_fsu_fp04_fields.py`：
  - 对 12 个正式 seed 的 687 个 root 校验 field 合法、bit 在区间内、
    `fault_mask == 1<<bit`、`lane_width=64`、`lane_offset=0`、`submodel=FP04-c`；
  - 锁定当前正式字段集合为 `{"mant_lo"}`；
  - 对 FP32 precision、lane 参数、`lane_mask` 发射设置 `strict=True` xfail。
- 验证：`python3 -m pytest tests/test_fsu_fp04_fields.py -q`
  （预期 15 passed + 3 xfailed，或按参数化计数）。

## 2. 任务 B：FP32 精度参数与字段表（1 commit）✅

> 已实现：`CHAOSFPU` precision/fp32 位表、事件 precision/field 范围；
> host C++ 单测与 FP32 scalar 门禁（F0-W1-GATE）3/3 PASS。

- `CHAOSFPU.py` 增加 `precision`（`fp64` 默认 / `fp32`）。
- `CHAOSFPU.cc` 按精度选择字段表：
  - FP64：现有 `sign=63, exp=62..52, mant=51..0`；
  - FP32：`sign=31, exp=30..23`（exp_hi=30..27, exp_lo=26..23），
    `mant=22..0`（mant_hi=22..15, mant_mid=14..8, mant_lo=7..0）。
- `configs/se/ooo_proxy.py`、`tools/fsu_seed_runner.py`、`tools/runner.py`、
  `tools/campaign.py` 透传 `--fpu_precision`；未知值 loud reject。
- 测试：FP64 现有证据字段语义不变；FP32 位表边界；非法 precision 拒绝。
- 构建：`flock /tmp/gem5-build.lock scons -j4 build/ARM/gem5.opt`（禁止 -j16）。
- 完成前不得启动新的正式 RunID；先用 gate/pilot 验证。

## 3. 任务 C：lane 选择、128-bit 写入与 lane_mask（1 commit）✅

> 已实现：laneWidth/laneOffset、16 字节 VecReg lane RMW、lane_mask/
> full_before/full_after/bit_in_lane/reg_class；NEON lane2 门禁与正式
> F0-W3 3/3 证明只改目标 lane。

- 增加 `laneWidth ∈ {8,16,32,64}`、`laneOffset`，按目标 lane 基址 XOR。
- VecRegClass 写路径覆盖 16 字节（当前仅 8 字节，`CHAOSFPU.cc:402-413`）。
- 事件真实发射 `lane_width`/`lane_offset`/`lane_mask`（替换 `:524-525` 常量）。
- 测试：目标 lane 外 bit 不变；lane_mask 落盘；128-bit 第二 lane 可注入。
- 构建同上；gate/pilot 先行。

## 4. 任务 D：真实 workload + golden + census（1 commit）✅

> 已新增 `fp32_fma_kernel` 与 `neon_fp32_lane_kernel`；golden 各 3 次一致；
> countOnly eligible 实测 524,292（scalar FP32）与 16,384（NEON lane2）。

- FP32：新增 `workloads/directed/elemwise_fma_kernel_fp32.c`，全数组
  ARRAYHASH + ULP；无注入 golden 连续 3 次一致；记录 source/binary SHA。
- FP NEON：新增 `float32x4_t` FMA lane kernel，逐 lane oracle（不能只用单一
  16-hex FINAL，`tools/classify.py:45-58` 只消费 16-hex）；每 lane 输出。
- countOnly 实测 eligible（不得线性推算）；为 F1 预留 N ≥ 1,500,000，否则
  按预注册预算扩 ROI 后重建。
- 注意：W3 现有 `neon_lane.c` 是整数 NEON，不在当前 `isFpOpClass` 域
  （`CHAOSFPU.cc:180-188`），不能直接复用。

## 5. 任务 E：gate/pilot 与正式注册裁决 ✅

> 已执行：3 个 GATE RunID × 3 seed 全 PASS（不计 519）；未新增第 174 个
> RunID。正式试点用未运行的 `FSU-FP04-F0-W3`，3 seed 全 PASS，
> 正式完成数 12/519 → 15/519。

- 先用 `*-GATE` RunID 证明机制（不计入 519）；逐 fault 链/audit 门禁与
  F3 门禁相同。
- 新增正式 RunID 前必须由负责人裁决：扩展工作簿注册表，或建立 supplement
  注册表；同步修改 `EXPECTED_RUNIDS`、`runids.json`、矩阵与测试。
- 在完成裁决前，不得批量启动新正式 RunID，也不得把 gate 计入完成数。

## 6. 任务 F：B0 配置参数化（独立阻塞项）

- `configs/se/ooo_proxy.py` 暴露 ROB/IQ/width/dispatch 参数；默认保持 C3。
- B0 下重新 census/预注册 ordinals（不能沿用 C3 的 57,347 / 2,097,155）。
- B0 与字段/lane 覆盖可并行设计，但不得混用 C3/B0 的数字。

## 7. 停止条件

- 无真实 workload identity、golden、eligible 与完整观测链时，不启动正式 RunID。
- 任一 gate 未闭合、audit 失败或证据截断时，保留 attempt 并停止该方向。
- 不因频率批次 12/12 宣称 FP04 COMPLETE；`overall` 保持 NOT_COMPLETE。
