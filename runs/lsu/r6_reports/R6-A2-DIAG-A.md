# R6-A2 阶段 1 — Lane A 只读诊断报告（频率载体 / 首发射位置 / repeat_factor / A06 hook）

- 日期：2026-10-28
- 工作树：`/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026`
- 分支 / HEAD：`fix/r6-a-unit-20261028` / `defb3e0d`
- 二进制：`CHAOS/gem5/build/ARM/gem5.opt` sha256 `37c9ec36…`（与权威报告一致）
- 约束遵守：本轮**只读**；未修改源码/配置/测试，未 git 写、未运行 gem5/scons/campaign/pytest。唯一写入 = 本文件。
- 上游权威：`R6-A-FINAL-REPORT.md`、`R6-A-STATUS.{md,json}`、`R6-A-SPAN-CENSUS.md`、`R6-A-DIAG-A.md`。本报告**不重做**其结论，只补 A2 所需的频率载体、首火位置、repeat 与 A06 hook 四块。

---

## 0. 结论先行（事实 + 数字）

1. **A 单元共有 5 种 workload**：`W0=mini_check`、`W3=agu_addrmodes`、`W5=sq_forward`、`W9=gap_bfs`、`W10=stream_chase`（`docs/gem5-fi/lsu/mdspec/runid_map.json`，39 条 A 记录逐条核对）。
2. **eligible_per_iteration 是强确定性的**：同一 cell 三个 seed 的 `attempted=eligible` 完全一致（实测 run.out）。A 族 addrpath 的 eligible 流 = 全部"普通 load/store"（非 atomic、非 prefetch），与 seed 无关；seed 只影响 F0/F1/F2/F4 的**抽签位置**，不改变流长。
3. **首发射位置是"eligible 计数空间"的阈值，不是 tick**。F1/F2/F4 的 `next_fire = warmup + iv/2 + lcg(seed)%iv`（`chaos_lsu_trigger.hh:221-225`）；A 族 F1-F4 用 `warmup_events=0`（`lsu_campaign.py:1143-1145`），故 `next_fire = iv/2 + lcg(seed)%iv`，仅取决于 tier+seed，**与 model/workload 无关**。日志**不打印** F1/F2/F4 的 `next_fire`（只有 F0 的 SPAN_UNREACHABLE 告警才印 `draw_next_fire`），故首次发射位置只能由**精确 seeded LCG 推导**（非估算），推导值：
   - **F1（iv=1e6）**：seed1/2/3 = 1,256,412 / 1,049,417 / **1,290,806** → `max_first_fire_position=1,290,806`
   - **F2（iv=1e5）**：106,412 / 99,417 / **140,806** → `max=140,806`
   - **F4（iv=1e5，burst period 同 F2）**：同 F2 → `max=140,806`
4. **repeat_factor**（`ceil(1.2·max_first_fire_position / eligible_per_iteration)`）关键值见 §4：
   - F2/F4 系全部落在 **53–66**（可行）；
   - **A01-F1-W3 = 558**（agu_addrmodes 太短，F1 间隔太大 → 实际不可行）；
   - **A01-F1-W9 = 6**（gap_bfs 长，可行）；
   - **A06-F2-W3 ≈ 101**（用 A06 实测 eligible=1677）；**A06-F2-W5 = UNKNOWN**（缺 A06×sq_forward census）。
5. **A06-a/A06-b 的最小安全 hook 就在现有 `LSQ::pushRequest` 入口**（`lsq.cc:800`，Request 构造**之前**）。`maybeCorruptPre` 改的是 **Request 构造前**的 by-value `size` 与可变 `byte_enable`，这是唯一安全层；**Request/Packet 构造之后改 size 不安全**（`packet_access.hh:55 assert(sizeof(T) <= size)` 会让定宽 load completion 直接 abort）。**A06-a（缩小 original/2）只对 store 安全，load 必须 ineligible**；**A06-b（同宽 byte mask）只对 store 安全**；`size=1` 无合法变换 → ineligible、不消费预算。
6. **最大风险**：`agu_addrmodes / mini_check / sq_forward` 是**单趟自终止探针、无外层迭代循环**（`workloads/directed/agu_addrmodes.c`），repeat 必须**改写 workload 加外层循环**，会改变 golden/负载身份与首迭代 cache 状态；这不是"重跑同一进程"能得到的。此点决定 repeat 方案能否成立，见 §5/§6。

---

## 1. 39 格 RunID → model → workload → tier 映射

`tier` 列即 freq（F 列）。workload 码（W 码）到二进制的映射：W0=mini_check、W3=agu_addrmodes、W5=sq_forward、W9=gap_bfs、W10=stream_chase。来源逐条：`docs/gem5-fi/lsu/mdspec/runid_map.json`（entries[*].run_id / model_id / freq / workload.binary）。

| RunID | model | tier | workload(binary) |
|---|---|---|---|
| A01-F0-W3 | A01 | F0 | agu_addrmodes |
| A01-F0-W9 | A01 | F0 | gap_bfs |
| A01-F1-W3 | A01 | F1 | agu_addrmodes |
| A01-F1-W9 | A01 | F1 | gap_bfs |
| A01-F2-W3 | A01 | F2 | agu_addrmodes |
| A01-F2-W9 | A01 | F2 | gap_bfs |
| A02-F0-W3 | A02 | F0 | agu_addrmodes |
| A02-F0-W9 | A02 | F0 | gap_bfs |
| A02-F2-W3 | A02 | F2 | agu_addrmodes |
| A02-F2-W9 | A02 | F2 | gap_bfs |
| A03-F5-W3 | A03 | F5 | agu_addrmodes |
| A03-F5-W10 | A03 | F5 | stream_chase |
| A04-F0-W3 | A04 | F0 | agu_addrmodes |
| A04-F0-W0 | A04 | F0 | mini_check |
| A04-F2-W3 | A04 | F2 | agu_addrmodes |
| A04-F2-W0 | A04 | F2 | mini_check |
| A04-F6-W3 | A04 | F6 | agu_addrmodes |
| A04-F6-W0 | A04 | F6 | mini_check |
| A05-F0-W3 | A05 | F0 | agu_addrmodes |
| A05-F2-W3 | A05 | F2 | agu_addrmodes |
| A05-F6-W3 | A05 | F6 | agu_addrmodes |
| A06-F0-W3 | A06 | F0 | agu_addrmodes |
| A06-F0-W5 | A06 | F0 | sq_forward |
| A06-F2-W3 | A06 | F2 | agu_addrmodes |
| A06-F2-W5 | A06 | F2 | sq_forward |
| A06-F6-W3 | A06 | F6 | agu_addrmodes |
| A06-F6-W5 | A06 | F6 | sq_forward |
| A07-F0-W3 | A07 | F0 | agu_addrmodes |
| A07-F0-W5 | A07 | F0 | sq_forward |
| A07-F4-W3 | A07 | F4 | agu_addrmodes |
| A07-F4-W5 | A07 | F4 | sq_forward |
| A07-F6-W3 | A07 | F6 | agu_addrmodes |
| A07-F6-W5 | A07 | F6 | sq_forward |
| A08-F0-W3 | A08 | F0 | agu_addrmodes |
| A08-F0-W5 | A08 | F0 | sq_forward |
| A08-F2-W3 | A08 | F2 | agu_addrmodes |
| A08-F2-W5 | A08 | F2 | sq_forward |
| A08-F6-W3 | A08 | F6 | agu_addrmodes |
| A08-F6-W5 | A08 | F6 | sq_forward |

计数核对：39 条；agu_addrmodes×21、sq_forward×9、gap_bfs×5、mini_check×3、stream_chase×1。

---

## 2. eligible_per_iteration（每个 model × workload）

### 2.1 口径说明（诚实标注）

- 这里的 "iteration" = 该 workload **执行一次完整探针**（gem5 SE 一次运行）。**不是** workload 内部某个 for-loop 的一圈——这些定向探针根本没有"整趟外层迭代"。
- 优先复用 `R6-A-SPAN-CENSUS.md` 的 F0 census（tier=F0, warmup=1, span=1e6 不落地，读 teardown `eligible=`）。对同一 cell 用其 **F1/F2/F4 实跑 run.out 的 `eligible=`** 复核（同一流，确定性），两者一致或给出差异。
- `A07` 的 census 目录 `runs/lsu/r6_a_census/A07_*` **为空**（无 run.out），其 2795/2579 是 census 表标注的 "pre-existing R4-5.8"（来自 `lsu_campaign.py:1094-1096` 的表）；但 A07-F4 实跑 run.out 实测 agu=2800、sq_forward=2582，与同族一致。**A2 用实跑值**。

### 2.2 表（单位：eligible events / 单次运行）

| model | workload | eligible/run | 来源 | 备注 |
|---|---|---|---|---|
| A01 | agu_addrmodes | **2777** | census + A01-F1/F2-W3 实跑 | attempted=eligible |
| A01 | gap_bfs | **265019** | census + A01-F1-W9 实跑 | 长流 |
| A02 | agu_addrmodes | **2777** | census + A02-F2-W3 实跑 | |
| A02 | gap_bfs | **265019** | census（+ A02-F2-W9 合格样本） | |
| A04 | agu_addrmodes | **2800** | census + A04-F2-W3 实跑 | |
| A04 | mini_check | **3207** | census + A04-F2-W0 实跑 | |
| A05 | agu_addrmodes | **2800** | census + A05-F2-W3 实跑 | |
| A07 | agu_addrmodes | **2800** | A07-F4-W3 实跑（3 seed 一致） | census 目录空；span 表旧值 2795 已过时 |
| A07 | sq_forward | **2582** | A07-F4-W5 实跑 | span 表旧值 2579 |
| A08 | agu_addrmodes | **2800** | census + A08-F2-W3 实跑 | |
| A08 | sq_forward | **2582** | census + A08-F2-W5 实跑 | 追加 census 2582 |
| **A06** | agu_addrmodes | **≈1677（A06-a 口径）** | `round4_findings.md:1979` `attempted=2800 eligible=1677`；DIAG-B 另记 1637 | **不是裸 addrpath 流**：A06-a 在 trigger 前过滤掉不可变换 load，故 1677<2800。属 A06 专属流，需 A2 重测确认 |
| **A06** | sq_forward | **UNKNOWN** | — | 无 A06×sq_forward census/实跑。缺：`--agu_pre_mode a06_size` 的 F0 census（tier=F0 span 未实测，`lsu_campaign.py:1038` EARLY_BIAS） |
| A03 | agu_addrmodes | 2777（addrpath 裸流） | census/A03-F5 实跑 | F5 恒真，无间隔，不受本表影响 |
| A03 | stream_chase | UNKNOWN | — | W10 的 addrpath eligible 未 census（A03-F5 用 F5=永久，不需要间隔） |

**要点**：A06 的 eligible 与 A01/A02/A04/A05/A08 的裸流**不同**（A06 在 `onAttempt` 前先算 `a06LoadSize` 并拒斥不可变换 load，`CHAOSAddrPath.cc:498-593`）。因此 **A06 不能直接借用兄弟 model 的 2800/2582**；1677 仅对 agu_addrmodes 的 A06-a 口径有效，且来源是旧轮（round4），本轮未复测。

---

## 3. 每个 RunID/seed 的实际首发射位置

### 3.1 首发射位置的语义与换算依据

- F1/F2/F4 触发在**eligible 计数**空间工作（`chaos_lsu_trigger.hh:277-295`）：`onEligible()` 每来一个 eligible event `++eligible`；当 `eligible >= next_fire` 才发火。
- `next_fire` 首次由 `scheduleNext(warmup_events)` 算出（`:221-225`）：`rng=lcg(rng); next_fire = warmup + iv/2 + rng%iv`；构造时 `rng = seed?seed:1`（`:229-231`）。
- A 族 F1-F4 的 campaign flags：`--addrpath_lsu_tier <F> --addrpath_warmup_events 0 --addrpath_span_events 1000`（`lsu_campaign.py:1143-1145`）；`--addrpath_rng_seed <seed>`（`lsu_campaign.py:1576`），seed = 样本 seed（s1=1,s2=2,s3=3，manifest 核对）。
- LCG：`chaosSampleLCG(x)=x*6364136223846793005+1442695040888963407 (mod 2^64)`（`chaos_event_sample.hh:46-49`）。
- 间隔：F1=1e6、F2=1e5、F4=1e5（`chaos_lsu_trigger.hh:209-217`）。
- **tick↔eligible 换算**：日志里有 `first_eligible_tick=80080`（序号 1）与 `last_eligible_tick`，但 eligible 事件在程序各处成簇出现，**序数→tick 非线性、无法反解**；触发本身也**不用 tick**。故本报告只给"序数空间"的首火位置；tick 仅作观测（首 eligible tick=80080；末 eligible tick 见 §3.3）。对 NO_FIRE 格，"本想发火的 tick"根本不存在（从未到达该序数）。

### 3.2 首火位置（tier×seed 常量，推导值，非实测日志）

| tier | iv | seed1 | seed2 | seed3 | max |
|---|---|---|---|---|---|
| F1 | 1,000,000 | 1,256,412 | 1,049,417 | 1,290,806 | **1,290,806** |
| F2 | 100,000 | 106,412 | 99,417 | 140,806 | **140,806** |
| F4 | 100,000 | 106,412 | 99,417 | 140,806 | **140,806** |

> **缺失/推导标注**：F1/F2/F4 的 `next_fire` **未出现在任何 run.out**（summary 只印 attempted/eligible/injected/first_eligible_tick/last_eligible_tick；只有 F0 的 SPAN_UNREACHABLE 才印 draw_next_fire）。上表是**由精确 seeded LCG 推导**（seed、warmup=0、iv 均已从源码+config 确认），属确定性推导而非估算；若 campaign 曾改动 seed 语义或 warmup，需重算。所有 A 族同 tier 同 seed 共用同一抽签（与 model/workload 无关）。

### 3.3 逐 target cell 的实测首 eligible / 末 eligible tick（来自 run.out，3 seed 完全一致）

| RunID | tier | eligible/run | first_eligible_tick | last_eligible_tick | 首火序数(max) | 首火 tick |
|---|---|---|---|---|---|---|
| A01-F1-W3 | F1 | 2777 | 80080 | 19481000 | 1,290,806 | 不存在（NO_FIRE） |
| A01-F1-W9 | F1 | 265019 | 80080 | 320271490 | 1,290,806 | 不存在 |
| A01-F2-W3 | F2 | 2777 | 80080 | 19481000 | 140,806 | 不存在 |
| A02-F2-W3 | F2 | 2777 | 80080 | 19481000 | 140,806 | 不存在 |
| A04-F2-W3 | F2 | 2800 | 80080 | 19481000 | 140,806 | 不存在 |
| A04-F2-W0 | F2 | 3207 | 80080 | 19713540 | 140,806 | 不存在 |
| A05-F2-W3 | F2 | 2800 | 80080 | 19481000 | 140,806 | 不存在 |
| A07-F4-W3 | F4 | 2800 | 80080 | 19481000 | 140,806 | 不存在 |
| A07-F4-W5 | F4 | 2582 | 80080 | 18940845 | 140,806 | 不存在 |
| A08-F2-W3 | F2 | 2800 | 80080 | 19481000 | 140,806 | 不存在 |
| A08-F2-W5 | F2 | 2582 | 80080 | 18940845 | 140,806 | 不存在 |
| A06-F2-W3 | F2 | UNKNOWN（A06 流） | 无 run | 无 run | 140,806（推导） | 无 run |
| A06-F2-W5 | F2 | UNKNOWN | 无 run | 无 run | 140,806（推导） | 无 run |

证据路径示例（每个 seed 目录同形）：
`/home/sdc/gem5-fi-ding/runs/lsu/r6_a_segv2_A01-F1-W3_s{1,2,3}/A01-F1-W3/seed{n}/run.out:16`、
`r6_a_segv2_A07-F4-W3_s1/A07-F4-W3/seed1/run.out:16`、
`r6_a_fix2_A08-F2-W5_s1/A08-F2-W5/seed1/run.out:16`、
`r6_a_segv2_A04-F2-W0_s1/A04-F2-W0/seed1/run.out:16`。

---

## 4. repeat_factor 表

公式：`repeat_factor = ceil(1.2 · max_first_fire_position / eligible_per_iteration)`（1.2 = 20% 余量）。含义：把该 workload 的 eligible 流重复 N 趟，使总 eligible ≥ 1.2×首火阈值。**前提：workload 可加外层循环且 oracle/golden 与流身份可控（见 §6 风险 R1）。**

| RunID | tier | max_first_fire | eligible/run | 1.2×Fmax | repeat_factor | 可行性 |
|---|---|---|---|---|---|---|
| A01-F1-W3 | F1 | 1,290,806 | 2777 | 1,548,967 | **558** | **不可行**（558 趟；见 §4.2） |
| A01-F1-W9 | F1 | 1,290,806 | 265019 | 1,548,967 | **6** | 可行 |
| A01-F2-W3 | F2 | 140,806 | 2777 | 168,967 | **61** | 可行（≤上限） |
| A02-F2-W3 | F2 | 140,806 | 2777 | 168,967 | **61** | 可行 |
| A04-F2-W3 | F2 | 140,806 | 2800 | 168,967 | **61** | 可行 |
| A04-F2-W0 | F2 | 140,806 | 3207 | 168,967 | **53** | 可行 |
| A05-F2-W3 | F2 | 140,806 | 2800 | 168,967 | **61** | 可行 |
| A07-F4-W3 | F4 | 140,806 | 2800 | 168,967 | **61** | 可行 |
| A07-F4-W5 | F4 | 140,806 | 2582 | 168,967 | **66** | 可行（贴上限） |
| A08-F2-W3 | F2 | 140,806 | 2800 | 168,967 | **61** | 可行 |
| A08-F2-W5 | F2 | 140,806 | 2582 | 168,967 | **66** | 可行（贴上限） |
| A06-F2-W3 | F2 | 140,806 | ≈1677 | 168,967 | **≈101** | 可行但需先 census（A06 流） |
| A06-F2-W5 | F2 | 140,806 | **UNKNOWN** | 168,967 | **UNKNOWN** | 缺 A06×sq_forward census；若流≈1677 → ≈101（不可当实测） |

### 4.1 数字依据

- `max_first_fire_position`：§3.2 推导（F1 1,290,806；F2/F4 140,806）。
- `eligible/run`：§2.2（实跑 run.out 与 census 一致；A07 用实跑 2800/2582，不用旧 2795/2579）。
- A06-F2-W3 用 A06 专属实测 1677（`round4_findings.md:1979`），不是裸流 2800。

### 4.2 合理上限建议

**实测墙钟**（manifest start/end，含 gem5 启动/统计落盘；`runs/lsu/r6_a_*/manifest.json`）：

- `agu_addrmodes` / `mini_check` / `sq_forward` 单次 3-seed 每 seed ≈ **2 s**（例：A01-F2-W3_s1 12:52:0x→2 s；A04-F2-W0_s1 2 s）。
- `gap_bfs` 单次 ≈ **7–9 s**（A01-F1-W9_s1 8 s）。
- 证据体积：单 seed 目录 ≈ **456 KB**（`stats.txt` 258 KB + `config.json` 122 KB + `config.ini` 42 KB 占绝大部分；`prop_evt/trace` 在 no-fire 且 propagation off 时仅数百字节）。**证据体积主要由固定文件决定，不随 repeat 趟数线性膨胀**（只要 propagation off、不额外打 attr）。

**推导上限**：
- 以"单 cell×3 seed、串行/4 并发硬上限、墙钟 ≤ ~4 min/cell"约束：短探针 2 s×R×3/4 ≤ 240 s ⇒ **R ≤ 160**。
- 语义上限（更紧）：外层重复会带**暖 cache / 分支预测 / StoreSet 等跨趟状态**，且 golden 必须重算；且 sq_forward 的转发/StoreSet 清理周期（250k mem ops，`store_set.cc` checkClear）会跨趟漂移。**建议保守硬上限 R ≤ 72**（覆盖全部 F2/F4 的 53–66 并留余量；A06 的 ≈101 超此上限 → 需单独裁决）。
- **A01-F1-W3（558）在所有合理上限下都不可行**：要么保持 `EXCLUDED_NO_FIRE`（诚实零），要么按规格改换长载体（这属 spec 级裁决，非本轮自决）。

> 若坚持 R≤72：11 个 F2/F4 目标格全部可达（最大 66）；A01-F1-W9（6）可达；A01-F1-W3（558）与 A06-F2-*（≈101/UNKNOWN）不可达。这是"repeat 策略"在本单元的真实边界。

---

## 5. A06-a/A06-b 真实 hook 设计（本轮裁决：a=缩小 original/2；b=同宽另一非零 byte mask）

### 5.1 现有 a06 实现改的是哪一层？（结论）

- 入口：`LSQ::pushRequest` 第一行（`CHAOS/gem5/src/cpu/o3/lsq.cc:772`），调用 `cpu->chaosAddrPathPre->maybeCorruptPre(addr, size, isLoad, flags, inst->seqNum, pre_byte_enable)`（`lsq.cc:800`）。
- 这是 **Request 构造之前**：`addr/size` 是 pushRequest 的 by-value 形参；`pre_byte_enable` 是 `byte_enable` 的可变拷贝（`lsq.cc:792`）。随后才 `new SingleDataRequest/SplitDataRequest(...)`（`lsq.cc:906-912`），并按 `pre_byte_enable` 重建 `request->_byteEnable`（`lsq.cc:924-925`）。
- 因此现有 a06 修改的是 **LSQRequest/Request 构造前的 AGU 输出层**——这正是**最安全**的层。
- **Request 构造之后改 size 不安全**：
  - `Request::_size` 在 `setVirt` 里固定（`request.hh:583-587`），`_byteEnable` 默认 `std::vector<bool>(size,true)`（`request.hh:501/511`）；
  - `Request::setByteEnable` 断言 `be.size()==_size`（`request.hh:716-719`）；`split` 按 `_size` 切片 byte-enable（`request.hh:625-636`）；
  - TLB/TC/缓存分片（`transferNeedsBurst(addr,size,cacheLineSize)`，`lsq.cc:868`）在构造时已按 size 决定 split；
  - **load 定宽完成**：`Packet::get<T>` → `packet_access.hh:55 assert(sizeof(T) <= size)`；shrunk load 的 packet size < 静态宽度 ⇒ **panic/abort**（`CHAOSAddrPath.hh:226-233` 已实测 `sizeof(unsigned long)<=size` failed）。
  - 结论：size/byteEnable 只能在 **Request 构造前**定；构造后改必须同步 packet size、byte-enable、split、TC、TLB 分片与完成宽度——不可做，也不该做。
- **现有 A06-a 是"任意合法目标尺寸"（campaign 钉 `--agu_size_to 2` / `--agu_size_to_load 8`，`lsu_campaign.py:372-373`），不是裁决要求的 original/2**；现有 A06-b 是 `shift_mid`（清中间字节 `(size-1)/2`，`CHAOSAddrPath.cc:802-827`），**不是裁决要求的"循环移位一位 / 全 1 清 MSB"**。所以本轮 A06 需**改语义 + 改合法性口径**，不是从零新建。

### 5.2 最小安全 hook（文件:行 + 函数 + 前后语义）

**Hook 点（不变）**：`LSQ::pushRequest` 入口 → `CHAOSAddrPath::maybeCorruptPre`（`CHAOSAddrPath.cc:462-760`）的 `pre_mode=="a06_size"` 分支（现 `:643-711`）。插入点前：`addr/size` 为 AGU 原始输出、`pre_byte_enable` 为 ISA 生成的（通常全 1）掩码；插入点后：pushRequest 用新 `size` 造 Request，并在 `lsq.cc:924-925` 按 `pre_byte_enable.size()==size` 决定用新掩码或重建全 1。

**A06-a（store，缩小 original/2）**：
```
// 在 a06_size 分支的 store 侧（现 :708 elif isLegalAguSize(agu_size_to)）替换为：
if (!isLoad && size >= 2 && (size/2) is legal AGU size && addr % size == 0) {
    unsigned ns = size / 2;            // 8→4, 4→2, 2→1；16→8
    size = ns;                         // by-value 出参，Request 以 ns 构造
    // byte_enable: 旧长度 != ns ⇒ lsq.cc:924 自动重建 vector<bool>(ns,true)
    // 记录 old_size/new_size（见 §5.3）
} else {
    // size==1 / 非对齐 / 非 store ⇒ ineligible，return size 且 **不计 injected**
}
```
语义：store 只写低半部字节；地址不变 → 不引入未映射页；不破 64B 行（ns≤size 且 addr%size==0 保证不越原区间）。
判定：store 缩小**架构上合法**（少写字节），不触发 load 定宽 assert。

**A06-b（store，同宽 byte mask）**：
```
// 在现 A06-b 掩码段（:793-827）替换 shift_mid：
if (!isLoad && size >= 2 && be_len == size) {
    // 构造"另一合法非零掩码"：优先把原掩码按字节循环移位 1；
    // ISA 常规掩码全 1 ⇒ 循环移位仍全 1 ⇒ 落到"全 1 清最高有效 byte"
    std::vector<bool> m = byte_enable;      // 原掩码
    bool all_true = all(m);
    if (all_true) { m[size-1] = false; }    // 清 MSB 字节；size>=2 ⇒ 非零
    else          { rotate_bytes_left(m,1); } // 一般情形循环移位一位
    if (m 全 0 或 m == 原掩码) { /* ineligible, 不消费预算 */ }
    else { byte_enable = m; }               // 同宽，lsq.cc:924 原样采用
}
```
语义：同 width 的部分 store/load——对 store 是真实部分写（`Packet::isMaskedWrite`/`writeData`，见 `CHAOSAddrPath.cc:815-817` 注释），不改 Request size；对 load 的 byte-enable 无架构消费者，故 **load 对 A06-b ineligible**。
size=1：A06-a 无 size/2（0.5 非合法）；A06-b 循环移位=恒等、全 1 清 MSB=全 0（非法）⇒ **size=1 两种子模型都 ineligible，不消费预算**。

**为什么这是"最小"**：只在既有 `maybeCorruptPre` 的 a06 分支内改数值语义与合法性判定；不动 Request 构造、不动 lsq_unit 缓冲、不动 TLB/缓存/TC。store 路径本来就不经过定宽 load 完成，故无需 `chaosA06BufBytes` 之类补丁；也**不应**再为 load shrink 造补丁（裁决把 shrink 限定为合法 store 缩小即可）。

### 5.3 需要记录的字段（每发火一行，abort-survivable 双轨）

现存日志段在 `CHAOSAddrPath.cc:828-900`（`write_log && log_stream` 分支，含 `old_size/new_size/widen_target` 等）。建议 A06 行固定字段：

| 字段 | 含义 | 现有/新增 |
|---|---|---|
| `Tick` | curTick | 现有 |
| `Site: lsq_pushRequest_PRE` | hook 点 | 现有 |
| `mode=a06_size` / `submodel=a06a|a06b` | 子模型 | 建议新增 submodel |
| `isLoad/isStore` | op class | 现有 |
| `EA` (hex) | 地址 | 建议新增（现有 REJECT 行无 EA） |
| `dyn_inst_seq` | `inst->seqNum` | 建议新增 |
| `request_id`/`fault_id`(ptag) | `chaosL0Register` 的 id / propagate ptag | 建议新增（现 registerInjection 在 lsq.cc:810 但未并入本行） |
| `old_size/new_size` | A06-a 尺寸前后 | 现有（A06-b 时 new==old） |
| `old_be/new_be` | A06-b 掩码前后（十六进制位） | 建议新增 |
| `activation` | 激活判据：EA 属于带 oracle 对象且下游真实读/写 | 建议新增 |
| `containment` | 被真实检测/取消的事件：`LSQUnit::tryToForward` 降级/replay（shrink store 破坏 `store_has_upper_limit`，`lsq_unit.cc:1657-1720`）、masked-write 落到 packet（`packet.hh:1320-1336`） | 建议新增（或由 prop_evt 的 addr_form/mem_req 关联） |

`activation` 口径（沿用 F-049）：只有在目标属于带 oracle 的对象、且故障后的 size/mask 被下游真实消费（store 真写入、load 真返回）才计 activated；否则 `Injected-not-activated`。

### 5.4 ineligible 形态（不得消费注入预算）

| 形态 | 理由 | 对 a / b |
|---|---|---|
| size=1 | a: /2 非合法；b: 掩码旋转恒等、清 MSB 归零 | a & b 都 ineligible |
| load（任何） | a: 定宽完成 assert（`packet_access.hh:55`）；b: byte-enable 无 load 架构消费者 | a & b 都 ineligible |
| 非零扩展 load（sign-extending，e.g. LDRSB/LDRSH/LDRSW） | 即使将来放开 load，其完成从故障宽度**符号扩展**，与别的模型混淆、且同样撞定宽 assert | 明确 ineligible（额外安全） |
| 非对齐（addr % orig_size != 0） | shrink/mask 与 ISA 对齐语义/分片交互不干净 | a ineligible；b 建议同规 |
| atomic / 独占（amo_op≠null、LDXR/STXR、`isLLSC`） | 原子性/独占监控与 size/mask 语义冲突 | 一律 ineligible |
| 跨 cache line（`transferNeedsBurst`）/ 向量 >16B | 分片后 size/mask 语义不唯一 | ineligible |
| pre/post-index / LDP-STP 产生的内部宽请求 | 不是独立架构 store/load，语义归属不清 | 建议 ineligible |

### 5.5 需修改文件清单（共享文件只列一个 owner）

| 文件 | 改动 | owner |
|---|---|---|
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc` | a06_size 分支语义（a=缩小/2；b=循环移位/清 MSB）、ineligible 判定、证据行字段 | **A06-A 实现 owner** |
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.hh` | `A06LoadVerdict`→改为 store-only 口径；新增 a06a/a06b 计数与 `old_be/new_be` 记录字段 | 同上 |
| `CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.py` | `be_mode` 取值改为新语义（如 `mask_shift`）；`agu_size_to` 改为"按 original/2"开关 | 同上 |
| `tools/lsu_campaign.py` | A06 路由 flags（`lsu_campaign.py:372-373`）改为新 submodel 选择；BLOCKED 理由更新（`lsu_campaign.py:1033-1041`）；补 A06 census 的 `ADDRPATH_F0_SPAN`/run 路径 | **campaign owner** |
| `workloads/directed/a06_size_be.c` | 增加 store 侧 size∈{2,4,8,16} 与非对齐/atomic canary 覆盖，支撑 a=半宽、b=清 MSB | **workload owner** |
| `CHAOS/gem5/src/cpu/o3/lsq.cc` | 一般**不改**；仅当要补 activation/containment 字段到同一行时，读 `pre_old_size`（已存在 `:821-825`） | 共享文件 → **唯一 owner：A06-A 实现 owner**（与 lsq 相关改动都归此 owner，避免多 owner 冲突） |
| `CHAOS/gem5/src/cpu/o3/lsq_unit.cc` | 一般**不改**（store shrink 不需缓冲下限；`chaosA06BufBytes` 对 store 无用） | 共享文件 → 归 **A06-A 实现 owner**，仅当确需 containment 事件时 |

---

## 6. 风险清单（会让 F1/F2/F4 repeat 失真 / 让 A06 改架构可见语义）

**R1（最高）workload 无外层循环，repeat 需改源码，改身份**：`agu_addrmodes.c`/`mini_check`/`sq_forward` 都是单趟自终止探针（`workloads/directed/agu_addrmodes.c:25-71` 无整趟 for）。"重复 N 趟"只能**改写 workload 加外层 loop**，会改变：(a) golden 校验和（须重算）；(b) 负载身份（W3/W5 载体被改）；(c) 首趟 vs 后趟的 cache/PHT/StoreSet 暖状态不同（后趟 eligible 事件序列可能变，`eligible_per_iteration` 不再恒定）。→ 若不重做 golden+census，repeat 后 PASS/FAIL 与基线不可比。

**R2 repeat 改变"每次运行只注入 1 次"的语义边界**：F0/F1/F2/F4 原语在"单次运行"内抽一次；重复 N 趟后，抽签位置可能落在第 k 趟，导致"注入发生在暖 cache 的第 k 趟"而非冷启动——与其它 cell 的不对称，需在 manifest 明示 repeat 趟数与命中趟。

**R3 propagation/证据膨胀**：repeat 后若开 propagation，`prop_evt`/`prop_trace` 随事件线性膨胀（当前 no-fire 仅数百字节；实测开启可达数 MB 级）。需固定 propagation 策略并在证据预算内。

**R4 seed 抽签不可复现风险**：首火位置依赖 `seed→旗标映射` 与 `warmup=0`。若 A2 改 campaign 的 seed 传递顺序、或把 warmup 从 0 改非 0，`next_fire` 全变，§3/§4 的 repeat_factor 全部作废。需把参数据钉死并加回归测试。

**R5 A06-a load 方向**：裁决 "缩小 original/2" 若被误用到 load，必撞 `packet_access.hh:55 assert(sizeof(T)<=size)` → SIGABRT（`CHAOSAddrPath.hh:230-233` 已测）。必须把 load 硬拦为 ineligible，且**不消费预算**（否则 F2 的 eligible 分母被污染，触发位移）。

**R6 A06-a store 半宽改变转发/一致性可见面**：半宽 store 会令后续同址 load 的 `tryToForward` 覆盖判定从 full 降为 partial→replay/回存（`lsq_unit.cc:1700-1720`），若 store 已 drain 则 load 读到旧上字节（可能 Masked）——这是**期望的故障传播**，但也会让"store 半宽"看起来像"地址错"，需用 `old_size/new_size` 与 EA 区分，避免与 A05/A04 混淆。

**R7 A06-b 掩码语义 must-not-alter request size**：旋转/清 MSB 后**必须保持 `be.size()==size`**（否则 `lsq.cc:924` 会重建全 1，故障被静默丢弃，与现有 `obs_be_declined` 同类）。清 MSB 对 `size=1` 归零 → 必须拦为 ineligible。

**R8 BLOCKED 解除仍需真机证据**：`lsu_campaign.py:370-373/1033-1041` 明确 A06 保持 MODEL_BLOCKED，解除要"真实 gem5 运行 + F0 census"。本轮只读设计，不改 BLOCKED 状态。

**R9 A06 eligible 分母未知**：F2 触发按 eligible 计数；A06 的 eligible 流（1677）≠ 兄弟裸流（2800）。若直接套 2800 计算 repeat/激活率，会系统性低谷/高峰期。A06 必须先做 `--agu_pre_mode a06_size` 的 F0 census。

**R10 A03/W10 的 addrpath eligible 未测**：若未来要把 F1/F2/F4 扩到 W10（stream_chase），当前无 census，repeat_factor 无法算（本报告标 UNKNOWN，不猜）。

---

## 7. 未决问题（需上层裁决或额外测量）

1. **A01-F1-W3（558 趟）**：任何合理上限下不可行。是保持 `EXCLUDED_NO_FIRE`（诚实零），还是按 spec 换长载体？属 spec 级裁决。
2. **A06-F2-W5 eligible**：缺 A06×sq_forward 的 F0 census（`--agu_pre_mode a06_size`）。补齐前 repeat_factor=UNKNOWN。
3. **A06 的 1677 是否本轮可复现**：1677 来自 round4（旧 bin `cd49…`/旧轮），本轮 `37c9ec36` 未复测；A06 解除 BLOCKED 前须用当前 bin 重测。
4. **repeat 上限的最终值**（建议 72）与 golden 重算责任：需 campaign owner + workload owner 共同确认，且要有"重复后 eligible/run 仍≈常量"的实测。
5. **A06-a 非对齐 store 是否放过**：本报告建议 ineligible；若裁决允许，需补分片/跨行实测。
6. **A06-b 一般掩码（非全 1）来源**：ISA 常规 store 掩码恒全 1，"循环移位一位"只在人为构造非全 1 掩码时才有别于"清 MSB"；实际生效分支几乎总是"清 MSB"。需裁决这是否接受为"循环移位"的实现（本报告按"全 1 则清 MSB"落地，并保留一般旋转代码）。

---

## 附：关键证据路径（只读）

- census：`/home/sdc/gem5-fi-ding/runs/lsu/r6_a_census/<model>_<workload>/run.out`（A07_* 目录为空，用 span 表旧值+实跑复核）
- F1/F2/F4 NO_FIRE：`/home/sdc/gem5-fi-ding/runs/lsu/r6_a_segv2_<RunID>_s{1,2,3}/<RunID>/seed{n}/run.out:16`
- A08 W5：`runs/lsu/r6_a_fix2_A08-F2-W5_s{1,2,3}/...`
- manifest/时间：`runs/lsu/r6_a_*/manifest.json`（start_time/end_time/binary_sha256）
- 源码：`CHAOS/gem5/src/cpu/o3/lsq.cc:772-925`、`CHAOS/gem5/src/cpu/o3/CHAOSAddrPath/CHAOSAddrPath.cc:395-900`、`CHAOSAddrPath.hh:226-241`、`chaos_lsu_trigger.hh:209-300`、`chaos_event_sample.hh:46-49`、`request.hh:400/583-636/703-719`、`packet_access.hh:55`、`lsq_unit.cc:1730-1748/1940-1950`、`arch/generic/memhelpers.hh:87`
- 上游测量：`docs/gem5-fi/lsu/mdspec/round4_findings.md:1979`（A06 eligible=1677）、`lsu_campaign.py:1094-1115`（span 表）、`lsu_campaign.py:1128-1145`（A 族 tier flags）
