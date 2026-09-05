# Task Plan: 5 个新 vmcore 案例独立诊断报告（2026-09-04 晚间批次）

## Goal

对 `/home/sdc/wangxu/vmcore0102/` 下 5 个尚无报告的新转储（2026-09-04 21:53 – 23:37），
逐案独立完成微架构级 SDC 故障根因分析，每案一个独立 subagent，生成与
`docs/cases/vmcore-diagnosis-report-*` 同格式的诊断报告。

## Constraints

- **禁止阅读既有分析文档**（docs/cases/**、docs/sdc-microarch/**、各转储目录内 DIAGNOSIS_REPORT.md 等），
  证据只来自：vmcore 原始文件、vmcore-dmesg.txt、crash 工具输出、内核源码、反汇编。
  （格式模板允许看标题结构，不允许抄内容结论。）
- 每个结论必须有实证（dmesg 行号原文、crash 输出、寄存器值），可复核。
- 报告目录格式：`docs/cases/vmcore-diagnosis-report-127.0.0.1-<ts-without-colons>/`
  内含主报告 md + 取证附件（dmesg_forensics.txt 等）。

## Evidence Base (5 new dumps)

| # | 转储目录 | 大小 | 初筛症状（已实证） |
|---|---------|------|--------------------|
| 13 | 127.0.0.1-2026-09-04-21:53:28 | 11G vmcore 完整 | CPU179 反复 __do_kernel_fault WARNING ×4+ |
| 14 | 127.0.0.1-2026-09-04-22:09:49 | 9.5G vmcore 完整 | CPU168 list_debug WARNING ×N，dmesg 从 397s 中段开始（无 boot 段） |
| 15 | 127.0.0.1-2026-09-04-22:27:27 | 7.9G vmcore-incomplete | CPU179 __do_kernel_fault WARNING ×4+ |
| 16 | 127.0.0.1-2026-09-04-22:39:38 | 9.4G vmcore 完整 | CPU179 __do_kernel_fault WARNING ×4+ |
| 17 | 127.0.0.1-2026-09-04-23:37:57 | 9.6G vmcore 完整 | CPU179 NULL(0x8) Oops, ESR=0x96000004 |

> 内核版本统一：6.6.0-145.3.23.154.oe2403sp3.aarch64，vmlinux=/tmp/vmlinux-0102（BuildID 276194e5）。

## Phases

### Phase 1: 环境与初筛（主会话完成）`complete`
- [x] 确认 5 个新转储无既有报告
- [x] crash 8.0.4 可用，vmlinux 匹配
- [x] 每案 dmesg 初筛（崩溃签名、CPU、时间线端点）

### Phase 2: 逐案深挖（每案一个独立 subagent）`complete`
- [x] 案例 13（21:53:28）→ vmcore-diagnosis-report-127.0.0.1-2026-09-04-215328/（339 行主报告 + 33 个 crash session；x20 读出 SDC 实锤：内存真值 ffffc573b8bda000 vs 寄存器 73b88cc000ffffc5）
- [x] 案例 14（22:09:49，CPU168 list_debug 新签名簇）subagent 深挖 + 报告（2026-09-05 完成）
- [x] 案例 15（22:27:27，incomplete）subagent 深挖 + 报告（2026-09-05 完成）
- [x] 案例 16（22:39:38）subagent 深挖 + 报告（2026-09-05 完成，402 行 + 25 个 crash session）
- [x] 案例 17（23:37:57，NULL Oops 案）subagent 深挖 + 报告（2026-09-05 完成）

> 内存约束：主机仅 ~4G 可用，crash 大转储会话必须串行（一次一个 subagent 跑 crash）。

> 主会话初筛关键发现（写入各 subagent 任务书）：
> - 案13/15/16 同签名（find_busiest_group+0x140, LDR x23,[x27,#0x120], FAR=x27+0x120 闭合），x27 高16位破坏形态各异（0x73b8/0x00ff/完好低位乱码）
> - 案14 为**多核级联受害**（168/169/180/50/55，458 次相同 list_add corruption = 共享内存持久写坏），CPU179 x27 与 CPU180 FAR 同前缀差 0x120
> - 案17 为**读出路径 SDC 直接实锤**：mem_section[0xc08] 内存真值非零（ffff6057fffaeb00）而 CPU 装载 x3=0 → load 读出≠内存

### Phase 3: 主会话验收 `complete`
- [x] 5 份报告存在性、结构完整性检查（全部含十大章节+附录，257-402 行）
- [x] 抽查关键实证真实性：
  - 案13: dmesg L3202 `x20: 73b88cc000ffffc5` ✓（与报告引用一致）
  - 案14: 458 次相同 list_add corruption ✓（grep 实测 458）
  - 案15: fatal x27=00ffab53df0abe80 ✓
  - 案16: fatal x27=ffffbda5543596c0 ✓
  - 案17: dmesg L2610 `x3 : 0000000000000000` ✓（与 mem_section 真值非零矛盾即实锤）
- [x] 跨案共性：5 案全部落在 CPU179/Node7（案14 致命在 CPU180 但 CPU179 同指针同偏移受扰），与既有 12 案共同构成 17 案同核谱系；新批次新增两类实锤——读出≠内存直接证据（案13/17）与写路径持久损坏（案14）

### Phase 4: 提交 `in_progress`
- [ ] feature 分支 + commit + push（不推 main）

## Decisions Made

| # | Decision | Why |
|---|----------|------|
| 1 | 每案独立 subagent，一次派 2-3 个并行 | 案例间无写冲突（各自独立报告目录）；crash 大内存转储加载串行化由 subagent 内部控制 |
| 2 | 案例 14（CPU168 list_debug）单独处理 | 新签名簇，与 CPU179 簇不同，需独立验证是否同一根因的不同表现 |
| 3 | 报告格式对齐 12:33:31 模板的章节结构 | 用户指定该格式 |
