# OoO W6 Int Decode 注入器 Implementation Plan

> Spec：04-design-matrix.md D01-D10 + 06 §4 W6。机制事实 findings.md（spike D：可行性高——hook fetch.cc:1246 decode 之后、1248 isMacroop 之前改局部 staticInst；asBytes() 取 8B ExtMachInst（arm/insts/static_inst.hh:596）改低 32 位→decodeInst(emi) re-decode（**现为 protected 需加 public wrapper 绕缓存**）；D08 无需值级 patch（decoder 自己 sext）；风险：macroop 样本排除/Thumb 排除（size 恒 4）/非法编码→Unknown→SIGILL 需分类单列/predictedBranch 看原指令）。
> 先例：W4 的 CHAOSRenameMap（日志格式/flat 索引/ROB 活跃池）。

### Task 1: W6.0-W6.4 — D01-D07 opcode/寄存器号/立即数 单/双比特 + opcode 换值
- [ ] **先做机制原型**：ArmISA::Decoder 加 public decodeChaos(ExtMachInst) wrapper（绕 instMap 缓存）+ CHAOSDecode 扩展（新 SimObject 挂 cpu->chaosDecode 已存在？查 CHAOSDecode 现有挂载——现有只有 dest_reg_sub 挂 rename.cc:1161；需加 fetch.cc:1246 钩子）。四类字段操作全走"机器位翻转→re-decode→替换局部 staticInst"：opcode 位（编码的低段）、寄存器号位（编码的 rt/rd 字段位区间——按 ARM64 编码手册位段）、立即数位（imm 字段位段）、opcode 换值（同类合法 opcode 互换表：ADD↔SUB/ORR↔AND 等操作数格式兼容对）。日志行：原编码 hex→新编码 hex+翻转位段+新旧 mnemonic。验证：注入日志（编码 diff 可复算）+同 seed 复现+golden 回归+ctrace L2 证据（预期多数 Crash=非法指令——SIGILL 分类说明）。
### Task 2: W6.5-W6.7 — D08 符号扩展位定向 / D09 子字段错位拼接 / D10 裂解控制位
- [ ] D08=翻立即数编码的符号位段（re-decode 后 decoder 自带 sext）；D09=imm 子字段移位错位重拼（如 imm[19:16]→imm[15:12]）后 re-decode；D10=探索性（gem5 宏裂解机制 spike：LDR/STR writeback macroop——若不可行诚实 blocker）。

**通用**：同 W5。注意 decode 阶段每指令都过钩子——性能门（有注入器挂载时 golden 跑通即可，空闲路径零开销）。
