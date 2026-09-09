# 09-07 两案 vmcore 深度诊断计划（core179 第 18/19 次转储）

> **For agentic workers:** 本计划按 superpowers 计划范式撰写；一案一 commit（one-patch-per-unit）。执行时逐项勾选 `- [ ]`。

**Goal:** 为 `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-09-07-13:51:42/`（第 18 次）与 `127.0.0.1-2026-09-07-15:16:31/`（第 19 次）两个 vmcore 各产出一份七要素深度诊断报告，存入 `docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-09-07-<HHMMSS>/`，全部结论基于真实执行的取证命令输出，区分【实锤】/【强推】/【假设】三级置信。

**Architecture:** 复用 12 案 census 方法论（`docs/cases/CPU179_TWELVE_BOOT_CENSUS.md`）与 08-26 范本报告结构。案 18 有 17GB PARTIAL vmcore 可做 crash 动态取证；案 19 无 vmcore 文件（kdump 未完成），只能 dmesg 法证 + 代数闭合，内存真值对照显式标注不可验证。

**Tech Stack:** crash 8.0.4-17.oe2403sp4 + debuginfo vmlinux（`/usr/lib/debug/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`）、python3（模 2⁶⁴ 代数）、grep/awk。

## 已勘察事实（2026-09-09 实证，执行者须复核）

- 两案 panic 均 `CPU: 179`、`pc : find_busiest_group+0x140/0xb60`、Code 字段 `f9400782 f879d814 2a1903e0 8b14003b (f9409377)` 与既往 11 案逐字相同。
- 案 18：ESR=0x96000006 / FSC=L2（pmd=0 变体，同第 11 次）、FAR=`ffffdf9b728097e0`、x20=0、x27==x1=`ffffdf9b728096c0`、x25=8、38 次 WARNING 全部 CPU179、崩溃进程 mi-scavenger (PID 1177282)、uptime≈223640s。已有三轮 crash 会话（/tmp/crash-0907/session1-3.log）：off[0]=ffffa0650d80e000、off[8]=ffffa0650d91e000、off[179]=ffffa0650efd4000、__per_cpu_offset=ffffdf9b72c055d0。
- 案 19：ESR=0x96000004 / FSC=L0、FAR=`ffdbc44e0c5e98df`（非规范）、x20=`ffdc206dfa4000ff`（撕裂形态）、x25=0xa1=161、0 次 WARNING（零前兆，同第 11 次案）、崩溃进程 HeapHelper (PID 57029)、uptime≈4615.7s。**python 已验：x27 = x1+x20 (mod 2⁶⁴) 精确成立，FAR = x27+0x120 精确成立。**
- 案 18 疑点（P4 须查明）：x20 实收 0（零塌缩族特征），但 x27==x1==ffffdf9b728096c0 ≠ 既往零塌缩族的 `.data..percpu` 模板塌缩地址形态（ffffa...开头）。x1 的语义须由反汇编+内存真值确定（`ldr x1,[x19,#56]` 的来源）。**注意既往 12 案中 x1 = &runqueues 模板地址，本案 x1=ffffdf9b728096c0 高位 ffffdf9b 与 __per_cpu_offset=ffffdf9b72c055d0 同段——需 crash 复核 x1 是否为 runqueues 符号地址（KASLR 本相位下）。**
- 编号：按开机时序为第 18、19 次致命转储（12 案 census 截至第 12 次 09-04-12:33；09-04 后续 21:53/22:09/22:27/22:39/23:37 五案为第 13~17 次，已有报告）。
- 内核版本一致 `6.6.0-145.3.23.154.oe2403sp3.aarch64 #1`，debuginfo 可复用。

## Global Constraints

- 本机即故障机：重负载命令 taskset -c 0-47，绝不用 CPU 179。
- 诚实铁律：引用输出必须真实执行；案 19 内存真值不可验证须显式声明。
- 分支 `docs/vmcore-case-reports-0907-2dumps`；一案一 commit；不 push main；无 Co-Authored-By 尾注。

## Task 1: 案 18（13:51:42）dmesg 全量法证

- [x] 1.1 WARNING 时间戳全谱提取（38 条，簇发结构分析）
- [x] 1.2 开机→panic 时间线表（0 → 33497 首症 → 71564 末次 WARNING → 223640 panic；注意 71564 后静默 152076s≈42.2h）
- [x] 1.3 崩溃块六要素摘录（Oops/ESR/FSC/FAR/寄存器/Call trace）
- [x] 1.4 受害进程身份与业务语义（mi-scavenger，futex→newidle 路径，与第 6 次 08-26 同型）

## Task 2: 案 18 crash 动态取证

- [x] 2.1 taskset 隔离下冷加载 17GB PARTIAL dump（复用既有 /tmp/crash-0907 会话结论，新会话补充）
- [x] 2.2 x1 语义钉死：`p runqueues` / `sym ffffdf9b728096c0` 附近符号 / 反汇编 fair.c:12050 上下文确定 x1 来源
- [x] 2.3 `__per_cpu_offset[]` 数组完整性 + 槽 8 真值（ffffa0650d91e000）vs 实收 0 对照
- [x] 2.4 反事实：vtop(x1 + off[8] + 0x120) 应 VALID 且内嵌自指针一致
- [x] 2.5 FAR 页表几何 vtop 复核（L2/pmd=0，与第 11 次案并排归一）

## Task 3: 案 18 报告撰写 + commit

- [x] 3.1 七要素报告写入 `docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-09-07-135142/`（含 algebra.py + 输出）
- [x] 3.2 验证（报告引用与 crash log 逐条对照）→ commit → push

## Task 4: 案 19（15:16:31）dmesg 法证 + 代数闭合 + 报告 + commit

- [x] 4.1 dmesg 全量法证（零前兆负证据；开机 4615.7s 时间线）
- [x] 4.2 代数闭合脚本（x27=x1+x20、FAR=x27+0x120 已验；x20 撕裂窗口形态初判——无 vmcore 不可做窗口直读，降级【强推】）
- [x] 4.3 七要素报告（内存真值对照显式标注"不可验证：kdump vmcore 文件缺失"）
- [x] 4.4 验证 → commit → push

## Task 5: 收尾

- [x] 5.1 两案跨案增量小结（18/19 案对 census 的增量：WARNING 谱 +42.2h 超长静默样本、案19 零前兆第二例）
- [x] 5.2 分支最终状态确认 + push
