# R6-A2 状态（2026-10-28）— **NOT COMPLETE**

> 本文件是**阶段性真实状态**，不是完成报告。A 单元尚未达到“30 非 F6
> RunID × 3 合格 seed”。以下每条都有真实命令/证据支撑；未完成项显式列出。

## 0. 现场

- 分支 `fix/r6-a-unit-20261028`，起点 `defb3e0d`。
- 最新二进制 `CHAOS/gem5/build/ARM/gem5.opt`
  sha256 `a1f85a0817bcd940075aa0dad995ed79da616c703e2c9ee67211743e88f49103`。
- 最近一次完整回归（全部 C++ 改动合并后）：
  `python3 -m pytest tests -q` → **107 passed in 244.75s, EXIT=0**。
  与 defb3e0d 基线同数同套件，NEW FAIL=0。
- 脚本级既存失败（defb3e0d 旧 checker 逐字复现，非本轮引入）：
  `tests/test_lsu_hook_a07.py` 的两条“合成链 → full”断言在旧/新 checker 上
  都返回 `provable_to_L0_then_unknown`；本轮不改断言、不掩盖。

## 1. 已完成并有真机证据

| 项 | 提交 | 真机证据 |
|---|---|---|
| 同源 repeat 载体 + repeat_factor（F1/F2/F4） | `748bd8f7`、`ed156dd7` | A01-F1-W3 s1：`repeat=4023`，`attempted=eligible=1,256,415 injected=1`，35.5s；A01-F2-W3 s1：`106,412 injected=1`；A02-F2-W3 s1：`156,096 injected=1` |
| 真实终局事件 E1/E3/E4 + split 空指针修复 | `a9da7e66` | E1 `arch_translation_fault`（L2，detected_contained）；E3 `squash_discarded`（L4）；E4 `store_not_retired`（L4，13 事件链） |
| A04-a ELF 对象注册表 + A04-b 按宽度同页 | `24883a60` | W3 `0x493060→0x493190`（offsets 96→400）；W0 `0x491b90→0x491b28`（130 事件 full）；A04-b `0x7ffffefc68→0x7ffffefbe8` |
| A06-a store original/2 + A06-b 同宽非零掩码 | `5dec2f77` | A06-a `old_size=8 new_size=4 submodel=a06a`；A06-b `old_be=0xffff… new_be=0x7fff… submodel=a06b`；两链均 detected_contained |
| A07-a 真实旧 EA + A07-c 有界 watchdog | `9cdccc11` | A07-a `old_ea=0x493230 new_ea=0x7ffffefc68`，full L5；A07-c `watchdog forced_resume` 有界；squash 出口发 `ready_loss_squashed` |
| A05-d pre/post EA 反转 | `cb8c7e8e` | W3 `0x4932f8→0x493300`，118 事件 full L5 |
| 负向门禁 + 回归 | `a9da7e66`、`5e0e9c59` | `test_lsu_r6a2_gate_negatives.py` ALL PASS；完整 pytest 107 passed |

代表 canary 实跑：A01-F1-W3、A02-F2-W3、A03-F5-W3（F5 injected=1）、
A04-F0-W3（a/b）、A05-F0-W3（d）、A06-F0-W3（a/b）、A07-F0-W3（a/b/c）。
A08 未实现，未运行。

## 2. 明确未完成 / 阻塞

1. **A05-a/b/c（精确架构限制，已实测）**：在 `LSQ::pushRequest` 用
   `DynInst::getRegOperand(slot0/1)` 重建 base/index 的 Design B 路径，
   在 microop 上实测 **SIGSEGV**（W0 a05_base_index / a05_shift 触发即崩）。
   microop 源操作数槽位不是稳定 API。当前 a/b/c 在资格判定处一律
   ineligible（不注入、不消费预算），**未用任何代理冒充**。
   最小未来方案：ISA `buildEACode()` 操作数钩子（详见 `R6-A2-A05.md`）。
2. **A08-a/b 未实现**：错误通道需要改 `LSQRequest::buildPackets` 的命令
   （load 侧只有 `lsq.cc:929-932` 数行窗口，store 侧在 `lsq_unit.cc:1036`
   前有长窗口）；同周期 EA 互换需要 IEW 配对登记 + store 侧同 4KiB 页
   `setPaddr`。尚无真实代码与 canary，不能声称覆盖。
3. **正式 90 seed 未运行**：本轮只做了代表 canary；未启动
   `runs/lsu/r6_a2_*` 正式批次。上一轮 9 个合格 seed 原样保留。
4. 因此 A06 四格、A05 两格、A08 四格与其余 RunID 尚未取得本轮 3/3。
   **不得**把本轮 canary 计入正式合格 seed。

## 3. 下一步（按依赖顺序）

1. A05-a/b/c：ISA `buildEACode` 钩子（ldr64/str64.isa + 新
   `chaos_agu_operands.{hh,cc}` + SConscript），全 ARM 重新生成；
   微载体 `agu_operand_modes` 覆盖 a/b/c。
2. A08-a/b：`buildPackets` 通道翻转（store 侧）+ IEW 同 tick 配对登记 +
   load 侧 PRE 换 EA / store 侧同页 `setPaddr`；跨页/跨周期明确 decline。
3. 两模型 canary 通过后，再按 `R6-A2` 工作令启动正式 90 seed 批次、
   逐 seed 验收与传播文档。
4. 上述完成前，A 单元**不得**合入 origin/fi-ding。
