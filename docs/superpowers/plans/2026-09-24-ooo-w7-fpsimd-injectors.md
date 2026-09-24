# OoO W7 FP/SIMD 注入器 Implementation Plan

> **Spec**：04-design-matrix.md D56-D91 + 06 §4 W7（D62-66/D72/73/76 已按北极星合并条款并入向量行，a8697ca9）。机制事实全在 findings.md「W7 FP/SIMD 设计 spike 结论」（行号已核）。先例：W4（RAT/Freelist 11+7 模式）、W5（ROB 9 模式）、W6（Decode 8 模式）。
> **依赖硬约束**：W7.1 排 W6 T2 后；W7.2/3 排 W5 T3-4 后；W7.4 排 W5 T5-7 后。

### Task 1: W7.1 — FP Decode（D56-D61）
- [ ] W6 引擎 + `fpOnly` 过滤（先明确口径：CHAOSFPU.cc:88-98 isFpOpClass 含标量+SimdFloat 但不含整数 SIMD——按 04"FP/SIMD"口径取 SimdFloat*∪Float*，文档化）；FP opcode 位集 bits23:10（D56/D57）；**FP swap 规则表新增**（FADD↔FSUB/FMUL↔FDIV 等操作数兼容对，主机 gcc 真编码核验——W6 先例；D58）；寄存器号 D59/D60 零改动（kRegBits 已覆盖 Vd/Vn/Vm，effective() 谓词保留筛 fp.isa 交错路径）；D61=引擎+新谓词 `new_opClass != orig_opClass`（诚实近似：无独立路由位，opClass→FUPool capability；观测=FU/latency 效应）。

### Task 2: W7.2 — VecRegClass RAT 族（D62-D71 合并行 + D66/D71 stale_read）
- [ ] CHAOSRenameMap 加 `targetClass` 参数（Int/Vec 两值即可，Float 惰性）：放宽 5 处 int 闸门（:194/:429/:471/:605/:706）、XZR 守卫按类条件化、pickAllocatedPhysReg + collectRobActiveDests 加类参数与 vecPhysRegId（regfile.hh:177）；**归因设计决策**：RAT 钩子无 opClass——D62-66 与 D67-71 同路径执行，归因从 commit trace 后置（文档化）。全部 11 模式 × Vec 类参数化（map_bitflip/2/swap_to_active/f5_rat_stuck/stale_read/hb_bitflip/2 优先）。

### Task 3: W7.3 — VecRegClass 空闲表（D72-D77 合并行）
- [ ] CHAOSFreeList mark_free/mark_free_event 类参数化：三处 int 硬编码（:142 类闸门/:255 numFreeRegs/:159 vecPhysRegId）+ **按类阈值**（vec 池初始空闲 4——int 的 ≤8 对 vec=全池；北极星 D75 的 ≤6 需按「初始空闲 4」重导为 ≤2 或 free==0，findings D75 校准结论）；finalSummary 扩 vec 行。

### Task 4: W7.4 — FP Dispatch/ROB（D83-D91）
- [ ] **D83-D85 零新代码**（W5 现有模式 × FP 负载 campaign——属 W8 执行）；D86 零新代码（CHAOSIQ 直接可用，可加 opClass 过滤增强）；D87-D91 = W5 tag 族（D50-54 机制）+ 类参数化（collectIntDestSlots/collectRobActiveDests/4 处闸门）。**排 W5 T5-7 落地后**。

**通用**：每 Task 三件套验证 + 注入日志（值可复算/活跃池含 vec id）+ 同 seed 复现 + golden 回归 + ctrace L2 一张 + runner 路由；代理不 commit；FP 负载用 polybench/embench-nbody/minver/libjpeg。
