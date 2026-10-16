# o3-atlas：ARMv8-ISA × O3 微架构链路图谱

对 `docs/cpu/armv8-isa/` 全部 372 个指令页建立「gem5 O3CPU 微架构链路」图谱。
spec：`docs/superpowers/specs/2026-10-16-armv8-isa-o3-microarch-atlas-design.md`；
计划：`docs/superpowers/plans/2026-10-16-o3-atlas.md`。

## 结构

- `data/families.yaml` — 31 个格式家族（链路骨架/注入器默认集/已验证锚点）
- `data/instructions/<category>.yaml` — 372 条指令记录（单一事实源）
- `pages/` — 生成的每指令一页（与 armv8-isa 文件名 1:1 互链）
- `index/` — 生成的分类索引
- `diagrams/` — 生成的总链路图与注入器命中矩阵（Phase 3）

## 工具

```bash
python3 -m tools.o3_atlas.gen_stubs     # 重新生成 372 条 stub 记录（可复现第一过）
python3 -m tools.o3_atlas.generate      # 数据 → pages/ + index/
python3 -m tools.o3_atlas.validate      # 全量门：schema+锚点验真+372 覆盖+确定性
python3 -m tools.o3_atlas.scan_tiers "ADD (immediate)"   # gem5 指令候选查询
python3 -m tools.o3_atlas.lsp_query def CHAOS/gem5/src/cpu/o3/fetch.cc:1059:8  # clangd LSP
python3 -m pytest tools/o3_atlas/tests -q                # 工具链测试
```

## 分账表（2026-10-16 终版，gen_stubs 生成，validate 全绿）

| category | implemented | macro-op | fs-only | unimpl(absent) | unimpl(warn-nop) | unimpl(illegal-fault) | total |
|---|---|---|---|---|---|---|---|
| Arithmetic | 29 | 0 | 0 | 4 | 0 | 0 | 33 |
| Atomic | 7 | 0 | 0 | 0 | 0 | 0 | 7 |
| Barrier-Hint | 13 | 0 | 0 | 2 | 1 | 0 | 16 |
| Bit-Manipulation | 24 | 0 | 0 | 1 | 0 | 0 | 25 |
| Branch | 11 | 0 | 0 | 2 | 0 | 0 | 13 |
| Compare | 10 | 0 | 0 | 1 | 0 | 0 | 11 |
| Conditional-Select | 7 | 0 | 0 | 0 | 0 | 0 | 7 |
| Count | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| Cryptographic | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| Load-Store | 97 | 5 | 0 | 21 | 0 | 0 | 123 |
| Logical | 23 | 0 | 0 | 0 | 0 | 0 | 23 |
| Other | 27 | 0 | 0 | 49 | 4 | 1 | 81 |
| PC-Relative | 2 | 0 | 0 | 0 | 0 | 0 | 2 |
| Pointer-Authentication | 10 | 0 | 0 | 0 | 1 | 0 | 11 |
| System | 7 | 0 | 3 | 6 | 0 | 0 | 16 |
| **合计** | **271** | **5** | **3** | **86** | **6** | **1** | **372** |

未实现主体 = MTE（CPY*/SETG*/STG* 等，gem5 v25 源码零匹配）、SYS/SYSL（落
Unknown64）、BTI/ESB/PSB CSYNC/TSB CSYNC/CSDB（WarnUnimplemented 警告+nop）。
absent 判定为第一过自动分账（候选为空），分类任务（计划 Task 10-24）逐条
复核并深填；任何修订以 data/instructions/*.yaml 为准。
