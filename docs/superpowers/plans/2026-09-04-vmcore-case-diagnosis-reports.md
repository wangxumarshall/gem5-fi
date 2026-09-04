# 七个新 vmcore 深度诊断报告计划（core179 第 2/7/8/9/10/11/12 次转储）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `/home/sdc/wangxu/vmcore0102/` 下 7 个尚无诊断报告的 vmcore 各产出一份深度诊断报告，存入 `docs/cases/vmcore-diagnosis-report-127.0.0.1-<YYYY-MM-DD>-<HHMMSS>/`（命名遵循现有规则），每份报告七要素齐备：**时间线、逻辑链条、故障根因、故障现象、业务现象、诊断定位过程、启示**。所有结论 100% 基于真实执行的取证命令输出，区分【实锤】/【强推】/【假设】三级置信。

**Architecture:** 三层推进。(P0) 工具链就位：定位/安装 crash 8.0.4，验证 debuginfo vmlinux 与内核精确匹配。(P1) 逐案法证：每个转储独立走"dmesg 全量法证 → crash 动态取证（完整转储）→ 寄存器代数闭合 → 内存真值对照 → 反事实验证"闭环，方法完全复用 08-26 范本报告（docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-08-26-103727/）。(P2) 横向综合：十二案总表更新 + 根因模型增量确认。**one-patch-per-unit：一案一 commit。**

**Tech Stack:** crash 8.0.4 + 内核 debuginfo（`6.6.0-145.3.23.154.oe2403sp3.aarch64`，既往路径 `/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux`）、objdump -dl / addr2line、grep/awk（dmesg 法证）、Python3（64 位模 2⁶⁴ 地址代数复算）、/usr/src/debug 内核源码。

## Global Constraints

- **诚实铁律（CLAUDE.md）**：报告中每一处引用的命令输出必须是真实执行后摘录的，禁止预测/杜撰；执行者自验时把实际输出与报告文本逐条对照。无法验证的项目（尤其 08-17 与 09-04-12:33 两个 incomplete 转储的内存真值）必须显式标注"不可验证 + 原因"，不得伪装成已验证。
- **本机即 core179 故障机**：所有重负载命令（crash 加载、objdump 大段反汇编）必须 `taskset -c 0-47`（或 0-31）隔离，**绝不使用 CPU 179**。crash 加载 10~74 GB 转储预计耗时数分钟到数十分钟，用后台运行 + 超时保护。
- **一案一 commit**：分支 `docs/vmcore-case-reports-7dumps`（从 main 切出）；每完成一案：验证 → commit → push；不 push main；commit message 不带 Co-Authored-By: Claude 尾注。
- **不重写既有 5 案报告**：08-14/08-24/08-25×2/08-26 已有报告，本次只新增 7 份；既有报告中的跨案统计如有增量（如"5/6 次同指令"应更新为"11/12"），在**本次新报告**与**终案综合**中更新，不回改旧报告正文（旧报告是历史快照）。
- **序号规则**：按开机时间全局编号，08-26 报告自称"第 6 次致命转储"。本次 7 案编号：08-17 = **第 2 次**（补写，报告头须注明"补写身份：本报告撰写于 2026-09-04，晚于第 3~6 次报告，但所诊断的转储时序为第 2 次"）、08-31 = **第 7 次**、09-03-18:25 = **第 8 次**、09-04-09:15 = **第 9 次**、09-04-10:27 = **第 10 次**、09-04-11:00 = **第 11 次**、09-04-12:33 = **第 12 次**。
- **报告结构模板**（从 08-26 范本继承，七要素映射固定，后续 Task 不得漂移）：

```markdown
# CPU179 缺陷核第 N 次致命转储深度诊断报告
## ——（单案标题，可含跨案副题）

| 项 | 值 |                      ← 表头：目标转储/主机/CPU/内核/崩溃时刻+进程/结论
## 1. 执行摘要                        ← 4~6 条编号结论
## 2. 证据规则与方法                  ← 只依据 vmcore/vmcore-dmesg；三级置信标注；工具清单
## 3. 本次开机时间线                  ← 【时间线】开机→首症(WARNING)→…→panic 全序列（真实时间戳表）
## 4. 故障现象                        ← 【故障现象】Oops/ESR/FSC/FAR/Call trace 原文摘录
## 5. 业务现象                        ← 【业务现象】崩溃进程是谁(sftp-server/mi-scavenger/rcu_sched/kworker/swapper)、
                                          它当时在做什么业务、崩溃对上层服务的表现(传输中断/扫描停摆/机器重启)
## 6. 诊断定位过程                    ← 【诊断定位过程】P1勘察→P2静态反汇编→P3 crash动态取证→P4软件根因排除→P5定论
                                          每步：命令 + 真实输出摘录 + 推理
## 7. 逻辑链条（寄存器代数闭合与反事实）  ← 【逻辑链条】x27=x1+x20、FAR=x27+0x120 逐位闭合；
                                          内存真值 vs 实收值对照；反事实推演"若收到真值则不崩"
## 8. 故障根因                        ← 【故障根因】子族归类（零塌缩/撕裂移位）+ LSU 装载数据返回通路 SDC 判定
## 9. 启示                            ← 【启示】本案新证据对根因模型的增量 + 工程启示（fail-fast/位置锚定校验/PEPR
                                          三启示在本案的体现，引用 core179-microarch-rootcause-synthesis/paper_zh.md §6）
## 10. 处置建议                       ← offline CPU179 + RMA 状态追踪
## 附录：命令索引                      ← 本报告全部取证命令（可复核）
```

- **置信度约定**：【实锤】= dump 内可复核证据；【强推】= 多源证据收敛的推断；【假设】= 无法软件验证的部分，明示验证途径。
- **代数计算一律脚本化**：所有 64 位地址加法/旋转/汉明距离用 Python3 计算（模 2⁶⁴），禁止手算；脚本与输出存入案件目录（如 `forensics.py` + 输出摘录入报告）。
- **已勘察事实（计划撰写时实证，2026-09-04，执行者可直接引用但须复核关键项）**：
  - 7/7 案 panic 均 `CPU: 179`、均 `pc : find_busiest_group+0x140/0xb60`、Code 字段与既往一致（`…8b14003b (f9409377)`）；
  - 7 案 WARNING（spurious fault，`arch/arm64/mm/fault.c:494 __do_kernel_fault`）全部 CPU179，非 179 核计数为 0；计数：08-17:26、08-31:13、09-03:35、09-04-09:2、09-04-10:2、09-04-11:0、09-04-12:1；
  - 09-04-11:00 案寄存器已初抽：x20=0、x27==x1==`ffffd77069c696c0`、FAR=`ffffd77069c697e0`==x27+0x120、x25=0x61（=97，迭代 CPU 号）、**pmd=0 → FSC=L2（新变体，既往零塌缩族是 pte=0/FSC=L3）**；
  - FAR 形态初判：08-17/08-31/09-03/09-04-09:15 四案 FAR 为非规范小值/高位零（`00ff…`/`0000…`/`2cd7…`）→ 疑似撕裂移位族（x20≫8 或移位形态，须 crash 内存真值对照后定论）；09-04-10:27/11:00/12:33 三案 FAR 为 `ffff…97e0` 型 → 疑似零塌缩族（x27==x1 模板地址塌缩）；
  - 内核版本 7 案一致：`6.6.0-145.3.23.154.oe2403sp3.aarch64 #1`（与既往 6 案相同，debuginfo 可复用）；
  - vmcore 文件属主 sdc、mode 0600 → 读取无需 sudo；crash 二进制当前不在 PATH（P0 解决）。

---

## Task 0（P0）: 工具链就位与冒烟验证

**Files:**
- Create: `/tmp/vmcore-cases-20260904/toolchain-check.log`（证据日志，不入仓库）
- Create: `.planning/2026-09-04-vmcore-case-diagnosis-reports/` 下 progress.md 追加结果

**Interfaces:**
- Produces: 可用的 `crash` 命令路径 + 验证过的 debuginfo vmlinux 路径，供后续所有 Task 引用。

- [ ] **Step 0.1: 定位或安装 crash 8.0.4**

按序尝试（先定位后安装，3-strike 协议）：
```bash
# 尝试 1：历史路径与包管理器查询
ls /usr/lib/debug/usr/lib/modules/ 2>&1            # debuginfo 是否仍在
rpm -qa | grep -i crash                             # crash 包是否装过
find / -maxdepth 5 -name crash -type f 2>/dev/null | grep -vE "proc|sys" | head
# 尝试 2：dnf 安装（需要 sudo；若 sudo 需密码则请用户执行，用 ! 前缀交互）
#   用户在会话中输入: ! sudo dnf install -y crash crash-arm64-packages 2>&1 | tail -5
# 尝试 3：若仓库无 crash-arm64，从源码构建（记录到 progress.md 并请示用户）
```
成功标准：`crash --version` 输出 8.x；记录二进制绝对路径。

- [ ] **Step 0.2: debuginfo vmlinux 就位校验**

```bash
VL=/usr/lib/debug/usr/lib/modules/6.6.0-145.3.23.154.oe2403sp3.aarch64/vmlinux
ls -la $VL && file $VL | grep -o "BuildID.*"
```
预期：BuildID 存在且带 debug_info。若路径不存在 → `dnf` 装 kernel-debuginfo（须用户 sudo 配合）。**注意：`gem5-fs/vmlinux` 是 gem5 仿真内核（BuildID fcd50d99…），严禁用于生产转储法证**——若 BuildID 与 debuginfo 一致才可用作对照，否则只用 debuginfo 版本。

- [ ] **Step 0.3: crash 冒烟（最小完整转储冷加载）**

用最小的完整转储（09-04-12:33 是 incomplete；用 08-31 的 14.7G）：
```bash
mkdir -p /tmp/vmcore-cases-20260904
cd /tmp/vmcore-cases-20260904
taskset -c 0-31 timeout 1800 crash <debuginfo-vmlinux> \
  /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-31-00:47:32/vmcore \
  -i /dev/stdin <<'EOF' > toolchain-check.log 2>&1
sys
log | tail -5
quit
EOF
tail -20 toolchain-check.log
```
预期：出现 `crash>` 命令回显、`sys` 输出 KERNEL/CPUS/MEMORY，无 "cannot open" 类错误。记录加载耗时。
（若 crash 对该转储拒载 → 如实记录错误，改用 09-04-11:00 的 46.9G 转储重试一次；仍失败则 escalate 用户。）

- [ ] **Step 0.4: 分支建立与工具链 commit（空跑验证提交链路）**

```bash
cd /home/sdc/wangxu/vmcore0102/gem5-fi
git checkout -b docs/vmcore-case-reports-7dumps
```
本 Task 产物在 /tmp 与 .planning，若 .planning 未被 .gitignore 排除则不入库（检查 `git status`）；本 Task 可无 commit（纯勘察），但必须在 progress.md 记录工具链三要素：crash 路径 / debuginfo vmlinux 路径 / 冒烟输出摘录。

---

## Task 1: 第 2 次转储（2026-08-17-13:47:08，vmcore-incomplete）诊断报告

**Files:**
- Create: `docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-08-17-134708/vmcore-diagnosis-report-127.0.0.1-2026-08-17-134708.md`
- Create: 同目录 `dmesg_forensics.txt`（grep/awk 法证命令与输出日志）

**Interfaces:**
- 输入: `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-17-13:47:08/`（vmcore-incomplete 28.9G + vmcore-dmesg.txt 287K）
- Produces: 第 2 次转储报告（dmesg-only 法证，crash 部分明示不可验证）。

**背景（已勘察）**：panic 于 uptime 239527.8s（~66.5h，历来最长存活），进程 swapper/179（PID 0，idle 路径 newidle_balance——与 08-26 案同路径），FAR=`00ffd780f5a3a7c0`（高位零 → 撕裂移位族形态），ESR=0x96000004（FSC=L0），26 次 WARNING 全 CPU179。既往 08-26 报告已注明本转储"incomplete，kdump 未完成，内存真值不可验证，x20≫8 归类置信度中高"。

- [ ] **Step 1.1: dmesg 全量法证**

```bash
D=/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-17-13:47:08/vmcore-dmesg.txt
grep -nE "Linux version|Command line|Memory:" $D | head -5          # 开机指纹
grep -n "WARNING: CPU:" $D | wc -l                                    # WARNING 总数（预期 26）
grep -oE "WARNING: CPU: [0-9]+" $D | sort | uniq -c                   # per-CPU 分布（预期仅 179）
awk '/Unable to handle/{f=1} f{print; c++} c>90{exit}' $D > /tmp/vmcore-cases-20260904/case2-crash-block.txt
cat /tmp/vmcore-cases-20260904/case2-crash-block.txt                  # 完整崩溃块：寄存器 x0~x30 全量
grep -nE "ERRIDR|ERX|EDAC|BERT|GHES|mce|ras" $D | head               # RAS 负证据
awk '/WARNING: CPU: 179/{print}' $D | head -3                          # WARNING 形态（ESR/FAR 样本）
grep -E "^\[" $D | head -1; tail -3 $D                                # 开机零点与 panic 终点（时间线端点）
```
全部输出存 `dmesg_forensics.txt`。从崩溃块提取 x20/x25/x27/x1 并用 Python 复算 `x27 = x1 + x20 (mod 2^64)` 与 `FAR` 关系（脚本输出入附录）。

- [ ] **Step 1.2: 尝试 crash 加载（预期失败，如实记录）**

```bash
taskset -c 0-31 timeout 1800 crash <debuginfo-vmlinux> \
  /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-17-13:47:08/vmcore-incomplete -i /dev/stdin <<'EOF' 2>&1 | tail -10
sys
quit
EOF
```
预期（依既往经验）：拒载或数据不全。**如实记录错误信息**，写入报告 §6 作为"诊断定位过程"的一部分（法证边界声明）。

- [ ] **Step 1.3: 报告撰写（七要素模板全章）**

按 Global Constraints 模板撰写，特别注意：
- §5 业务现象：swapper/179 idle 调度路径崩溃 = 机器本轮最长存活 66.5h 后整体重启；
- §8 故障根因：撕裂移位族归类标【强推】（无内存真值对照），明示"若 vmcore 可载则可升级为实锤"；
- §9 启示：本案存活 66.5h 说明故障率极低（间隔发作），对"巡检式检测（fleetscanner）检出窗口"的启示；
- 报告头注明补写身份（撰写于 2026-09-04，晚于第 3~6 次报告）。

- [ ] **Step 1.4: 自验证 + commit + push**

```bash
# 自验证 1：七要素章节齐全
for s in 时间线 逻辑链条 故障根因 故障现象 业务现象 诊断定位过程 启示; do \
  grep -q "【$s】" docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-08-17-134708/*.md && echo "OK $s" || echo "MISS $s"; done
# 自验证 2：报告引用的 dmesg 行号真实存在（抽查 5 处）
# 自验证 3：Python 代数复算输出与报告数值逐位一致
git add docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-08-17-134708/
git commit -m "docs(cases): 第2次转储(08-17)诊断报告 — dmesg-only法证, 撕裂移位族【强推】, incomplete边界声明"
git push -u origin docs/vmcore-case-reports-7dumps
```

---

## Task 2: 第 7 次转储（2026-08-31-00:47:32，14.7G 完整）诊断报告

**Files:**
- Create: `docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-08-31-004732/vmcore-diagnosis-report-127.0.0.1-2026-08-31-004732.md`
- Create: 同目录 `forensics_cmds.txt`（crash 批量命令）+ `crash_session.log`（完整输出）+ `algebra.py`（代数复算脚本与输出）

**Interfaces:**
- 输入: `/home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-31-00:47:32/`
- Produces: 第 7 次转储报告（完整 crash 法证闭环）。

**背景（已勘察）**：uptime 396122.7s（~110h，刷新最长存活纪录），进程 rcu_sched（PID 16），FAR=`0000c1a9443c9305`（高位零 → 撕裂移位族形态），ESR=0x96000004（L0），13 次 WARNING 全 CPU179。

- [ ] **Step 2.1: dmesg 全量法证**（同 Task 1.1 命令模板，输出入 forensics 附件）

- [ ] **Step 2.2: crash 动态取证（决定性实验：内存真值对照）**

```bash
taskset -c 0-31 timeout 3600 crash <debuginfo-vmlinux> \
  /home/sdc/wangxu/vmcore0102/127.0.0.1-2026-08-31-00:47:32/vmcore \
  -i forensics_cmds.txt > crash_session.log 2>&1
```
`forensics_cmds.txt` 内容（08-26 范本方法复用，KASLR 基址先从 `sym find_busiest_group` 获取再套用）：
```
sys
bt
sym find_busiest_group
sym runqueues
sym __per_cpu_offset
px __per_cpu_offset[179]
rd -64 __per_cpu_offset 192
px ((char *)&__per_cpu_offset)[0]        # 撕裂移位族: 检查数组首槽与后续内存
vtop <FAR>                                # 故障地址页表走查
vtop <x27_true>                           # 反事实地址走查（应 VALID）
p runqueues:179                           # crash 内建 per-cpu 解析交叉验证
quit
```
判定分支：
- 若 x20 与 `__per_cpu_offset[179]` 真值不一致而数组整体完好（等差数列）→ 内存完好+寄存器收坏实锤（D1 通路）；
- 用 Python 对 x20 与各槽位做旋转/移位匹配（ror/rol 1~7 字节、字节通道错位），确定撕裂子族形态与汉明距离；
- 若数组本身损坏 → **停止，如实报告**（这将动摇既有根因模型，是重大发现，须 escalate 用户讨论后再成文）。

- [ ] **Step 2.3: 反事实验证**

Python 计算 `x27_true = (&runqueues + __per_cpu_offset[179]) mod 2^64`；crash `vtop x27_true` 须 VALID；`p runqueues:179` 实例健全性（cpu=179、curr 指向崩溃任务或一致状态）。三重验证逐位一致后写入 §7。

- [ ] **Step 2.4: 报告撰写 + 七要素自验证 + commit + push**（同 Task 1.4 模板）

特别注意 §5 业务现象：rcu_sched 是内核 RCU 后台线程——它崩溃意味着什么（宽限期停滞风险→本次直接整机 panic）；§9 启示：110h 存活 + 13 次 WARNING 的发作频率统计对"预测模型"的启示。

---

## Task 3: 第 8 次转储（2026-09-03-18:25:12，73.7G 完整）诊断报告

**Files:** 同 Task 2 模式，目录 `vmcore-diagnosis-report-127.0.0.1-2026-09-03-182512/`

**背景（已勘察）**：uptime 322246.2s（~89.5h），进程 rcu_sched（PID 16），FAR=`00ffc99ebbaad120`（高位零→撕裂移位族形态），ESR=0x96000004（L0），**35 次 WARNING**（历来最多），且 WARNING 时间戳呈簇状爆发（142792s 处 10 秒内 6 连发）。

- [ ] **Step 3.1: dmesg 法证 + WARNING 簇分析**

额外命令（簇状爆发是本案特色，时间线必须逐条列出）：
```bash
grep "WARNING: CPU: 179" $D | awk -F'[][]' '{print $2}' | sort -n | uniq -c | awk '{print $2, "x"$1}'   # 时间戳聚类
grep -B2 "WARNING: CPU: 179" $D | grep -E "esr|far|at " | head -10    # WARNING 的 ESR/FAR 形态
```

- [ ] **Step 3.2: crash 动态取证**（同 Task 2.2 模板；73.7G 加载耗时更长，timeout 7200，后台运行）

- [ ] **Step 3.3: 报告撰写 + 自验证 + commit + push**

特别地，§3 时间线要呈现"静默 40h → 142792s 簇爆发（10s 内 6 起）→ 10s 后 panic"的脉冲式发作模式，§9 启示讨论其对"电压/频率相依性"假说的支撑（簇发 = 边际条件窗口）。

---

## Task 4: 第 9 次转储（2026-09-04-09:15:42，10.6G 完整）诊断报告

**Files:** 同 Task 2 模式，目录 `vmcore-diagnosis-report-127.0.0.1-2026-09-04-091542/`

**背景（已勘察）**：uptime 52269.8s（~14.5h），进程 kworker/u392:0（PID 1154762），FAR=`2cd7ddf3a9089790`（**全新形态：非规范大值，既非 ffff 高位也非 0000 高位**），ESR=0x96000004（L0），2 次 WARNING（2582s PID 16 / 13867s PID 422956）。

- [ ] **Step 4.1: dmesg 法证 + 崩溃块全量寄存器提取**

FAR 形态特殊：`2cd7ddf3a9089790` 疑似 x20 为大幅污染值（非零塌缩、非简单移位）。须从崩溃块提取 x20/x27/x1 后 Python 复算闭合关系，**在 crash 真值对照前不预设子族归类**。

- [ ] **Step 4.2: crash 动态取证**

重点：x20 与真值 `__per_cpu_offset[179]` 的关系分析——若是随机污染（与任何槽位无旋转/移位关系），则是**新子族**（随机位翻转族），报告须如实归类并讨论对根因模型的修正（既往仅两子族：零塌缩/撕裂移位）。汉明距离 popcount、与 192 槽位逐一比对（既往经验 crash search 命令失效，用 rd 全数组导出 + Python 比对）。

- [ ] **Step 4.3: 报告撰写 + 自验证 + commit + push**

§9 启示若确认为新子族：对"单一故障机制多形态表征"的讨论（fill-buffer 竞态的不同相位 → 不同污染形态）。

---

## Task 5: 第 10 次转储（2026-09-04-10:27:58，29.7G 完整）诊断报告

**Files:** 同 Task 2 模式，目录 `vmcore-diagnosis-report-127.0.0.1-2026-09-04-102758/`

**背景（已勘察）**：uptime 3951.2s（~1.1h，短存活），进程 sftp-server（PID 293168），FAR=`ffffd99f13ae97e0`（97e0 型→零塌缩族形态），ESR=0x96000007（**L3**，pte=0），2 次 WARNING（2099/2117s，PID 16）。

- [ ] **Step 5.1: dmesg 法证**（标准模板）
- [ ] **Step 5.2: crash 动态取证**（标准闭环：真值对照+反事实；预期 x20=0、x27==x1==模板地址、FAR=x27+0x120）
- [ ] **Step 5.3: 报告撰写 + 自验证 + commit + push**

特别地 §5 业务现象：sftp-server 在 pipe_write→schedule→newidle_balance 崩溃 = 用户文件传输会话中断（与 08-26 案 mi-scavenger 同为用户态业务进程视角）；§3 时间线：开机 35 分钟首症、70 分钟死亡——短存活案例。

---

## Task 6: 第 11 次转储（2026-09-04-11:00:00，46.9G 完整）诊断报告

**Files:** 同 Task 2 模式，目录 `vmcore-diagnosis-report-127.0.0.1-2026-09-04-110000/`

**背景（已勘察+寄存器已初抽）**：uptime 1456.2s（**~24 分钟，最短存活**），进程 sftp-server（PID 56263），Not tainted（唯一），FAR=`ffffd77069c697e0`，ESR=0x96000006（**FSC=L2，pmd=0——新变体**：既往零塌缩族均为 L3/pte=0），**0 次 WARNING**（唯一无前兆直接死亡的案例），寄存器：x20=0、x27==x1==`ffffd77069c696c0`、x25=0x61(=97)、x9=`ffffd7706823ae58`（KASLR 锚）、Call trace 经 pipe_write→…→el0t_64_sync。

- [ ] **Step 6.1: dmesg 法证**（标准模板 + 确认零 WARNING）

- [ ] **Step 6.2: crash 动态取证 + L2/L3 变体专项分析**

标准闭环之外，专项解释 **pmd=0 而非 pte=0**：零塌缩后 x27 落在 `.data..percpu` 模板地址，本次页表走查在 PMD 级即断（pte 级都未到）。用 crash `vtop` 分别对 x27 与 FAR 走查并对比 08-26 案（pte=0）：确认是**同一零塌缩机制的页表几何差异**（init 区 free_initmem 后不同粒度的解映射边界）而非新故障通路。此分析须【实锤】级：两级走查输出并排呈现。

- [ ] **Step 6.3: 报告撰写 + 自验证 + commit + push**

§3 时间线突出"零前兆、24 分钟速死"；§9 启示：无 WARNING 直接 panic 对"用 WARNING 做预警监控"策略的边界讨论（fail-fast 启示的反面佐证：本案例连 spurious 前兆都没有）。

---

## Task 7: 第 12 次转储（2026-09-04-12:33:31，vmcore-incomplete）诊断报告

**Files:** 同 Task 1 模式（dmesg-only），目录 `vmcore-diagnosis-report-127.0.0.1-2026-09-04-123331/`

**背景（已勘察）**：uptime 5060.5s（~1.4h），进程 mi-scavenger（PID 55114，与 08-26 案同进程），FAR=`ffffc8a996d397e0`（97e0 型→零塌缩族形态），ESR=0x96000007（L3），1 次 WARNING（5022s，PID 61156）。vmcore 9.2G incomplete（kdump 未完成）。

- [ ] **Step 7.1: dmesg 全量法证**（同 Task 1.1；寄存器块提取 + Python 代数闭合复算）
- [ ] **Step 7.2: crash 加载尝试**（同 Task 1.2，预期拒载/不全，如实记录）
- [ ] **Step 7.3: 报告撰写 + 自验证 + commit + push**

零塌缩族归类置信度：FAR 形态 + x27==x1 若在崩溃块中闭合 →【强推】；§9 启示：与 08-26 案同进程（mi-scavenger）同路径（futex_wait_queue→newidle_balance）——同一业务负载反复踩中同一调度路径的统计规律。

---

## Task 8: 十二案横向综合更新与收尾

**Files:**
- Create: `docs/cases/vmcore-diagnosis-report-127.0.0.1-2026-09-04-123331/` 之外的汇总更新——在最后一个案件报告（Task 7 产物）§4 或独立小节，或单独创建 `docs/cases/CPU179_TWELVE_BOOT_CENSUS.md`（执行时按信息量决定，倾向独立文件）
- Update: `.planning/2026-09-04-vmcore-case-diagnosis-reports/task_plan.md`（全部勾选）

**Interfaces:**
- Produces: 十二开机总表（每次开机：日期/uptime/进程/子族/ESR/FSC/寄存器闭合/内存真值验证状态/WARNING 数）、根因模型最终陈述、处置时间线（offline+RMA 是否已执行）。

- [ ] **Step 8.1: 十二案总表编制**（全部数据点来自 12 份已发布报告，逐项引用出处）

```bash
# 汇总校验：12 份报告齐全
ls docs/cases/ | grep -c "vmcore-diagnosis-report-127.0.0.1"   # 预期 12
# 七要素 12 份全查
for d in docs/cases/vmcore-diagnosis-report-*/; do for s in 时间线 逻辑链条 故障根因 故障现象 业务现象 诊断定位过程 启示; do grep -q "【$s】" $d/*.md || echo "MISS $d $s"; done; done
# 预期无输出（全部命中）
```

- [ ] **Step 8.2: 综合结论 + 最终 commit + push**

汇总统计预期（以执行实测为准，计划期数字仅为待证先验）：12 次开机异常 100% CPU179、~11/12 同指令 `find_busiest_group+0x140`（08-14 若为异例则 11/12，如实统计）、子族谱（零塌缩/撕裂移位/可能的随机污染新族）、WARNING 谱与 panic 间隔分布。处置建议追踪：CPU179 是否已 offline（`grep -E "offline|isolated" <任一>dmesg` 查 command line 佐证）。

```bash
git add -A docs/cases/
git commit -m "docs(cases): 十二案横向综合 — CPU179 缺陷核全谱收敛（第2~12次转储报告完成）"
git push
```

---

## Self-Review 记录（计划撰写时执行）

1. **Spec 覆盖**：用户要求"每个 vmcore 深度研究 + 诊断报告 + docs/cases 独立目录 + 现有命名规则 + 七要素一个不能少"——12 案中 5 案已有报告（不重写，避免破坏历史快照），7 案逐案成文（Task 1~7），七要素在模板中逐字锚定并配自验证命令；"最先进的 skill"= planning-with-files（本计划由其驱动）+ superpowers 计划纪律 + subagent-driven-development 执行。工具链风险（crash 缺失）单列 Task 0。
2. **占位符扫描**：`<debuginfo-vmlinux>`/`<FAR>` 等尖括号占位是执行期才可知的动态值（Task 0 产出/各案 dmesg 提取），非内容缺失；crash 命令块中 KASLR 相关地址依赖 `sym` 输出，模板已注明"先取基址再套用"。
3. **类型一致性**：目录/文件名 `127.0.0.1-<date>-<hhmmss>`（冒号去除）与现有 5 例逐字一致；序号链（第 2/7/8/9/10/11/12 次）与 08-26 报告"第 6 次"自洽；分支名 `docs/vmcore-case-reports-7dumps` 全计划唯一。
4. **诚实性**：计划期勘察数据（7 案 CPU179/同指令/寄存器初抽）全部来自本会话真实命令输出，已在 Global Constraints 标注"执行者须复核"；两个 incomplete 转储的法证边界、crash 拒载预期、x20 子族归类置信度全部显式降级（【强推】而非【实锤】）；Task 2.2 内置"若数组本身损坏则停止并 escalate"的证伪分支——执行者不得为凑结论而跳过。
5. **资源现实性**：本机即故障机（taskset 隔离硬约束）；29G 内存加载最大 73.7G 转储依赖 crash 惰性读页（既往 116G 成功先例）；sudo 依赖点仅 debuginfo 安装（Task 0，用户 `!` 前缀交互）；308G 磁盘足够（crash 会话日志为文本）。
