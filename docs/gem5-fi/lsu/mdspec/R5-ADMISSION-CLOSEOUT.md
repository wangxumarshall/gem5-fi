# R5 正式准入收官 — 状态快照（2026-10-22）

- 分支：`lsu-mdspec-20261019`（worktree `.claude/worktrees/lsu-mdspec-20261019`）
- 基线：`677b6fa1`（R4-10 集成报告）→ 本轮 R5 提交见 §5
- 权威规格：`gem5-fi-LSU单元故障注入方案.md` + 4 子文档（-03/-07/-09/-10）
- **结论：仍为 NO-GO。** 契约 `verdict()` 自动判定（非人工声明）。

## 1. 现场恢复（事实，非口头结论）

| 项 | 实测 |
|---|---|
| 主仓库 | `/home/sdc/gem5-fi-ding`，分支 `fi-ding`@`6f98088a`；工作树有 69 个 lsu 跟踪文件被删 + 176 未跟踪（`artifacts/`、`campaigns/` 等）。**本轮全部工作不落在主工作树**。 |
| 集成分支 | `lsu-mdspec-20261019`@`677b6fa1`，与 `origin/lsu-mdspec-20261019` 同步（0/0）；已合入 R4-10-SPEC（=r4-10-spec）、R4-10-FSINFRA、R4-8-FSMC-B。 |
| 分支关系 | `r4-10-spec` 与 `lsu-mdspec-20261019` 同源于 `b113fab4`；后者另有 12 个提交（T05/T06/T07 + T08-b/c/d + 多核 FS + NO-GO 判定 + 正式命令纠正）。 |
| 并发会话 | 另有 2 个 claude 进程；`lsu-mdspec` 工作树 30 分钟内无文件改动、reflog 自 18:48 静止 → 判定无并发冲突，采用"只追加提交、不改写历史"。 |
| 资源 | load ~1.3；MemAvailable 23–26 GiB；`/home` free 76 GiB。未启动 stress-ng / backfill。 |

### 运行中的真实任务（不杀、不干预）

| 任务 | PID | 起 | 判定 |
|---|---|---|---|
| S01-F0-W1 span census（`w1_all`） | 2133313 | 17:44 | **正常推进**：两轮 512 s 采样线性增长（~492 B/s，99.8% CPU）；日志已过 `[w1] patricia exit=1 ok=1`。ETA ≈ 01:00–01:15（或 `SE_W1=43200 s` 超时） |
| T01-F0-W4 集成后 FS pilot（本轮发起） | — | 21:0x | 见 §4 |

## 2. 权威准入复现（非沿用旧数字）

```
$ python3 tools/lsu_ready_contract.py
total=325 READY=241 PARTIAL=0 BLOCKED=84 self_consistent=True
blocked_by_category={'RULING':6,'FS-INFRA':24,'MODE-UNIMPL':3,'UNRESOLVED':4,'FS-MULTICORE':35,'LICENSE':12}
```

**325 机器可读核对**（四源集合运算，非 grep 行数）：ready_contract / runid_map / 规格 -07 / 规格 -09
四集合 unique 各 = 325，两两对称差全 = 0，union = intersection = 325。
源 xlsx sha256 = `389546f0…` 与主文档头 `Source-SHA256` **一致**（未覆盖源表）。

## 3. 本轮修复的真实缺陷（一 unit 一 commit）

| # | 缺陷（实测） | 修复 | commit |
|---|---|---|---|
| D1 | `test_lsu_hook_tlb.py`(2 失败) / `test_lsu_hook_cpf.py`(13 失败)：夹具缺 `corr`，而 R4-4(`acc19511`) 已把 `corr` 列为全部入链事件必录 | 夹具补 `corr=origin`（单行合成夹具无 join 伙伴） | `7b3734a5` |
| D2 | 门禁 `pytest tests/ -q` **只收集 21 个**；~50 个 hook 契约套件是 `main()` 独立脚本，**从不被收集执行**（这才是根因）；D1 的红因此静默数周 | 新增 `tools/lsu_test_runner.py`（逐套件真实子进程 + **解析输出**判定 PASS/SKIP/ENV/FAIL）；`gate()` 接入；`verdict()` 增 NO-GO 理由 | `642ef725` |
| D3 | 旧 obs 管线硬编码已删主树二进制路径（R4-10 磁盘审计刻意删除的陈旧件）→ 4 套件 RED | 统一 `$LSU_GEM5_BIN` → `<repo>/CHAOS/gem5/build/ARM/gem5.opt`；`e2e_select` 依赖的冻结数据/二进制确缺 → **诚实 SKIP 并逐项披露**，未改写 `FROZEN_GEM5_SHA` 充绿 | `039e88ce` |
| D4 | BLOCKED 台账三处总数矛盾（126/100/106 vs 契约 84），20 个 RunID 台账 BLOCKED 而契约 READY，无 UNRESOLVED 桶 | `lsu_blocked_triage.py` 增 `--contract`（直接读契约 category，**单一分类来源**）+ `--approval-out`（裁决清单同源生成，此前手写无生成器）；新增契约测试 `test_lsu_triage_ledger.py` | `728fb375` |
| D5 | 4 条 BLOCKED 行在 `why` 字段**自报 "PASS"**（`_classify` 在 flags=None 分支返回 coverage 状态） | 改引 `resolve_cell` 的真实拒绝理由 | `63a89932` |

另有 R4-10 集成轮已修复、本轮复核确认的：临时调用的 `--phase trial --max-seeds-per-cell 3` 已被
纠正为正式口径；`R4-8-GO` 已被正式纠正为 **NO-GO**（`R4-10-GO-CORRECTION.md`）。

## 4. 对抗性核验（独立 agent，逐条实测）

**已用真实产物核验为真**：
- LICENSE 12：全盘搜 SPEC CPU2017 产物 = **零命中**；`workloads/` 仅 `directed/litmus/mibench/ooo`。
- RULING 6（A06）：证明链 **四处 file:line 逐字正确**（`mem.isa:499` getMemLE → `memhelpers.hh:80 pkt->get<MemT>` → `packet_access.hh:55 assert(sizeof(T)<=size)` → `packet.hh:908 size=req->getSize()`）；真机 `load_shrink=0 / load_shrink_unsafe=1212`，rc=0（静默零已修）。
- FS-MULTICORE 真机：`/tmp/r4-8-fsmcb/run{1,2}` 两臂 `board.terminal` **逐字节相同**；干净臂 prop_evt 仅表头，故障臂有真实链。
- FS-INFRA 根因修复 `e4dcd5da` 是 HEAD 祖先；`configs/fs/lsu_multicore_fs.py`（`--num-cores`，默认 2）已存在。
- 二进制 sha256 `f4dbfb9a66e0df80…`（1,145,188,760 B）与集成报告一致。

**核验推翻/纠错（重要）**：
1. 集成报告称多核 FS "616 事件" —— 实测链文件为 **810 事件 / 585 链节点**。定性结论（干净臂为空、链由注入引起）成立，数字需更正。
2. 集成报告称 "FS 载体在预算内不终止 → 无 L5" —— **过于笼统**：`T04-F0-W4` 达到 `outcome=Crash` 且链 `L0→L1 proven…`（有 L5）；仅 T01/T03/T08 超时。
3. FS-INFRA 的阻塞理由串 `blocked(fs-infra: TLB workload needs FS)` **已被本树自身证据反驳**（T01/T04-F0-W4 在 FS 上 `activated=1`）—— 理由措辞陈旧，需更正（见 §6 待办）。
4. 旧台账里 O04/O09/T05/T06/T07/T08 的 "COMPILE-UNVERIFIED" 文案被冻结二进制的 `strings` 反驳（`rmw_mux`/`rmw_order`/`valid_clear`/`walk_fill_dup` 等均在）—— D4 重生成后已消失。

**仅有散文、盘上无产物支撑的说法**（如实披露）：集成报告 §3 的"scons 零新增告警"、§5 的磁盘回收 GiB 数。

## 5. 本轮提交与推送

```
63a89932 R5-U5  BLOCKED 行自报 PASS 修复 + 门禁接入全套件结果
728fb375 R5-U4  台账与契约同源（消除三处总数矛盾与 42 项漂移）
039e88ce R5-U3  旧 obs 管线硬编码已删主树二进制路径（4 套件 RED→GREEN）
642ef725 R5-U2  门禁真实运行全部套件（新增 lsu_test_runner）
7b3734a5 R5-U1  hook 契约套件与 corr 必录契约漂移修复
75026975 R5-PLAN 计划与三路审计缺陷清单
```
全部推送至 `origin/lsu-mdspec-20261019`。

## 6. BLOCKED 84 逐项处置状态（诚实分类）

| 类别 | n | 处置 | 证据 |
|---|---|---|---|
| LICENSE | 12 | **真外部**（不可自解） | 全盘无 SPEC 产物；规格 sheet 6 W11 = SPEC CPU2017 采样区间 |
| RULING | 6 | **规格级裁决**（已封存） | load SHRINK 结构性不可达，源码级证明链 + 真机 `load_shrink_unsafe=1212` |
| FS-INFRA | 24 | **可跑但未解锁** —— 载体/checkpoint/二进制齐备，T01/T04-F0-W4 集成前真机 `activated=1`；阻塞点为陈旧静态 `WL_BLOCKED["TLB-AliasPerm"]` + 缺 campaign 入口 pilot | 见 §4；解锁需先跑集成后真机 pilot（**本轮已发起 T01-F0-W4**） |
| FS-MULTICORE | 35 | **混合**：O04–O09 W7 共 15 项钩子已落地且**已编译**（`strings` 证实），仅缺 pilot；C08×4 = classic `Param.Cache` vs Ruby 控制器的构造性互斥；W13×6 = PARSEC 源码/输入/aarch64 构建在仓库内**不存在**（真外部） | §4 |
| MODE-UNIMPL | 3 | T08-a/b/c/d **均已实现并编译**，仅缺真机 FS pilot | `CHAOSArmTLB.cc` 中 `walk_fill_dup`/`walk_done_early`/`walk_stale_result` |
| UNRESOLVED | 4 | S10-F2-W5/W9 = **规格结构性拒绝**（F2 首抽下界 50000 ≫ 实测流 3/4，改 interval 即改故障模型语义）；S01/S02-F0-W1 = **待 census 收敛** | `chaos_lsu_trigger.hh` F2 `intervalEvents=100000` + `next_fire = from + iv/2 + rng%iv` |

**未做**：把任何一项通过改分类/放宽阈值/移出分母的方式"制造"为 READY（`verdict()` 与
负向契约测试 `test_lsu_ready_contract_verdict.py` 钉死此禁令）。

## 7. 正式启动命令（机器校验，GO 前禁止执行）

`ready_contract.json` 每条 READY 行给出精确命令，由
`tests/test_lsu_ready_contract_verdict.py` 机器校验：**不得含 `--phase trial`**、
**不得含 `--max-seeds-per-cell 3`**、全部 `--phase screening`、21 个重点 RunID 用
`--screening-target 2401`、其余 `--screening-target 385`。全量入口：

```bash
LSU_GEM5_BIN=$PWD/CHAOS/gem5/build/ARM/gem5.opt \
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir runs/lsu/formal_325 \
  --phase screening --screening-target 385 --max-seeds-per-cell 100000 \
  --max-parallel 1
```

## 8. 尚待完成（下一步）

- [ ] T01-F0-W4 集成后真机 FS pilot 结果 → 据此决定是否解除 FS-INFRA 静态阻塞（**不得**在无 pilot 证据前解除）。
- [ ] S01/S02-F0-W1：census 收敛后写 `LSQFWD_F0_SPAN` 并契约钉死。
- [ ] FS-INFRA 阻塞理由措辞更正（旧措辞已被证据反驳）。
- [ ] 集成报告 "616 事件" → 810 更正。
- [ ] O04–O09 W7 15 项的 campaign 入口 pilot。

---

## 9. 本轮终局快照（2026-10-22 21:30）

- **HEAD**：`0665b051`（`origin/lsu-mdspec-20261019` 同步，工作树干净）
- **权威准入**：`total=325 READY=241 PARTIAL=0 BLOCKED=84 self_consistent=True`；
  `verdict = NO-GO`（`verdict()` 自动判定，非人工声明）
- **325 机器核对**：四源集合对称差全 0；源 xlsx sha256 `389546f0…` 与文档头一致
- **全套件**：`lsu_test_runner` → `PASS=50 SKIP=1 FAIL=0 ENV=0`；`pytest` 21 passed
- **二进制**：sha256 `f4dbfb9a66e0df80…`（1,145,188,760 B）

### 仍在运行的真实任务（不杀、不干预）

| 任务 | 状态 |
|---|---|
| S01-F0-W1 span census | 运行中（21:06 后进入输出静默段，CPU 持续 99.8%，判定为推进中） |
| T01-F0-W4 FS pilot | 运行中 |
| FS-INFRA 逐格 pilot 批（22 格，2 并发） | 本轮发起，证据落 `/tmp/r5_fs_pilot/batch/` |

### 结论（不夸大）

达到正式实验标准所需的是 **BLOCKED→0**，本轮**未达到**，也**未**通过任何改分类/放宽阈值手段接近它。
84 项中：**真外部 47**（LICENSE 12 + W13 PARSEC 6 + C08 构造性互斥 4 + A06 规格裁决 6 +
S10-F2 规格结构性拒绝 2 + FS-MULTICORE 其余外部项）+ **可跑但未逐格 pilot ~33**
（FS-INFRA 24 + O04–O09 W7 15 中的未 pilot 部分）+ **census 待收敛 2**（S01/S02-F0-W1）。

⇒ 未满足用户条件 2 的"剩余项全部不可达"分支：约 33 项**可达**，缺的是逐格 pilot
（每格 FS pilot 约 30–45 min，33 格 × 2 并发 ≈ 8–12 h），本轮已启动该批次但未完成。
**不得**据此宣布 GO，也不得把"批次已启动"当作"已解锁"。
