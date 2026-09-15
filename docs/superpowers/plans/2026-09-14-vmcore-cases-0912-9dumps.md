# 9 案新增 vmcore 独立诊断报告计划(第 20~28 次转储,cases-2 系列)

> **For agentic workers:** 本计划按 superpowers 范式撰写;一案一 commit(one-patch-per-unit)。执行时逐项勾选 `- [ ]`。

**Goal:** 为 `/home/sdc/wangxu/vmcore0102/` 下 9 个新增 dump 目录各产出一份七要素独立诊断报告,输出到 `docs/cases-2/vmcore-diagnosis-report-<目录名去冒号>/`(每案 1 子目录,含取证附件),全部结论基于真实执行的命令输出,置信度分【实锤】/【强推】/【假设】三级。

**Architecture:** 9 案中 8 案仅有 `vmcore-dmesg.txt`(kdump vmcore 文件缺失),走 dmesg 法证 + python3 mod 2⁶⁴ 代数闭合路线;1 案(09-14-01:45:56)有 12GB 完整 vmcore,追加 crash 动态取证(x1 语义、`__per_cpu_offset[]` 真值对照、反事实 vtop)。方法论沿用 12 案 census(docs/cases-2/SYNTHESIS-12case-cross-analysis.md)+ 09-09 两案计划(docs/superpowers/plans/2026-09-09-vmcore-cases-0907-2dumps.md)。诊断流程遵循 systematic-debugging 四阶段:取证(Phase1)→对照前 19 案谱系(Phase2)→假设检验(Phase3)→报告(Phase4)。

**Tech Stack:** crash 8.0.4-17.oe2403sp4 + debuginfo `/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`(BuildID 276194e5…,419MB,已验证存在)、python3(mod 2⁶⁴)、grep/awk。

## 已勘察事实(2026-09-14 实证,执行者须复核)

9 案签名完全一致,与前 19 案同谱系(CPU179 / `find_busiest_group+0x140/0xb60` / Code 末字 `(f9409377)` = `ldr x23,[x27,#288]` / 崩溃链均为 newidle_balance 或 idle softirq 路径):

| # | dump 目录 | uptime | 进程 | x25 | x20(坏值) | ESR/FSC | FAR | 前兆数 |
|---|---|---|---|---|---|---|---|---|
| 20 | 09-07-20:04:26 | 9979s | mi-scavenger | 7 | 0(零塌缩) | 0x96000007/L3 | ffffbc6421fa97e0 | 8(全 CPU179) |
| 21 | 09-08-17:21:33 | 76275s | mi-scavenger | 0x36=54 | d3eb5026e000ffff(高段塌缩+0xffff 标签) | 0x96000004/L0 | d3eafc3c10eb97df | 3 |
| 22 | 09-11-14:31:32 | 15980s | mi-scavenger | 0xb3=179 | 9226e000ffffa4bd | 0x96000004/L0 | 0026bb43eeea3c9d | 0(Not tainted) |
| 23 | 09-11-16:30:10 | 6648s | mi-scavenger | 0xa4=164 | ffa9342267e000ff(字节窗口错位) | 0x96000004/L0 | ffa90aeec68998df | 0 |
| 24 | 09-11-17:06:07 | 1592s | kworker/179:1 | 0x32=50 | 00ffffb810e4a240 | 0x96000004/L0 | 00ffc7a7ac4a3a20 | 0 |
| 25 | 09-11-17:58:36 | 2777s | mi-scavenger | 6 | 0(零塌缩) | 0x96000006/L2 | ffffdee405e697e0 | 0 |
| 26 | 09-12-00:09:19 | 21773s | mi-scavenger | 0xac=172 | ffdfb79a8ee000ff | 0x96000004/L0 | ffdf57e3756298df | 63 |
| 27 | 09-12-10:00:31 | 35000s | neon_rot_ldr_at | 0x14=20 | d74000ffffabcecc | 0x96000004/L0 | 003fd531b2dc66ac | 17 |
| 28 | 09-14-01:45:56 | 142081s | swapper/179 | 7 | 0(零塌缩) | 0x96000007/L3 | ffffcad705af97e0 | 184(新纪录) |

- **09-11 四连崩(案 22-25)为 4 次独立开机**(panic uptime 15980/6648/1592/2777s 各异,不可能同 boot),即 4 次冷启动后 26min~4.4h 内复发——故障跨重启稳定复现。
- taint 自洽:有前兆的案(20/21/26/27/28)均 `Tainted: G W`(W=前兆 WARNING 所致),零前兆案(22-25)均 `Not tainted`。
- RAS 负证据:9 案均仅 2 条开机 EDAC/ghes_edac 初始化行,零真实 RAS 错误上报。
- 8 案无 vmcore 文件(仅 dmesg),1 案(28)有 12GB 完整 vmcore。
- 案 22 x25=0xb3=179:**自指装载**——CPU179 装载自己的 percpu 偏移槽时坏值。案 24 x25=50、案 27 x25=20 为跨槽装载。
- 案 27 受害进程 `neon_rot_ldr_at` 是 opendcdiag 派生的每核满载压测进程(谱系#11案crash实测确认;原勘察表误记为'本仓库探针',案27报告已澄清),首次作为崩溃进程出现。

## Global Constraints

- 本机即故障机:所有重负载命令 `taskset -c 0-47`,绝不用 CPU179。
- 诚实铁律:报告引用的每条输出必须真实执行过;无 vmcore 的 8 案内存真值对照显式标注"不可验证:kdump vmcore 文件缺失"。
- 分支 `docs/vmcore-case-reports-0912-9dumps`;一案一 commit;不 push main;commit message 无 Co-Authored-By 尾注。
- 报告独立成篇:执行 subagent 禁读 docs/cases/(第一轮)与 docs/cases-2/(第二轮)既有报告正文,仅可引用 SYNTHESIS 的谱系表用于对照(报告"跨案对照"小节允许引用其结论级内容)。**但 crash 取证会话日志、代数脚本输出须作为附件存于各案子目录。**
- 报告目录名:目录名中冒号替换为空(与 cases-2 既有 12 案命名一致),如 `vmcore-diagnosis-report-127.0.0.1-2026-09-07-200426`。

## 报告七要素(每案一致结构)

1. 案情摘要(时间线、受害进程、置信度结论)
2. 崩溃现场六要素(Oops/ESR/FSC/FAR/寄存器组/Call trace,逐字摘录)
3. 指令级解剖(`ldr x20,[x0,w25,sxtw#3]` → `add x27,x1,x20` → `ldr x23,[x27,#288]` 链条;code dump 5 指令反汇编)
4. 坏值形态分析与代数闭合(x27=x1+x20 mod 2⁶⁴、FAR=x27+0x120 验证;形态族归属:零塌缩/字节窗口/高位保留撕裂)
5. 前兆谱(spurious fault 时间戳全谱、末次距致命间隔、CPU 归属)或零前兆负证据
6. 反事实与软件成因排除(RAS 零上报、若装载返回真值则地址有效【仅案 28 可 crash 实测】、taint 自洽性)
7. 根因判定(三级置信)与跨案对照(编号 #20~#28,对照 SYNTHESIS 谱系)

## Task 1: 案 20(09-07-20:04:26)dmesg 法证 + 报告 + commit

- [x] 1.1 复核勘察表数据(uptime/寄存器/前兆 8 次/末次前兆 9978.33 距致命 0.72s——**谱系最短前兆-致命间隔,须精确计算**)
- [x] 1.2 python3 代数闭合(x27=x1+x20;FAR=x27+0x120)脚本写入案目录并运行
- [x] 1.3 dmesg_forensics.txt(关键行原文+行号)、报告 md 撰写
- [x] 1.4 验证(报告引用 vs dmesg 原文逐条对照)→ commit → push

## Task 2: 案 21(09-08-17:21:33)同上四步

- [x] 2.1 复核(前兆 3 次;x20=d3eb5026e000ffff 高段塌缩形态分析——低 16 位 0xffff 标签与案 22-24-26-27 的窗口尾部 0xff/0xffff 系列归并)
- [x] 2.2 代数闭合脚本+运行
- [x] 2.3 附件+报告
- [x] 2.4 验证 → commit → push

## Task 3: 案 22(09-11-14:31:32)同上四步

- [x] 3.1 复核(**x25=179 自指装载**——CPU179 读自己的槽;零前兆;4 连崩第 1 案)
- [x] 3.2 代数闭合
- [x] 3.3 附件+报告
- [x] 3.4 验证 → commit → push

## Task 4: 案 23(09-11-16:30:10)同上四步

- [x] 4.1 复核(x20=ffa9342267e000ff vs FAR 低段 09aeec68998df 错位窗口几何)
- [x] 4.2 代数闭合
- [x] 4.3 附件+报告
- [x] 4.4 验证 → commit → push

## Task 5: 案 24(09-11-17:06:07)同上四步

- [x] 5.1 复核(受害进程 kworker/179:1H 同族;开机仅 1592s 即崩——谱系最短 uptime 崩溃之一;x12=0101010101010101 有趣但与崩溃无关)
- [x] 5.2 代数闭合
- [x] 5.3 附件+报告
- [x] 5.4 验证 → commit → push

## Task 6: 案 25(09-11-17:58:36)同上四步

- [x] 6.1 复核(ESR=0x96000006/L2 变体;零前兆零塌缩)
- [x] 6.2 代数闭合
- [x] 6.3 附件+报告
- [x] 6.4 验证 → commit → push

## Task 7: 案 26(09-12-00:09:19)同上四步

- [x] 7.1 复核(前兆 63 次;末次 21771.26 距致命 1.75s;x20 尾 0xff 窗口)
- [x] 7.2 代数闭合
- [x] 7.3 附件+报告
- [x] 7.4 验证 → commit → push

## Task 8: 案 27(09-12-10:00:31)同上四步

- [x] 8.1 复核(受害进程 neon_rot_ldr_at=本仓库满载探针首次成为崩溃进程;前兆 17 次;exit 系统调用路径 do_task_dead→schedule 崩溃链首见)
- [x] 8.2 代数闭合
- [x] 8.3 附件+报告
- [x] 8.4 验证 → commit → push

## Task 9: 案 28(09-14-01:45:56)完整 crash 取证 + 报告 + commit

- [ ] 9.1 dmesg 法证(前兆 184 次新纪录;swapper/179 idle softirq 路径)
- [ ] 9.2 taskset -c 0-47 下 crash 冷加载 12GB vmcore(`crash -i cmdfile` 批处理,timeout 590+)
- [ ] 9.3 x1 语义钉死(p runqueues/sym x1)、`__per_cpu_offset[7]` 真值 vs 实收 x20=0 对照、反事实 vtop(x1+off[7]+0x120) VALID 验证、FAR 页表几何
- [ ] 9.4 附件(crash 会话 log)+报告
- [ ] 9.5 验证 → commit → push

## Task 10: 收尾——9 案汇总增量 + SYNTHESIS 更新

- [ ] 10.1 9 案增量小结写入本计划文件尾(或 SYNTHESIS 附记):4 连崩跨重启复现、前兆-致命间隔 0.72s 新纪录、184 前兆新纪录、neon_rot_ldr_at 首次成为受害进程、`__per_cpu_offset[7]` 真值对照(案 28)
- [ ] 10.2 分支最终状态确认 + push
