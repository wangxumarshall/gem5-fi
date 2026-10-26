# LSU R6 — T03-F5-W4 F5/stuck-at 事件爆炸修复 + 安全清理 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消除 F5/stuck-at 注入在 armtlb lookup 路径上的"伪注入"爆炸（T03-F5-W4 seed1 产出 2.77GB 注入日志 / 2.40GB prop_evt），按规范实现"每次运行固定一个 bit + no_effect 只聚合"，并在安全清理 ~27.2GB 冗余证据后，用**同一个新冻结二进制**产出 T01-F1-W4 3/3 + T01-F2-W4 3/3 + T03-F5-W4 3/3 = 9/9 certified & admitted 的完整观测链。

**Architecture:** 三个各自独立的单元，按"一提交一单元"串行推进：
1. **清理**（非代码，产出报告到 `runs/lsu/r6_reports/`）；
2. **C++ 语义修复**（唯一 C++ owner：`CHAOSArmTLB` + `chaos_lsu_trigger.hh` + 新增 header-only 判定模块；TDD 用 gem5 构建之外的独立单测钉住语义）；
3. **分析工具内存治理**（`tools/` 流式读取 + EVENT_CAP）。

修复后**必须重建** gem5（`-j16`），得到新 `binary_sha256`，再以该 SHA 跑完 9 样本。

**Tech Stack:** C++17（gem5 v25.1.0.1 vendored 树）、Python 3（`tools/` + pytest）、bash（batch runner）、gem5 FS（ARM checkpoint 恢复）。

**Spec:**
- `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md:60`（T03-F5-W4 单元格规范，**本次修复的规范依据**）
- `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案.md:149`（F5 频率档规范）
- `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-09-逐RunID传播监控.md:60`（T03-F5-W4 传播监控口径）
- `runs/lsu/r6_reports/R6-EVIDENCE-DEDUP.md`（权威 16/16 清单）
- `docs/superpowers/plans/2026-10-24-lsu-r6-toolfix-panic-count-trigger.md`（上一轮停点裁决）

## Global Constraints

- **正式实验在本计划 Task 17/21/22 之外一律停止。** 除本计划明确列出的 9 个样本，不得启动任何 gem5 / campaign / scons。
- **冻结二进制不得删除、不得覆盖**：`.claude/worktrees/r6-fiding-merge-20261026/CHAOS/gem5/build/ARM/gem5.opt`（SHA `e80528423fec4af35b9e82d0d2672895de214d01bd3974437546558c5faf6959`）。
- **不得删除**任何 `runs/lsu/r6_c9_*`、当前 T01-F1-W4/T01-F2-W4 六条 `runs/lsu/r6_n6_T01-F{1,2}-W4_s{1,2,3}` 证据、`runs/lsu/fs_cpt_boot/`、`runs/lsu/r6_reports/`。
- **不得修改或删除** `runs/lsu/r6_reports/R6-SIX-PROPAGATION-PATHS.md` 与 `.json`；只读引用。
- **不得触碰** `/home/sdc/wangxu`、`/home/sdc/sdc-excite-reproduce`、`/home/sdc/.local`、`/home/sdc/google`、`/home/sdc/sdc-run`、`/home/sdc/gem5-fi-backups` 之外的任何用户目录；`gem5-fi-backups` 仅在 Task 5 的确认条件下处置。
- **禁止 `git add -A`**；一律显式 stage 路径。禁止推送 `main`。
- **EVENT_CAP = 200000**；超限输出 `UNPROVEN`/`OVER_CAP`，**绝不**计为 PASS。
- **0101 上分析并发 ≤ 1**；gem5 并发：T03-F5 严格 1，T01-F1/F2 批次 ≤ 2，全机 ≤ 4。
- **不得用** 删除真实事件、伪造 `chain_end`、放宽 admission、把超限流记为 PASS 的方式控制体积。
- 所有结论必须以**真实命令的真实输出**为准；不写"应该通过"。

## Review Focus

（规范/任务书暗示、但没有任何任务的测试直接覆盖的输入类别，最可能先咬人者在前）

1. **`applyProtection` 还原 pfn 的时序** — `parity_interleaved` 1-bit 检测会把 `entry->pfn` 还原为 `old_pfn`（Corrected）。若"是否 effective"在 `applyProtection` **之前**判定，Correction 事件会被记成 effective 真注入；Task 10 的判定必须在该调用**之后**，并由 Task 9 的独立单测钉住"mask 命中但被保护还原 ⇒ effective=false"。
2. **F5 mask latch 与 `--tlb_fault_mask` 的优先序** — 显式 `fault_mask` 必须胜出且同样被 latch（运行内固定）；Task 9 单测须覆盖"未给 fault_mask ⇒ latch 抽取值且重复调用返回同值"和"给了 fault_mask ⇒ 永不抽取值"。
3. **`fires == injected + no_effect` 不变量的完整性** — F5 的 fire 可能经 4 条出口离开（mask==0 早退、stuck 路径、`pfn_to_mapped_page`、entry-state/attr）。任何一条漏报都会让汇总与 stats/日志对不上；Task 10 必须在**每条** F5 出口上报，Task 11 的合同测试须对真实运行断言 `fires == injected + no_effect`。
4. **多条目共享 TLB entry 的累积污染** — 修复前 `entry->pfn` 被逐次改写会跨 lookup 累积（实测 `0x81d75→…→0x0`）。固定 mask 后 stuck-at-zero 是幂等的，但 Task 10 的回归必须证明"同一条目的第 2 次读出是 no_effect 而非又一次 effective"。
5. **分析工具的超限流处理** — `lsu_r6_golden_control.py` 现以 `fh.read()` 整体载入解压流；Task 15 若只改 `lsu_prop_fields.py` 而漏掉它，超大流仍会 OOM；Task 16 的合成超大流测试须同时覆盖两条路径。

---

## 已确认事实（本计划的事实基础，不重新诊断）

| 项 | 值 | 来源 |
|---|---|---|
| 失败目录 | `runs/lsu/r6_n6_T03-F5-W4_s1/T03-F5-W4/seed1` | 实测 |
| `armtlb_injections.log` | 2,768,458,486 B（2.77GB） | `stat` |
| `prop_evt.txt.gz` | 2,401,477,771 B（2.40GB） | `stat` |
| `run.out` | 1,612,035,897 B（1.61GB） | `stat` |
| `prop_trace.csv.gz` | 590,774,909 B（591MB） | `stat` |
| `stats.txt` | 0 B；无 `.done` / manifest / cell_results | 实测 |
| 档位 | stdout `CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1` | `run.out` |
| 爆炸机制 | 每次 lookup 重抽 `Mask:`（`0x400000000000`→`0x800000000000000`→`0x1`…），`old_pfn==new_pfn` 仍建 ptag/写日志/发事件；pfn 被累积摧毁到 `0x0` | 注入日志 head/tail |
| 触发器根因 | `chaos_lsu_trigger.hh:243` F5 分支发射即 `++injected`（无 no_effect 概念） | 源码 |
| 注入器根因 | `CHAOSArmTLB.cc:659-718` 每次 fire 重抽 mask；`:692` 无条件 `numFaultsInjected++`；无 `old_pfn==new_pfn` 判定 | 源码 |
| 规范要求 | 「warm-up 后**固定一个物理 bit**」「对每次 TLB 读出施加**同一掩码**」「**若某次事件的正确值本来就等于卡死值，该次不增加 activated**」 | `07-展开执行矩阵.md:60` |
| F5 档规范 | 「warm-up 后第一个 eligible event 起持续到运行结束；**每次运行仅选一个 bit/字段**」 | `方案.md:149` |
| 权威 16/16 | 全部在 `runs/lsu/r6_c9_*`；`r6_w1*`/`r6_w1b*` 被该文件标为 excluded duplicate | `R6-EVIDENCE-DEDUP.md` |
| 六个旧巨流目录大小 | 4.5+4.5+4.4+2.3+2.2+2.2 = **20.1GB**（GB 流合计 ≈19.9GB） | `du -sh` |
| 当前冻结二进制 | `r6-fiding-merge-20261026/CHAOS/gem5/build/ARM/gem5.opt`，SHA `e8052842…6959`，source head `f77bb0ab` | `runs/lsu/r6_n6_bin_identity.txt` |
| origin/fi-ding | `039fb2b7` | `git fetch` |
| 本计划分支/worktree | `fix/r6-f5-noeffect-20261026` @ `.claude/worktrees/r6-f5-noeffect-20261026` | 已建，C++ 与冻结树逐字节相同 |

---

## 文件结构（本计划新增/修改）

| 文件 | 责任 |
|---|---|
| `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/chaos_tlb_stuck.hh`（新建） | **纯判定**：mask latch + stuck 施加 + effective 判定。无依赖，供 `.cc` 与独立单测共享 |
| `tests/chaos_tlb_stuck_test.cc`（新建） | 独立单测（gem5 构建之外）钉住上述判定 |
| `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh`（改） | F5 fire/outcome 分离计数 + `noteOutcome` + 汇总/告警 |
| `tests/chaos_lsu_trigger_test.cc`（改） | 扩展钉住 F5 fire≠injected、no_effect 汇总 |
| `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh`（改） | 新增 latch/聚合计数器成员 + 聚合摘要声明 |
| `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc`（改） | mask latch；effective 判定后置；no_effect 抑制；聚合摘要；（如适用）`applyEntryFieldFault` 返回 `bool` |
| `tools/lsu_prop_fields.py`（改） | 流式读取 + EVENT_CAP |
| `tools/lsu_r6_golden_control.py`（改） | 去掉整体 `fh.read()` |
| `tests/test_lsu_prop_stream_cap.py`（新建） | EVENT_CAP 语义 + 合成超大流峰值内存有界 |
| `tests/test_lsu_armtlb_f5_noeffect.py`（新建） | 合同测试：解析 stdout 断言 `fires == injected + no_effect` 与四方一致 |
| `runs/lsu/r6_reports/R6-CLEANUP-20261026.md` / `.json` | 清理台账（绝对路径/字节/mtime/SHA-256/理由/引用关系/删除时间/df） |
| `<每个被保留的旧目录>/RAW_STREAMS_REMOVED.md` | 该目录被删巨流的说明 + 原 SHA + 权威替代 |

**Interfaces（跨任务契约，必须在实现前锁定）**

- `gem5::chaos_tlb::applyStuckMask(uint64_t mask, uint64_t old_pfn, StuckKind kind) -> StuckOutcome{uint64_t new_pfn; bool effective;}`
- `gem5::chaos_tlb::latchStuckMask(uint64_t user_mask, uint64_t &latched, uint64_t draw) -> uint64_t`
- `gem5::ChaOSLsuTrigger::noteOutcome(bool effective) -> void`（F5 专用：`injected` 只在 effective 时自增）
- stdout 新行：`CHAOS_LSU_NOEFFECT: injector=CHAOSArmTLB tier=F5 requested=F5 effective=F5 attempted=… eligible=… fires=… effective_injected=… no_effect=… first_no_effect_tick=… last_no_effect_tick=…`

---

## Phase A — 安全清理（非代码；3 个提交量的**报告产物**，均落在未跟踪的 `runs/`）

### Task 1: 清理前安全闸与台账骨架

**Files:**
- Create: `runs/lsu/r6_reports/R6-CLEANUP-20261026.json`
- Create: `runs/lsu/r6_reports/R6-CLEANUP-20261026.md`

**Interfaces:**
- Produces: 两个台账文件；后续 Task 2–5 逐条追加记录。

- [ ] **Step 1: 确认零实验进程**

```bash
ps -eo pid,comm,args | grep -E 'gem5|scons|lsu_campaign' | grep -v grep; echo "rc=$?"
```
Expected: 无输出（rc=1）。若有输出 → 停止并汇报。

- [ ] **Step 2: 记录清理前基线**

```bash
df -B1 /home | tail -1
du -sb /home/sdc/gem5-fi-ding/runs/lsu
```
把两值写入台账 JSON 的 `pre` 字段（`df_home_bytes_used`、`runs_lsu_bytes`）。

- [ ] **Step 3: 建立台账骨架**

`R6-CLEANUP-20261026.json` 初始内容：

```json
{
  "date": "2026-10-26",
  "pre": {"df_home_bytes_used": 0, "runs_lsu_bytes": 0},
  "post": {"df_home_bytes_used": 0, "runs_lsu_bytes": 0},
  "ops": []
}
```

`ops` 每一项的 schema（Task 2–5 填充）：

```json
{
  "path": "/abs/path",
  "kind": "dir|giant-stream",
  "bytes": 123,
  "mtime": "2026-10-26T15:09:22+08:00",
  "sha256": "…|n/a-for-dirs",
  "reason": "…",
  "referenced_by": ["R6-EVIDENCE-DEDUP.md? no", "R6-SIX-PROPAGATION-PATHS.json? yes(input_streams)", "status_table? no", "ready_contract? no"],
  "deleted_at": "2026-10-26T…+08:00"
}
```

- [ ] **Step 4: Commit（仅台账骨架，不进 git）**

`runs/` 未被跟踪，无需 commit。跳过。

### Task 2: 失败目录诊断包 + 删除

**Files:**
- Create: `runs/lsu/r6_reports/r6_n6_T03-F5-W4_s1_DIAG/`（小型诊断包）
- Delete: `runs/lsu/r6_n6_T03-F5-W4_s1/`（整个）

**Interfaces:**
- Produces: 诊断包（含所有大文件 SHA-256）；台账 `ops[]` 追加一条 dir 记录。

- [ ] **Step 1: 建诊断包目录并采集小文件**

```bash
S=/home/sdc/gem5-fi-ding/runs/lsu/r6_n6_T03-F5-W4_s1/T03-F5-W4/seed1
D=/home/sdc/gem5-fi-ding/runs/lsu/r6_reports/r6_n6_T03-F5-W4_s1_DIAG
mkdir -p "$D"
cp "$S/config.ini" "$S/config.json" "$S/run.err" "$S/citations.bib" "$D/" 2>/dev/null
```
**不得** `cp` 四个巨型文件。

- [ ] **Step 2: 记录四个巨型文件的 size/mtime/SHA-256（SHA 在后台算，需数分钟）**

```bash
for f in armtlb_injections.log prop_evt.txt.gz run.out prop_trace.csv.gz; do
  stat -c '%n %s %y' "$S/$f"
  sha256sum "$S/$f"
done | tee "$D/giant_files.sha256"
```
Expected: 四行 size/mtime + 四个 SHA-256。**必须真实跑完并保存输出。**

- [ ] **Step 3: 采集首尾各 100 行与 no_effect 样例**

```bash
head -100 "$S/armtlb_injections.log" > "$D/armtlb_injections.head100"
tail -100 "$S/armtlb_injections.log" > "$D/armtlb_injections.tail100"
head -100 "$S/run.out"                  > "$D/run.out.head100"
tail -100 "$S/run.out"                  > "$D/run.out.tail100"
# old_pfn == new_pfn 样例（从首 200 万行内取样，避免全扫 2.77GB）
head -2000000 "$S/armtlb_injections.log" \
  | awk -F'old_pfn: |, new_pfn: ' '/arm_tlb_lookup_hit/ {split($2,a," "); split($3,b," "); if (a[1]==b[1]) print}' \
  | head -20 > "$D/oldpfn_eq_newpfn.samples"
```
Expected: `oldpfn_eq_newpfn.samples` 非空（首行即 `old_pfn: 0x81d75, new_pfn: 0x81d75`）。

- [ ] **Step 4: 记录最后 ptag/tick 与二进本身份**

```bash
grep -o 'ptag=[0-9]*' "$S/run.out" | tail -1          | tee "$D/last_ptag.txt"
grep -o 'tick=[0-9]*' "$S/run.out" | tail -1          | tee "$D/last_tick.txt"
git -C /home/sdc/gem5-fi-ding/.claude/worktrees/r6-fiding-merge-20261026 rev-parse HEAD | tee "$D/source_head.txt"
sha256sum /home/sdc/gem5-fi-ding/.claude/worktrees/r6-fiding-merge-20261026/CHAOS/gem5/build/ARM/gem5.opt | tee "$D/binary.sha256"
```

- [ ] **Step 5: 写退役标记**

`$D/INTERRUPTED.md` 内容：

```markdown
# T03-F5-W4 seed1 — INTERRUPTED，非权威，不可认证

- stats.txt = 0 B；无 .done / manifest.json / cell_results.json。
- 该目录**不是** R6-EVIDENCE-DEDUP.md 的 authoritative dir（16/16 权威副本全在 r6_c9_*）。
- 终止原因：F5/stuck-at 伪注入爆炸 —— 每次 lookup 重抽 mask、old_pfn==new_pfn 仍建 ptag/写日志/发事件。
- 本目录已被删除；本诊断包保留全部小文件、四个巨流的 size/mtime/SHA-256、首尾 100 行与 no_effect 样例。
- 删除时间：<由 Task 2 Step 7 回填>
```

- [ ] **Step 6: 台账记录**

把 `runs/lsu/r6_n6_T03-F5-W4_s1` 作为一条 `kind=dir` 记录写入 `R6-CLEANUP-20261026.json` 的 `ops[]`，`referenced_by` 四项逐条实测（下面 Step 8 的 grep）。`bytes` 用 `du -sb`。

- [ ] **Step 7: 删除并回填时间**

```bash
du -sb /home/sdc/gem5-fi-ding/runs/lsu/r6_n6_T03-F5-W4_s1
rm -rf /home/sdc/gem5-fi-ding/runs/lsu/r6_n6_T03-F5-W4_s1
test -e /home/sdc/gem5-fi-ding/runs/lsu/r6_n6_T03-F5-W4_s1 && echo "STILL PRESENT (FAIL)" || echo "REMOVED"
```
回填 `deleted_at` 与 `INTERRUPTED.md` 的删除时间。

- [ ] **Step 8: 记录引用关系（对每个待删路径逐条实测）**

```bash
cd /home/sdc/gem5-fi-ding
for p in r6_n6_T03-F5-W4_s1; do
  echo "== $p"
  grep -c "$p" docs/gem5-fi/lsu/mdspec/R6-EVIDENCE-DEDUP.md runs/lsu/r6_reports/R6-SIX-PROPAGATION-PATHS.md runs/lsu/r6_reports/R6-SIX-PROPAGATION-PATHS.json runs/lsu/r6_reports/STATUS.md 2>/dev/null
done
```

### Task 3: 六个旧巨流目录 — 只删巨流、留小文件

**Files:**
- Modify: `runs/lsu/r6_reports/R6-CLEANUP-20261026.{md,json}`
- Create: `<dir>/RAW_STREAMS_REMOVED.md`（每个目录一份）
- Delete: 每个目录下 `prop_evt.txt.gz` 与 `prop_trace.csv.gz` **仅当文件存在于 `seed*/` 且 >100MB**

**Interfaces:**
- Consumes: Task 1 台账骨架。
- Produces: 12 条 `kind=giant-stream` 记录。

- [ ] **Step 1: 冻结删除清单（显式路径，禁止通配到仓库根）**

```bash
cd /home/sdc/gem5-fi-ding/runs/lsu
for d in r6_w1_T04-F0-W4 r6_w1_T04-F2-W4 r6_w1_T04-F6-W4 \
         r6_w1b_T04-F0-W4 r6_w1b_T04-F2-W4 r6_w1b_T04-F6-W4; do
  find "$PWD/$d" -type f \( -name 'prop_evt.txt.gz' -o -name 'prop_trace.csv.gz' \) -size +100M
done | sort | tee /tmp/r6_giant_targets.txt
wc -l /tmp/r6_giant_targets.txt
```
Expected: 6 行（每目录仅 `seed2/prop_evt.txt.gz` 与 `seed2/prop_trace.csv.gz` 中的大者；实测每目录 2 个 → 应为 12 行）。**若行数与实测不符，停止并核对**。

- [ ] **Step 2: 逐个记录 path/bytes/mtime/SHA-256（12 个 SHA，约 20GB 读取，后台跑）**

```bash
while read -r f; do
  stat -c '%n %s %y' "$f"
  sha256sum "$f"
done < /tmp/r6_giant_targets.txt | tee /tmp/r6_giant.sha256
```
**必须真实跑完。**

- [ ] **Step 3: 核对六个目录不是权威目录、且 16/16 与 6/6 完好**

```bash
cd /home/sdc/gem5-fi-ding/runs/lsu
# (a) 六个目录不得出现在权威清单
grep -E 'r6_w1[a-z]?_' r6_reports/R6-EVIDENCE-DEDUP.md; echo "authoritative-refs rc=$?  (期望 rc=1，无输出)"
# (b) 权威 16/16 目录仍在
for d in $(grep -oE 'r6_c9_[A-Za-z0-9-]+_s[0-9]' r6_reports/R6-EVIDENCE-DEDUP.md | sort -u); do
  test -d "$d" || echo "MISSING AUTHORITATIVE: $d"; done; echo "16/16 检查完成"
# (c) 当前 6 条 T01-F1/F2 证据仍在
for d in r6_n6_T01-F1-W4_s{1,2,3} r6_n6_T01-F2-W4_s{1,2,3}; do
  test -f "$d/$(echo $d | sed 's/^r6_n6_//;s/_s[0-9]$//')/cell_results.json" || echo "MISSING: $d"; done
```
Expected: (a) 无输出；(b)(c) 无 MISSING 行。**任一 MISSING 或 (a) 有输出 → 立即停止，不执行 Step 4。**

- [ ] **Step 4: 每个目录写 `RAW_STREAMS_REMOVED.md`**

模板（逐目录实例化，`<...>` 全部填实测值）：

```markdown
# RAW_STREAMS_REMOVED — <目录名>

- 状态：**非权威旧流（excluded duplicate）**。本目录未被
  `docs/gem5-fi/lsu/mdspec/R6-EVIDENCE-DEDUP.md` 引用为 authoritative dir；
  该文件的权威副本全部位于 `runs/lsu/r6_c9_*`。
- 本目录被 `runs/lsu/r6_reports/R6-SIX-PROPAGATION-PATHS.{md,json}` 以
  `input_streams` 条目引用（该报告**未被修改**，其导出内容保留）。
- 删除日期：2026-10-26
- 已删除文件：
  | 文件 | 字节 | mtime | SHA-256 |
  |---|---|---|---|
  | <path> | <bytes> | <mtime> | <sha256> |
- **后果（主动放弃）**：本目录的原始 `input_stream` 已不存在，
  上述报告中的 local 复算（按 SHA 重放原始流）**能力被主动放弃**，
  不视为可复现证据。
- **当前权威替代目录**：见 `R6-EVIDENCE-DEDUP.md` 对应 (RunID, seed) 行的
  `runs/lsu/r6_c9_*` 副本。
```

- [ ] **Step 5: 删除巨流**

```bash
while read -r f; do rm -f "$f"; test -e "$f" && echo "FAIL still present: $f" || echo "removed $f"; done < /tmp/r6_giant_targets.txt
```

- [ ] **Step 6: 逐目录确认小文件仍在**

```bash
cd /home/sdc/gem5-fi-ding/runs/lsu
for d in r6_w1_T04-F0-W4 r6_w1_T04-F2-W4 r6_w1_T04-F6-W4 r6_w1b_T04-F0-W4 r6_w1b_T04-F2-W4 r6_w1b_T04-F6-W4; do
  echo "== $d"; du -sh "$d"
  test -f "$d/"*/seed1/config.ini && echo "  seed1 config.ini OK"
  test -f "$d/RAW_STREAMS_REMOVED.md" && echo "  RAW_STREAMS_REMOVED.md OK"
done
```

- [ ] **Step 7: 台账追加 12 条 `kind=giant-stream` 记录**（含 `deleted_at`），并在 md 里写明：

> `R6-SIX-PROPAGATION-PATHS.{md,json}` **未被修改/删除**；其导出内容仍保留；
> 但原始 `input_stream` 的本地复算能力已在本轮**主动放弃**（见各目录 `RAW_STREAMS_REMOVED.md`）。

### Task 4: `/home/sdc/gem5-fi-backups` 盘点与处置

**Files:**
- Modify: `runs/lsu/r6_reports/R6-CLEANUP-20261026.{md,json}`

- [ ] **Step 1: 盘点**

```bash
du -sh /home/sdc/gem5-fi-backups/*
find /home/sdc/gem5-fi-backups -maxdepth 2 -printf '%y %10s %p\n' | sort -k3 | head -60
```
已实测：`excel_backups/` 1.1M、`lsu_analysis_20261010/` 6.6M、`pre-sync-b34a407c-20261010-095856/` 2.7G（含 `fi-ding-b34a407c.bundle` 259MB + `artifacts/` + `dirty_files/`）。

- [ ] **Step 2: 确认无唯一未提交内容（三查）**

```bash
# (a) bundle 内的 head 是否已是 origin 的祖先
git -C /home/sdc/gem5-fi-ding bundle verify /home/sdc/gem5-fi-backups/pre-sync-b34a407c-20261010-095856/fi-ding-b34a407c.bundle 2>&1 | tail -3
git -C /home/sdc/gem5-fi-ding cat-file -t b34a407c 2>&1
git -C /home/sdc/gem5-fi-ding merge-base --is-ancestor b34a407c origin/fi-ding && echo "ANCESTOR-OF-origin/fi-ding" || echo "NOT-ANCESTOR"
# (b) dirty 清单里的文件今天是否已入库（逐条）
head -20 /home/sdc/gem5-fi-backups/pre-sync-b34a407c-20261010-095856/dirty_tracked_files.txt
# (c) 无软链接/运行依赖指向备份目录
ls -la /home/sdc/gem5-fi-ding/gem5-fs 2>/dev/null | head
grep -rl 'gem5-fi-backups' /home/sdc/gem5-fi-ding/configs /home/sdc/gem5-fi-ding/tools 2>/dev/null | head
```

- [ ] **Step 3: 判定与执行**

**仅当** (a) 为 `ANCESTOR-OF-origin/fi-ding` **且** (b) 的 dirty 文件全部可由 git 历史取得 **且** (c) 无引用 → 记录后删除；否则**保留并在 md 中逐项说明无法确认的唯一内容**。

```bash
# 仅在上述三条件全部满足时执行：
find /home/sdc/gem5-fi-backups -type f -printf '%p %s %T+\n' | sort | tee /tmp/r6_backups_manifest.txt
# 删除（若判定为可删）：
rm -rf /home/sdc/gem5-fi-backups
```

- [ ] **Step 4: 台账追加该目录（或"保留 + 原因"）记录。**

### Task 5: worktree 审计（先出候选清单，再执行）

**Files:**
- Modify: `runs/lsu/r6_reports/R6-CLEANUP-20261026.{md,json}`

- [ ] **Step 1: 生成候选清单（只读）**

```bash
cd /home/sdc/gem5-fi-ding
: > /tmp/r6_wt_candidates.txt
for p in .claude/worktrees/*/; do
  w=$(basename "$p")
  case "$w" in
    r6-fiding-merge-20261026|r6-next6-seedfix-20261026|lsu-mdspec-20261019|r6-f5-noeffect-20261026) continue;;
  esac
  h=$(git -C "$p" rev-parse HEAD 2>/dev/null) || continue
  dirty=$(git -C "$p" status --porcelain 2>/dev/null | wc -l)
  git merge-base --is-ancestor "$h" origin/fi-ding 2>/dev/null || { echo "KEEP(non-ancestor) $w $h"; continue; }
  [ "$dirty" -ne 0 ] && { echo "KEEP(dirty) $w $h"; continue; }
  # 冻结二进制不得位于候选 worktree
  [ "$w" = r6-fiding-merge-20261026 ] && { echo "KEEP(frozen-bin) $w"; continue; }
  # 唯一未跟踪证据/构建产物
  untracked=$(git -C "$p" ls-files --others --exclude-standard 2>/dev/null | head -1)
  [ -n "$untracked" ] && { echo "KEEP(untracked) $w"; continue; }
  sz=$(du -sb "$p" 2>/dev/null | cut -f1)
  echo "CANDIDATE $w $h ${sz}B" >> /tmp/r6_wt_candidates.txt
done
cat /tmp/r6_wt_candidates.txt
awk '{s+=$3} END {printf "预计释放: %.1f GB\n", s/1e9}' /tmp/r6_wt_candidates.txt
```

- [ ] **Step 2: 把候选清单写入 md（**执行前必须先给你看**）**

在 `R6-CLEANUP-20261026.md` 写一节 `## worktree 候选清单（执行前）`，列出每个候选的路径、HEAD、占用字节与预计释放量，并声明 `r6-fiding-merge-20261026` / `r6-next6-seedfix-20261026` / `lsu-mdspec-20261019` / `r6-f5-noeffect-20261026` 一律保留。

- [ ] **Step 3: 执行移除（禁止 `rm -rf` 直接删 worktree 目录）**

```bash
cd /home/sdc/gem5-fi-ding
while read -r _ w h _; do
  git worktree remove --force ".claude/worktrees/$w" && echo "removed $w"
done < /tmp/r6_wt_candidates.txt
git worktree prune
git worktree list | wc -l
```

- [ ] **Step 4: 台账追加 worktree 记录 + 逐个 `git worktree list` 复核。**

### Task 6: 清理后完整性与台账收口

**Files:**
- Modify: `runs/lsu/r6_reports/R6-CLEANUP-20261026.{md,json}`

- [ ] **Step 1: 复核权威 16/16 + 当前 6/6 + 冻结二进制**

```bash
cd /home/sdc/gem5-fi-ding/runs/lsu
n=$(for d in $(grep -oE 'r6_c9_[A-Za-z0-9-]+_s[0-9]' r6_reports/R6-EVIDENCE-DEDUP.md | sort -u); do test -d "$d" && echo ok; done | wc -l)
echo "authoritative dirs present: $n/6"
for d in r6_n6_T01-F1-W4_s{1,2,3} r6_n6_T01-F2-W4_s{1,2,3}; do
  r=$(echo $d | sed 's/^r6_n6_//;s/_s[0-9]$//'); test -f "$d/$r/cell_results.json" && echo "OK $d" || echo "MISSING $d"; done
sha256sum /home/sdc/gem5-fi-ding/.claude/worktrees/r6-fiding-merge-20261026/CHAOS/gem5/build/ARM/gem5.opt
```
Expected: 6/6、6 个 OK、SHA 仍为 `e8052842…6959`。

- [ ] **Step 2: 记录删除后 `df -h /home` 与 `df -B1`**

```bash
df -h /home | tail -1; df -B1 /home | tail -1
du -sb /home/sdc/gem5-fi-ding/runs/lsu
```

- [ ] **Step 3: 写 `post` 与汇总节**

`R6-CLEANUP-20261026.md` 必须含：删除路径清单与释放字节数、`/home` 清理前后对比、权威 16/16 完整性结论、六个旧目录的"旧候选/重复/失败证据"身份、`R6-SIX-PROPAGATION-PATHS` 的引用后果声明。

---

## Phase B — C++ 修复（唯一 C++ owner；TDD）

### Task 7: `chaos_tlb_stuck.hh` — 纯判定模块（先写测试）

**Files:**
- Create: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/chaos_tlb_stuck.hh`
- Test: `tests/chaos_tlb_stuck_test.cc`

**Interfaces:**
- Produces: `chaos_tlb::StuckKind`、`chaos_tlb::StuckOutcome`、`chaos_tlb::applyStuckMask`、`chaos_tlb::latchStuckMask`。

- [ ] **Step 1: 写失败测试**

```cpp
// tests/chaos_tlb_stuck_test.cc
// 独立单测（gem5 构建之外）。构建：
//   g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
//       tests/chaos_tlb_stuck_test.cc -o /tmp/tlb_stuck && /tmp/tlb_stuck
#include <cstdint>
#include <cstdio>
#include "arch/arm/CHAOSArmTLB/chaos_tlb_stuck.hh"

using namespace gem5::chaos_tlb;
static int failures = 0;
#define CHECK(c, m) do { if (!(c)) { printf("FAIL: %s\n", m); ++failures; } } while (0)

int main() {
    // (1) StuckAtZero on a already-0 bit is a no_effect
    CHECK(!applyStuckMask(0x2ull, 0x81d74ull, StuckKind::StuckAtZero).effective,
          "stuck_at_zero on an already-zero bit must be no_effect");
    // (2) StuckAtZero on a set bit is effective and clears it
    { auto o = applyStuckMask(0x1ull, 0x81d75ull, StuckKind::StuckAtZero);
      CHECK(o.effective && o.new_pfn == 0x81d74ull, "stuck_at_zero must clear the bit"); }
    // (3) mask above the PA width leaves the frame unchanged -> no_effect
    CHECK(!applyStuckMask(0x8000000000000000ull, 0x81d75ull,
                          StuckKind::StuckAtZero).effective,
          "mask bit above PA width must be no_effect");
    // (4) StuckAtOne on an already-1 bit is a no_effect (idempotent)
    CHECK(!applyStuckMask(0x1ull, 0x81d75ull, StuckKind::StuckAtOne).effective,
          "stuck_at_one on an already-one bit must be no_effect");
    CHECK(applyStuckMask(0x2ull, 0x81d75ull, StuckKind::StuckAtOne).effective,
          "stuck_at_one on a zero bit must be effective");
    // (5) BitFlip always changes the frame
    CHECK(applyStuckMask(0x1ull, 0x81d74ull, StuckKind::BitFlip).effective,
          "bit_flip on any set bit must be effective");
    // (6) mask == 0 is never effective
    CHECK(!applyStuckMask(0ull, 0x81d75ull, StuckKind::StuckAtZero).effective,
          "mask==0 must be no_effect");
    // (7) latched mask is FIXED for the run (repeated calls return the same)
    { uint64_t latch = 0;
      const uint64_t a = latchStuckMask(0, latch, 0x100ull);
      const uint64_t b = latchStuckMask(0, latch, 0xdeadbeefull);
      CHECK(a == 0x100ull && b == 0x100ull, "latched mask must not be redrawn"); }
    // (8) an explicit user mask wins over the draw and is latched
    { uint64_t latch = 0;
      CHECK(latchStuckMask(0x8ull, latch, 0x100ull) == 0x8ull &&
            latchStuckMask(0, latch, 0x200ull) == 0x8ull,
            "explicit fault_mask must win and be latched"); }
    // (9) same input -> same output (determinism)
    CHECK(applyStuckMask(0x4ull, 0x10ull, StuckKind::BitFlip).new_pfn == 0x14ull,
          "bit_flip must be an exact xor");

    printf(failures ? "chaos_tlb_stuck_test: %d FAILURE(S)\n"
                    : "chaos_tlb_stuck_test: ALL PASS\n", failures);
    return failures ? 1 : 0;
}
```

- [ ] **Step 2: 运行，确认失败（头文件不存在）**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
    tests/chaos_tlb_stuck_test.cc -o /tmp/tlb_stuck
```
Expected: `fatal error: arch/arm/CHAOSArmTLB/chaos_tlb_stuck.hh: No such file or directory`。

- [ ] **Step 3: 写实现**

```cpp
// CHAOS/gem5/src/arch/arm/CHAOSArmTLB/chaos_tlb_stuck.hh
#ifndef __ARCH_ARM_CHAOS_TLB_STUCK_HH__
#define __ARCH_ARM_CHAOS_TLB_STUCK_HH__

// [MDSPEC][R6-F5-NOEFFECT] 永久卡死掩码语义（armtlb LOOKUP 路径，单元格
// T03-F5-W4）。
//
// 规范原文（docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md:60）：
//   "…在 warm-up 后固定一个物理 bit、lane 或控制位置 … 之后每次读出/写入都
//    施加同一掩码直到运行结束。若某次事件的正确值本来就等于卡死值，该次不增加
//    activated。"
// 频率档规范（…方案.md:149）：
//   "warm-up 后第一个 eligible event 起持续到运行结束；每次运行仅选一个 bit/字段"
//
// 本头文件把两条规则编码为无依赖的纯函数，供 CHAOSArmTLB.cc（gem5 构建内）与
// 独立单测（tests/chaos_tlb_stuck_test.cc）共享 —— 与 chaos_tlb_pfn.hh 同一模式，
// 保证"被测的规则就是跑的规则"。

#include <cstdint>

namespace gem5
{
namespace chaos_tlb
{

enum class StuckKind : uint8_t { StuckAtZero, StuckAtOne, BitFlip };

struct StuckOutcome
{
    uint64_t new_pfn = 0;    // 施加掩码后的帧号
    bool effective = false;  // new_pfn != old_pfn ⇒ 真实有效注入
};

inline StuckOutcome
applyStuckMask(uint64_t mask, uint64_t old_pfn, StuckKind kind)
{
    uint64_t np = old_pfn;
    switch (kind) {
      case StuckKind::StuckAtZero: np = old_pfn & ~mask; break;
      case StuckKind::StuckAtOne:  np = old_pfn |  mask; break;
      case StuckKind::BitFlip:     np = old_pfn ^  mask; break;
    }
    return {np, np != old_pfn};
}

// F5 永久卡死：每次运行仅一个掩码（07:60）。latched 是本次运行的固定掩码
// （0 表示尚未抽取）。显式 --tlb_fault_mask 优先于抽取，且同样被 latch ——
// 两条路径下运行内掩码都是固定的。
inline uint64_t
latchStuckMask(uint64_t user_mask, uint64_t &latched, uint64_t draw)
{
    if (latched != 0) return latched;
    latched = user_mask ? user_mask : draw;
    return latched;
}

} // namespace chaos_tlb
} // namespace gem5

#endif // __ARCH_ARM_CHAOS_TLB_STUCK_HH__
```

- [ ] **Step 4: 运行测试，确认全过**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
    tests/chaos_tlb_stuck_test.cc -o /tmp/tlb_stuck && /tmp/tlb_stuck
```
Expected: `chaos_tlb_stuck_test: ALL PASS`，退出码 0。

- [ ] **Step 5: Commit**

```bash
git add CHAOS/gem5/src/arch/arm/CHAOSArmTLB/chaos_tlb_stuck.hh tests/chaos_tlb_stuck_test.cc
git commit -m "[LSU][MDSPEC][R6-F5-NOEFFECT] chaos_tlb_stuck.hh：F5 固定掩码 latch + no_effect 判定（独立单测 9 组全过）"
```

### Task 8: `chaos_lsu_trigger.hh` — F5 fire/outcome 分离

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh:180-282`（计数成员、`onEligible` F5 分支、新增 `noteOutcome`）、`:310-373`（`summary`）
- Test: `tests/chaos_lsu_trigger_test.cc`（追加断言组）

**Interfaces:**
- Consumes: 无（与 Task 7 独立）。
- Produces: `ChaOSLsuTrigger::fires`、`::no_effect`、`::outcomes_recorded`、`::noteOutcome(bool)`、`::require_outcome_accounting`（bool）。

- [ ] **Step 1: 追加失败测试到 `tests/chaos_lsu_trigger_test.cc`（在 `main()` 末尾 `return failures;` 之前插入）**

```cpp
    // ---- [R6-F5-NOEFFECT] F5 的 fire 与 injected 必须分离 ----
    {
        gem5::ChaOSLsuTrigger t(gem5::ChaOSLsuTier::F5, 1, 0, 0);
        t.require_outcome_accounting = true;
        int fired = 0;
        for (int i = 0; i < 10; ++i) if (t.onEligible()) ++fired;
        CHECK(fired == 10, "F5 must fire on every eligible event");
        CHECK(t.injected == 0,
              "F5 must NOT increment injected at fire time (fault not written yet)");
        CHECK(t.fires == 10, "F5 must count every fire attempt");
        for (int i = 0; i < 10; ++i) t.noteOutcome(i < 3);
        CHECK(t.injected == 3, "injected counts only effective fires");
        CHECK(t.no_effect == 7, "no_effect counts the rest");
        CHECK(t.outcomes_recorded == t.fires,
              "fires must equal injected + no_effect after full reporting");
    }
```

- [ ] **Step 2: 运行，确认失败**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
g++ -std=c++17 -I CHAOS/gem5/src tests/chaos_lsu_trigger_test.cc -o /tmp/lsu_trig && /tmp/lsu_trig
```
Expected: 编译失败（`no member named 'require_outcome_accounting'` / `'fires'` / `'noteOutcome'`）。

- [ ] **Step 3: 实现**

在 `chaos_lsu_trigger.hh` 的 funnel 成员（`:180-183`）后追加：

```cpp
    // [R6-F5-NOEFFECT] F5 永久卡死的 fire/outcome 分离计数。
    // F5 在 warm-up 后的每个 eligible event 上都会"发射"（fire），但只有真正
    // 改写注入状态的 fire 才算一次注入。`fires` 计发射机会，`no_effect` 计
    // 未写任何东西的发射，`outcomes_recorded` 让汇总能对"注入器漏报结果"
    // 发出响亮告警（必须 fires == injected + no_effect）。
    uint64_t fires = 0;
    uint64_t no_effect = 0;
    uint64_t outcomes_recorded = 0;
    // 该 tier 是否要求注入器逐次回报结果（仅 F5 路径置 true）
    bool require_outcome_accounting = false;
```

把 F5 分支（`:240-245`）替换为：

```cpp
          case ChaOSLsuTier::F5: {
              if (!armed && eligible > warmup_events) armed = true;
              if (!armed) return false;
              ++fires;        // 发射机会；是否写入了故障由注入器经
              return true;    // noteOutcome() 回报（见下）
          }
```

在 `onEligible()` 之后新增方法：

```cpp
    // [R6-F5-NOEFFECT] 注入器对每一次从 onEligible()/onF6Event() 收到的
    // fire 回报"是否真的写入了故障"。`injected` 因此对**所有** tier 都保持
    // 头文件里声明的语义："fault written"。
    void
    noteOutcome(bool effective)
    {
        ++outcomes_recorded;
        if (effective) ++injected; else ++no_effect;
    }
```

在 `summary()` 的 `printf` 里，把 `injected=%lu` 之后追加（保持既有键顺序不变，只在尾部追加新键）：

```cpp
        printf("CHAOS_LSU_TRIGGER: injector=%s tier=F%d attempted=%lu "
               "eligible=%lu injected=%lu first_eligible_tick=%lu "
               "last_eligible_tick=%lu fires=%lu no_effect=%lu "
               "(activated=W3-L0-layer)\n",
               injector, static_cast<int>(tier),
               (unsigned long)attempted, (unsigned long)eligible,
               (unsigned long)injected,
               (unsigned long)first_eligible_tick,
               (unsigned long)last_eligible_tick,
               (unsigned long)fires, (unsigned long)no_effect);
```

在 `summary()` 末尾（F0 诊断块之后）新增 F5 漏报告警：

```cpp
        // [R6-F5-NOEFFECT] F5 的发射必须 100% 被回报；漏一条即会让汇总与
        // stats / 注入日志三方对不上。响亮点名，绝不静默。
        if (require_outcome_accounting && tier == ChaOSLsuTier::F5
                && outcomes_recorded != fires)
            printf("CHAOS_LSU_TRIGGER_ALARM: injector=%s "
                   "mode=F5_UNREPORTED_OUTCOME fires=%lu "
                   "outcomes_recorded=%lu injected=%lu no_effect=%lu "
                   "(injector did not report every F5 fire's outcome; the "
                   "fire accounting is incomplete)\n",
                   injector, (unsigned long)fires,
                   (unsigned long)outcomes_recorded,
                   (unsigned long)injected, (unsigned long)no_effect);
```

- [ ] **Step 4: 运行测试，确认全过**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
g++ -std=c++17 -I CHAOS/gem5/src tests/chaos_lsu_trigger_test.cc -o /tmp/lsu_trig && /tmp/lsu_trig
```
Expected: 既有断言组全过 + 新增 F5 组全过（无 `FAIL:` 行）。

- [ ] **Step 5: 回归另一独立单测（不得破坏 F0–F4/F6）**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src \
    tests/chaos_armtlb_lookup_ftier_test.cc -o /tmp/tlb_ftier && /tmp/tlb_ftier
g++ -std=c++17 -I CHAOS/gem5/src -I CHAOS/gem5/src/cpu/o3 tests/chaos_trigger_test.cc -o /tmp/ooo_trig && /tmp/ooo_trig
```
Expected: 两者均 ALL PASS。

> 勘误（Task 8 实测发现，2026-10-26）：`tests/chaos_trigger_test.cc` 使用**未限定**的
> `#include "chaos_trigger.hh"`，故**必须**额外 `-I CHAOS/gem5/src/cpu/o3`；仅
> `-I CHAOS/gem5/src` 会报 `chaos_trigger.hh: No such file or directory`。
> 这是该测试的**既有**构建约定，与本次改动无关（`chaos_trigger.hh` 未被修改）。

- [ ] **Step 6: Commit**

```bash
git add CHAOS/gem5/src/cpu/o3/chaos_lsu_trigger.hh tests/chaos_lsu_trigger_test.cc
git commit -m "[LSU][MDSPEC][R6-F5-NOEFFECT] F5 fire/injected 分离 + noteOutcome + 漏报告警"
```

### Task 9: `CHAOSArmTLB` — 固定掩码 + no_effect 抑制

**Files:**
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh:285-305`（成员）、`:330-340`（stats 不变）
- Modify: `CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc:36-123`（构造：F5 时置 `require_outcome_accounting`；注册聚合摘要 exit 回调）、`:659-718`（核心）、`:142-157`（参照 `printLegacyFunnelSummary` 写 `printNoEffectSummary`）

**Interfaces:**
- Consumes: Task 7 的 `chaos_tlb::latchStuckMask/applyStuckMask/StuckKind`；Task 8 的 `ChaOSLsuTrigger::noteOutcome(bool)`。
- Produces: stdout 行 `CHAOS_LSU_NOEFFECT: …`。

- [ ] **Step 1: `.hh` 新增成员（放在 `legacy_last_eligible_tick` 之后，`:299` 附近）**

```cpp
    // [R6-F5-NOEFFECT] F5 固定掩码 latch + lookup 侧 no_effect 聚合。
    // 规范 07:60 要求"warm-up 后固定一个物理 bit"且"每次读出施加同一掩码"，
    // 故掩码在本次运行内只抽一次；"正确值本来就等于卡死值"的那些读出只进
    // 聚合，不建 fault identity、不写日志、不发事件、不计 stats。
    uint64_t f5_stuck_mask = 0;                 // 0 = 尚未抽取
    uint64_t lookup_no_effect = 0;
    uint64_t lookup_effective = 0;
    uint64_t lookup_no_effect_first_tick = 0;
    uint64_t lookup_no_effect_last_tick = 0;
    void printNoEffectSummary() const;
```

- [ ] **Step 2: `.cc` 构造函数 —— F5 时要求逐次回报，并注册聚合摘要**

在 `lookupTier` 创建之后（`:44-46` 之后）加：

```cpp
            // [R6-F5-NOEFFECT] F5 的每次发射都必须被回报（见
            // chaos_lsu_trigger.hh 的 require_outcome_accounting）。
            if (lsuTrigger->tier == ChaOSLsuTier::F5)
                lsuTrigger->require_outcome_accounting = true;
```

并把已有的 exit 回调（`:85-89`）改为在 trigger summary 之后追加聚合摘要：

```cpp
        if (lsuTrigger) {
            registerExitCallback([this]() {
                if (lsuTrigger)
                    lsuTrigger->summary("CHAOSArmTLB");
                printNoEffectSummary();      // [R6-F5-NOEFFECT]
            });
        } else {
```

- [ ] **Step 3: `.cc` 新增 `printNoEffectSummary`（放在 `printLegacyFunnelSummary` 之后，`:158` 附近）**

```cpp
    // [R6-F5-NOEFFECT] lookup 侧 no_effect 聚合摘要（任务书要求的最小字段集：
    // attempted / eligible / effective_injected / no_effect / first_tick /
    // last_tick / requested+effective tier）。只打印聚合，绝不逐事件。
    void
    CHAOSArmTLB::printNoEffectSummary() const
    {
        if (!lsuTrigger) return;
        const auto cap = chaos_lsu_tier_cap::resolve(lsu_tier_string,
                                                     static_cast<int>(lsuTrigger->tier));
        printf("CHAOS_LSU_NOEFFECT: injector=CHAOSArmTLB tier=F%d "
               "requested=%s effective=%s attempted=%lu eligible=%lu "
               "fires=%lu effective_injected=%lu no_effect=%lu "
               "first_no_effect_tick=%lu last_no_effect_tick=%lu\n",
               static_cast<int>(lsuTrigger->tier),
               cap.requested.c_str(), cap.effective.c_str(),
               (unsigned long)lsuTrigger->attempted,
               (unsigned long)lsuTrigger->eligible,
               (unsigned long)lsuTrigger->fires,
               (unsigned long)lookup_effective,
               (unsigned long)lookup_no_effect,
               (unsigned long)lookup_no_effect_first_tick,
               (unsigned long)lookup_no_effect_last_tick);
        fflush(stdout);
    }
```

> 实现者注意：`lsu_tier_string` 与 `chaos_lsu_tier_cap::resolve` 的实际签名以 `.hh`/`chaos_lsu_tier_cap.hh` 为准；若 `resolve` 只接受 `(const std::string&, int)` 且 `cap` 无 `requested/effective` 字段，则改用 `chaos_lsu_tier_cap::marker(cap)` 的既有字段名逐字对齐（**不得**自造字段名）。

- [ ] **Step 4: `.cc` 核心 —— 固定掩码 + effective 后置判定（替换 `:659-718`）**

```cpp
        // [R6-F5-NOEFFECT] F5 是**永久**卡死：规范 07:60 要求"warm-up 后固定
        // 一个物理 bit…之后每次读出/写入都施加同一掩码直到运行结束"。在这里
        // latch 抽取值即实现了"永久"；修复前每次 lookup 重抽，实测
        // armtlb_injections.log 每行 Mask 都不同，并把命中条目的 pfn 逐位
        // 摧毁到 0（0x81d75→0x81d74→0x81c74→…→0x0）。
        const FaultType chosen = fault_type_enum;   // (Random 已在上方解析)
        const bool pfn_model = (chosen == FaultType::StuckAtZero
                             || chosen == FaultType::StuckAtOne
                             || chosen == FaultType::BitFlip);
        if (!pfn_model) return;   // entry-state/attr/pfn 模型不走本路径

        const bool permanent =
            lookupTierMounted() && lsuTrigger->tier == ChaOSLsuTier::F5;

        uint64_t mask;
        if (fault_mask) {
            mask = fault_mask;               // 显式掩码优先
        } else if (permanent) {
            mask = chaos_tlb::latchStuckMask(0, f5_stuck_mask,
                        generateRandomMask(num_bits_to_change));
        } else {
            mask = generateRandomMask(num_bits_to_change);
        }
        if (mask == 0) {
            if (permanent) lsuTrigger->noteOutcome(false);  // 抽不到位 = 没写
            return;
        }

        chaos_tlb::StuckKind sk;
        switch (chosen) {
            case FaultType::StuckAtZero: sk = chaos_tlb::StuckKind::StuckAtZero; break;
            case FaultType::StuckAtOne:  sk = chaos_tlb::StuckKind::StuckAtOne;  break;
            case FaultType::BitFlip:     sk = chaos_tlb::StuckKind::BitFlip;     break;
            default: return;   // 结构上不可达（见下方 WalkPairing 注）
        }

        Addr old_pfn = entry->pfn;
        // [R4-4] gem5 自身的 PA 运算，在改写前后各取一次 —— 捕捉 64 位回绕
        // 导致高位 pfn 失效的情形。
        const Addr old_pa = entry->pAddr(va);
        const int entry_way = entryIndex(entry);
        const std::string entry_before = snapshotEntry(entry, old_pa);

        entry->pfn = chaos_tlb::applyStuckMask(mask, old_pfn, sk).new_pfn;

        // §1.2 注入后保护（N1 TRM Table 9-1 PROXY）。在条目返回 MMU **之前**
        // 运行 —— 1-bit parity_interleaved 检测会把 clean pfn 还原（Corrected）。
        // 因此"是否 effective"必须在它**之后**判定（见 Review Focus 1）。
        applyProtection(entry, mask, old_pfn, chosen);

        const bool effective = (entry->pfn != old_pfn);
        if (permanent) lsuTrigger->noteOutcome(effective);

        if (!effective) {
            // [R6-F5-NOEFFECT] no_effect：卡死值本来就等于正确值（07:60
            // "若某次事件的正确值本来就等于卡死值，该次不增加 activated"）。
            // 不建 fault identity、不建 ptag、不注册传播链、不写注入日志、
            // 不计 stats、不发 CHAOS_DETECT / prop_evt —— 只进聚合。
            ++lookup_no_effect;
            if (lookup_no_effect_first_tick == 0)
                lookup_no_effect_first_tick = curTick();
            lookup_no_effect_last_tick = curTick();
            return;
        }

        switch (chosen) {
            case FaultType::StuckAtZero: stats->numStuckAtZero++; break;
            case FaultType::StuckAtOne:  stats->numStuckAtOne++;  break;
            case FaultType::BitFlip:     stats->numBitFlips++;    break;
            default: break;
        }
        ++lookup_effective;
        stats->numFaultsInjected++;
        ++faults_injected_count;

        if (write_log) {
            *(log_stream->stream())
                << "Tick: " << curTick()
                << ", Site: arm_tlb_lookup_hit"
                << ", VA: 0x" << std::hex << va
                << ", old_pfn: 0x" << old_pfn
                << ", new_pfn: 0x" << entry->pfn
                << ", FaultType: " << faultTypeToString(chosen)
                << ", Mask: 0x" << mask << std::dec
                << ", effective: 1" << std::endl;
        }
        const Addr new_pa = entry->pAddr(va);
        registerTrace(va, old_pfn, entry->pfn, old_pa, new_pa,
                      entry->size + 1, faultTypeToString(chosen),
                      req_seq, req_size, entry_way,
                      /*candidate_way=*/-1, /*walk_id=*/0,
                      entry_before, snapshotEntry(entry, new_pa));
```

> **实现者注意（必须先读再改）**：上面的 `chosen` 重命名可能与上方 `:581-585` 已有的 `FaultType chosen = fault_type_enum;`（含 `Random` 解析）冲突。**保留上方那份**，本段直接使用它，不要重复声明。同理 `isEntryStateFault/chosen`、`PfnToMappedPage`、`isCamFault`、`WalkPairing` 的既有早退分支（`:511`、`:593-596`、`:603-657`、`:682-689`）保持原样，**不得删除**。

- [ ] **Step 5: F5 非 pfn 模型情形必须响亮（不得静默通过）**

在 `isEntryStateFault(chosen) || isAttrSubstFault(chosen)` 分支（`:593-596`）内、`applyEntryFieldFault(...)` 调用之后追加：

```cpp
            // [R6-F5-NOEFFECT] F5 的 outcome 记账目前只覆盖 pfn 改写模型。
            // 若某次 F5 运行选了 entry-state/attr 模型，必须响亮说明"本格未
            // 计入 no_effect 记账"，绝不静默当作已覆盖。
            if (lookupTierMounted() && lsuTrigger->tier == ChaOSLsuTier::F5)
                printf("CHAOS_LSU_TRIGGER_ALARM: injector=CHAOSArmTLB "
                       "mode=F5_NONPFN_MODEL fault_type=%s (F5 outcome "
                       "accounting covers pfn-mutating models only; this run's "
                       "fires are not fully accounted)\n",
                       faultTypeToString(chosen).c_str());
```

- [ ] **Step 6: 独立单测回归（不得破坏既有 6 个 C++ 单测）**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
for t in chaos_tlb_stuck_test chaos_tlb_pfn_candidate_test chaos_tlb_chain_containment_test \
         chaos_tlb_f6_applicability_test chaos_lsu_tier_cap_test chaos_consumer_summary_test; do
  [ -f tests/$t.cc ] || continue
  g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/$t.cc -o /tmp/$t && /tmp/$t || echo "FAILED $t"
done
g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/chaos_armtlb_lookup_ftier_test.cc -o /tmp/ftier && /tmp/ftier
g++ -std=c++17 -I CHAOS/gem5/src tests/chaos_lsu_trigger_test.cc -o /tmp/lsutrig && /tmp/lsutrig
```
Expected: 全部 ALL PASS，无 `FAILED`。

- [ ] **Step 7: Commit**

```bash
git add CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.hh CHAOS/gem5/src/arch/arm/CHAOSArmTLB/CHAOSArmTLB.cc
git commit -m "[LSU][MDSPEC][R6-F5-NOEFFECT] CHAOSArmTLB：F5 固定掩码 latch + no_effect 抑制（不建 ptag/不写日志/不发事件/不计 stats）+ 聚合摘要"
```

### Task 9b: （计划外，Task 8 引入的 NEW FAIL 修复）

**Files:** Modify `tests/chaos_tlb_f6_applicability_test.cc`

- [x] Task 8 把 F5 的 `injected` 改为由 `noteOutcome()` 决定后，该测试的 `[3] F5` 段仍断言旧契约
      （`injected == applied == eligible`），实测 `FAILED (2)`——**Task 8 引入的 NEW FAIL，原计划未覆盖**。
- [x] 修复：`drive()` 对 F5 镜像真实注入器契约（置 `require_outcome_accounting`、每次 fire 调
      `noteOutcome(applied)`），`Run` 增加 `no_effect`；断言改写为
      `fires == eligible`、`injected == applied == eligible`、`no_effect == fires - applied`，
      并**新增**不变量 `fires == injected + no_effect`（gate 双序各一条）。
- [x] 断言数 3 → 8（**加强，非削弱**）；F0/F2/F6 段未触碰。
- [x] 验证：`g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/chaos_tlb_f6_applicability_test.cc -o /tmp/f6app && /tmp/f6app`
      → `ALL PASS`，exit 0；全部 9 个独立单测 `ALL PASS`。
- [x] Commit `82c6ea4f`。

### Task 9c: （计划外，Task 9 的语义收窄）

- [x] 计划 Task 9 的 `if (!effective)` 被实现为 **`if (permanent && !effective)`**：否则 F1–F4 在
      "掩码恰好不改变 pfn"（≈50% 的抽取）时会出现 trigger `injected=1` 而 stats/日志为 0，
      触发 `tools/lsu_campaign.py:armtlb_count_sources` 的 `contradiction=True` 回归。
      规范 07:60 的 no_effect 规则本身只针对 F5，故收窄既是正确的也是更小改动。
- [x] `++lookup_effective` 改为仅在 `effective` 时自增（诚实命名）。
- [x] 前述 `lsu_tier_string` 在树中不存在，已新增该成员并由 `p.lsuTier` 赋值，使聚合摘要与启动
      `CHAOS_LSU_TIER_CAP` 走**同一个** `chaos_lsu_tier_cap::resolve()`，构造上不可能互相矛盾。

### Task 9d: （计划外，真机 run #1 暴露的两处遗漏）

**Files:** Modify `CHAOSArmTLB.cc`、`chaos_tlb_stuck.hh`、`tests/chaos_tlb_stuck_test.cc`

- [x] **真机实测（T03-F5-W4 seed1 run #1，8 分钟 610MB）**：`armtlb_injections.log` 里
      `Site: arm_tlb_lookup_hit` 行数 = **0**、`effective: 1` 行数 = **0**；全部内容是第一行 tier
      通知 + 无数行 `    protection: model=none bits=1 -> Raw`。`prop_evt.txt.gz` 仅 **289 B、事件 0**。
      ⇒ **no_effect 抑制与传播爆炸消除均已生效**；体积来源是**被 Task 9 漏 gate 的 protection 行**。
- [x] 修复 A：`applyProtection()` 内的无条件 `protection:` 日志移除，改由调用点在 **effective
      分支**（与注入行同生共死）打印其返回值。该函数全树仅 1 个调用点，改动面极小。
- [x] 修复 B：F5 掩码 latch 由 `latchStuckMask`（uniform 0..63）改为 **`latchStuckMaskForFrame`**
      —— 把抽取限制在该帧**实际存在的物理位**内。规范 07:60 要求"固定一个**物理** bit"；实测
      pfn≈20 位而 uniform 取 0..63 有约 **69%** 概率落在物理宽度之外，使整个运行恒为 no_effect。
- [x] 验证：`g++ -std=c++17 -Wall -Wextra -Werror -I CHAOS/gem5/src tests/chaos_tlb_stuck_test.cc -o /tmp/t && /tmp/t`
      → `ALL PASS`（10 条断言组）；8 个独立单测全过。
- [x] Commit（见链）。

### Task 10: 工具侧四方一致合同测试

**Files:**
- Create: `tests/test_lsu_armtlb_f5_noeffect.py`

**Interfaces:**
- Consumes: stdout 的 `CHAOS_LSU_TRIGGER:` / `CHAOS_LSU_NOEFFECT:` / `CHAOS_LSU_TIER_CAP:` 三种行；`armtlb_injections.log`；`stats.txt`。
- Produces: 可被 Task 12/17 复用的合同断言函数 `assert_f5_noeffect_consistency(outdir) -> list[str]`（返回违规列表，空 = 通过）。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lsu_armtlb_f5_noeffect.py
"""R6-F5-NOEFFECT 合同测试（纯离线，不跑 gem5）。

钉住：F5 的四方计数必须一致 ——
  trigger summary 的 injected / no_effect / fires，
  CHAOS_LSU_NOEFFECT 的 effective_injected / no_effect / fires，
  armtlb_injections.log 中 Site: arm_tlb_lookup_hit 且 effective: 1 的行数，
  stats.txt 的 board.chaos_armtlb.numFaultsInjected。
且 fires == injected + no_effect 必须成立。
"""
import re, textwrap, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def assert_f5_noeffect_consistency(outdir):
    """返回违规字符串列表（空 = 通过）。"""
    outdir = Path(outdir)
    bad = []
    td = None
    for cand in sorted(outdir.rglob("stats.txt")):
        if cand.stat().st_size > 0:
            td = cand.parent
            break
    if td is None:
        return ["no non-empty stats.txt found"]
    stdout = (td / "run.out").read_text(errors="replace") if (td / "run.out").exists() else ""

    def last(pat):
        m = re.findall(pat, stdout)
        return m[-1] if m else None

    trig = last(r"CHAOS_LSU_TRIGGER:\s*injector=(\S+)\s+tier=F(\d+)\s+attempted=(\d+)\s+"
                r"eligible=(\d+)\s+injected=(\d+).*?fires=(\d+)\s+no_effect=(\d+)")
    noeff = last(r"CHAOS_LSU_NOEFFECT:\s*injector=(\S+)\s+tier=F(\d+)\s+requested=(\S+)\s+"
                 r"effective=(\S+)\s+attempted=(\d+)\s+eligible=(\d+)\s+fires=(\d+)\s+"
                 r"effective_injected=(\d+)\s+no_effect=(\d+)")
    if trig is None:
        return ["CHAOS_LSU_TRIGGER line with fires/no_effect not found in run.out"]
    if noeff is None:
        return ["CHAOS_LSU_NOEFFECT line not found in run.out"]

    t_inj, t_fires, t_noeff = int(trig[4]), int(trig[5]), int(trig[6])
    n_fires, n_eff, n_noeff, n_req, n_efftier = int(noeff[6]), int(noeff[7]), int(noeff[8]), noeff[2], noeff[3]

    logf = td / "armtlb_injections.log"
    logged = 0
    if logf.exists():
        for line in logf.open(errors="replace"):
            if "Site: arm_tlb_lookup_hit" in line and "effective: 1" in line:
                logged += 1
    else:
        bad.append("armtlb_injections.log missing")

    stats = None
    m = re.search(r"board\.chaos_armtlb\.numFaultsInjected\s+(\d+)", (td / "stats.txt").read_text(errors="replace"))
    if m:
        stats = int(m.group(1))
    else:
        bad.append("stats.txt missing board.chaos_armtlb.numFaultsInjected")

    if t_fires != t_inj + t_noeff:
        bad.append(f"trigger: fires({t_fires}) != injected({t_inj}) + no_effect({t_noeff})")
    if n_fires != n_eff + n_noeff:
        bad.append(f"noeffect: fires({n_fires}) != effective_injected({n_eff}) + no_effect({n_noeff})")
    for name, val in (("trigger.fires", t_fires), ("noeffect.fires", n_fires)):
        if val != t_fires:
            bad.append(f"{name} disagrees with trigger.fires={t_fires}")
    if t_inj != n_eff:
        bad.append(f"trigger.injected({t_inj}) != noeffect.effective_injected({n_eff})")
    if t_noeff != n_noeff:
        bad.append(f"trigger.no_effect({t_noeff}) != noeffect.no_effect({n_noeff})")
    if n_eff != logged:
        bad.append(f"effective_injected({n_eff}) != injection-log effective rows({logged})")
    if stats is not None and stats != n_eff:
        bad.append(f"stats.numFaultsInjected({stats}) != effective_injected({n_eff})")
    if n_req != n_efftier:
        bad.append(f"requested tier({n_req}) != effective tier({n_efftier})")
    return bad


def test_synthetic_consistent():
    """合成一致样本：必须 0 违规。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "T03-F5-W4" / "seed1"
        p.mkdir(parents=True)
        (p / "run.out").write_text(textwrap.dedent("""\
            CHAOS_LSU_TIER_CAP: requested=F5 effective=F5 lookup_tier_enabled=1
            CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F5 attempted=900 eligible=900 injected=3 first_eligible_tick=1 last_eligible_tick=9 fires=900 no_effect=897 (activated=W3-L0-layer)
            CHAOS_LSU_NOEFFECT: injector=CHAOSArmTLB tier=F5 requested=F5 effective=F5 attempted=900 eligible=900 fires=900 effective_injected=3 no_effect=897 first_no_effect_tick=2 last_no_effect_tick=900
            """))
        (p / "armtlb_injections.log").write_text("".join(
            f"Tick: {i}, Site: arm_tlb_lookup_hit, VA: 0x1, old_pfn: 0x2, new_pfn: 0x1, "
            f"FaultType: stuck_at_zero, Mask: 0x1, effective: 1\n" for i in range(3)))
        (p / "stats.txt").write_text("board.chaos_armtlb.numFaultsInjected 3\n")
        assert assert_f5_noeffect_consistency(d) == []


def test_synthetic_inconsistent_is_loud():
    """人为制造不一致：必须被点名，绝不静默通过。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "T03-F5-W4" / "seed1"
        p.mkdir(parents=True)
        (p / "run.out").write_text(textwrap.dedent("""\
            CHAOS_LSU_TRIGGER: injector=CHAOSArmTLB tier=F5 attempted=900 eligible=900 injected=5 first_eligible_tick=1 last_eligible_tick=9 fires=900 no_effect=897 (activated=W3-L0-layer)
            CHAOS_LSU_NOEFFECT: injector=CHAOSArmTLB tier=F5 requested=F5 effective=F5 attempted=900 eligible=900 fires=900 effective_injected=3 no_effect=897 first_no_effect_tick=2 last_no_effect_tick=900
            """))
        (p / "armtlb_injections.log").write_text("")
        (p / "stats.txt").write_text("board.chaos_armtlb.numFaultsInjected 3\n")
        bad = assert_f5_noeffect_consistency(d)
        assert bad, "inconsistent counts must be reported"
        assert any("fires" in b or "injected" in b for b in bad)


if __name__ == "__main__":
    test_synthetic_consistent()
    test_synthetic_inconsistent_is_loud()
    print("test_lsu_armtlb_f5_noeffect: ALL PASS")
```

- [ ] **Step 2: 运行，确认通过**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
python3 -m pytest tests/test_lsu_armtlb_f5_noeffect.py -q
python3 tests/test_lsu_armtlb_f5_noeffect.py
```
Expected: `2 passed` 与 `ALL PASS`。

- [ ] **Step 3: Commit**

```bash
git add tests/test_lsu_armtlb_f5_noeffect.py
git commit -m "[LSU][MDSPEC][R6-F5-NOEFFECT] 四方计数一致合同测试（trigger/noeffect/log/stats）+ 不一致响亮失败"
```

### Task 11: 统一构建 + 独立单测 + pytest 全回归

- [ ] **Step 1: 零警告构建（新 worktree 首次配置慢 ~2 分钟/次 conftest，不是卡死）**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5
scons -j16 build/ARM/gem5.opt 2>&1 | tee /tmp/r6_f5_build.log | tail -20
grep -nE 'warning:|error:' /tmp/r6_f5_build.log | grep -v 'Checking' | head -20; echo "warnings/errors above (空 = 通过)"
```
Expected: 构建成功；无本次改动引入的 warning/error。

- [ ] **Step 2: 记录新二进制身份**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
sha256sum CHAOS/gem5/build/ARM/gem5.opt | tee runs_bin.sha256
git -C . rev-parse HEAD
```
把 SHA 与 HEAD 记入 `runs/lsu/r6_reports/R6-F5-NOEFFECT-IDENTITY.txt`（新建，未跟踪）。

- [ ] **Step 3: 全部独立 C++ 单测**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
for f in tests/*.cc; do t=$(basename "$f" .cc)
  g++ -std=c++17 -I CHAOS/gem5/src "$f" -o "/tmp/$t" 2>/dev/null && "/tmp/$t" >/tmp/$t.out 2>&1 || true
  grep -qi 'FAIL' /tmp/$t.out && echo "FAIL $t" || echo "pass $t"
done
```
Expected: 无 `FAIL` 行。

- [ ] **Step 4: pytest 全量回归，记录基线对比**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
python3 -m pytest tests/ -q 2>&1 | tail -20 | tee /tmp/r6_f5_pytest.log
```

- [ ] **Step 5: 与 origin/fi-ding 的基线对比，确认 NEW FAIL = 0**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
git stash list >/dev/null 2>&1
git worktree add /tmp/r6_f5_base origin/fi-ding 2>/dev/null || true
cd /tmp/r6_f5_base && python3 -m pytest tests/ -q 2>&1 | tail -5 | tee /tmp/r6_f5_pytest_base.log
cd /home/sdc/gem5-fi-ding && git worktree remove --force /tmp/r6_f5_base 2>/dev/null || true
diff <(grep -c FAIL /tmp/r6_f5_pytest.log) <(grep -c FAIL /tmp/r6_f5_pytest_base.log) && echo "NEW FAIL = 0"
```
Expected: 计数相同，`NEW FAIL = 0`。**若出现新增失败 → 立即停止汇报，不得提交。**

---

## Phase C — 分析工具内存治理

### Task 12: `lsu_prop_fields.py` 流式读取 + EVENT_CAP

**Files:**
- Modify: `tools/lsu_prop_fields.py:521-580`（`read_stream` / `read_events`）
- Test: `tests/test_lsu_prop_stream_cap.py`

**Interfaces:**
- Consumes: 现有 `read_stream(path)`、`read_events(path)` 调用方（`lsu_chain_check.py`、`lsu_pilot_evidence.py`、`lsu_campaign.py`）。
- Produces: `EVENT_CAP = 200000`；`read_events` 在超限时返回 `(events, truncated)` 且调用方可判 `OVER_CAP`。

- [ ] **Step 1: 写失败测试**

```python
# tests/test_lsu_prop_stream_cap.py
"""R6 prop_evt 流式读取 + EVENT_CAP 语义（合成超大流，峰值内存有界）。"""
import gzip, os, resource, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tools.lsu_prop_fields as PF


def _write_stream(path, n):
    with gzip.open(path, "wt") as f:
        f.write("# prop-evt v1: header\n")
        for i in range(n):
            f.write(f"PROP-EVT: tick={i} kind=probe fault_id=1 event_id={i} parent_event_id=0\n")


def test_cap_is_200k():
    assert PF.EVENT_CAP == 200000


def test_under_cap_is_not_truncated():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prop_evt.txt.gz"
        _write_stream(p, 1000)
        ev, truncated = PF.read_events(p)
        assert len(ev) == 1000 and truncated is False


def test_over_cap_is_flagged_not_silently_truncated():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prop_evt.txt.gz"
        _write_stream(p, PF.EVENT_CAP + 5000)
        ev, truncated = PF.read_events(p)
        assert truncated is True, "over-cap streams must be flagged truncated"
        assert len(ev) <= PF.EVENT_CAP + 1


def test_peak_rss_bounded_on_huge_stream():
    """合成 ~1200 万事件（远超 EVENT_CAP）——峰值 RSS 必须有界。"""
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prop_evt.txt.gz"
        _write_stream(p, 12_000_000)
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        ev, truncated = PF.read_events(p)
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert truncated is True
        growth_mb = (after - before) / 1024.0
        assert growth_mb < 400, f"peak RSS grew {growth_mb:.0f} MB (>400 MB bound)"


if __name__ == "__main__":
    test_cap_is_200k(); test_under_cap_is_not_truncated()
    test_over_cap_is_flagged_not_silently_truncated(); test_peak_rss_bounded_on_huge_stream()
    print("test_lsu_prop_stream_cap: ALL PASS")
```

- [ ] **Step 2: 运行，确认失败**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
python3 -m pytest tests/test_lsu_prop_stream_cap.py -q
```
Expected: FAIL（`EVENT_CAP` 不存在 / 超限未标记）。

- [ ] **Step 3: 实现（改造 `read_stream`，保持调用方签名兼容）**

在 `lsu_prop_fields.py` 的模块级常量区加：

```python
# [R6-STREAM] 权威事件上限：超过即 OVER_CAP（响亮），绝不静默截断后继续
# 认证。与 lsu_r6_status_table.py 的既有语义一致。
EVENT_CAP = 200000
```

把 `read_stream` 的"把所有事件塞进 list"改为**有界**：

```python
def read_stream(path, cap=EVENT_CAP):
    """流式读取 prop_evt.txt.gz。

    返回 (events, truncated)。events 最多 cap 条；超过 cap 时 truncated=True
    且**继续流式计数**（不保留超额事件、不载入内存），保证峰值内存与流大小
    无关。绝不整体 read() 解压流。
    """
    events, truncated, seen = [], False, 0
    path = Path(path)
    if not path.exists():
        return events, truncated
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", errors="replace") as f:
        for line in f:                     # 逐行流式；不 read()
            if not line.startswith("PROP-EVT:"):
                continue
            seen += 1
            if seen > cap:
                truncated = True
                continue                   # 只计数，不保留
            events.append(parse_prop_evt(line))
    return events, truncated


def read_events(path, cap=EVENT_CAP):
    """兼容旧签名的封装（旧调用方忽略 truncated 时行为 = 有界）。"""
    return read_stream(path, cap)
```

> 实现者注意：`parse_prop_evt` 的实际函数名以文件为准（若为内联解析，抽成同名函数）；**不得**改变既有 `read_events` 的返回元组含义。

- [ ] **Step 4: 运行测试 + 既有调用方回归**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
python3 -m pytest tests/test_lsu_prop_stream_cap.py -q
python3 -m pytest tests/test_lsu_chain_check.py tests/test_lsu_campaign_propagation.py -q
```
Expected: 新测试全过；既有测试不新增失败。

- [ ] **Step 5: Commit**

```bash
git add tools/lsu_prop_fields.py tests/test_lsu_prop_stream_cap.py
git commit -m "[LSU][MDSPEC][R6-STREAM] prop_evt 流式读取 + EVENT_CAP=200000（超限 UNPROVEN/OVER_CAP，峰值内存有界）"
```

### Task 13: `lsu_r6_golden_control.py` 去整体读取

**Files:**
- Modify: `tools/lsu_r6_golden_control.py:58-61`、`:118-121`
- Test: `tests/test_lsu_prop_stream_cap.py`（追加一组）

- [ ] **Step 1: 追加失败测试**

```python
def test_golden_control_bounded_on_huge_stream():
    """golden_control 的流探测不得整体 read() 解压流。"""
    import subprocess
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "prop_evt.txt.gz"
        _write_stream(p, 12_000_000)
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        import lsu_r6_golden_control as GC
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        GC.stream_status(p)          # (实现后语义：返回状态而不载入全部事件)
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert (after - before) / 1024.0 < 400, "golden_control must not load the whole stream"
```

- [ ] **Step 2: 运行，确认失败**（`AttributeError` 或 RSS 超限）

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
python3 -m pytest tests/test_lsu_prop_stream_cap.py::test_golden_control_bounded_on_huge_stream -q
```

- [ ] **Step 3: 实现**

把 `:58-61` 与 `:118-121` 的 `text = fh.read()` 改为逐行流式（保留原有正则语义）：

```python
    # [R6-STREAM] 逐行流式；禁止整体 read() 解压流（超大流会 OOM）。
    with opener(path, "rt", errors="replace") as fh:
        for line in fh:
            ...既有正则匹配逻辑，作用于 line...
```

- [ ] **Step 4: 运行测试 + 该工具既有测试**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
python3 -m pytest tests/test_lsu_prop_stream_cap.py -q
python3 -m pytest tests/test_lsu_r6_golden_control.py -q 2>/dev/null || echo "(该测试文件不存在，跳过)"
```
Expected: 全过 / NEW FAIL 0。

- [ ] **Step 5: Commit**

```bash
git add tools/lsu_r6_golden_control.py tests/test_lsu_prop_stream_cap.py
git commit -m "[LSU][MDSPEC][R6-STREAM] lsu_r6_golden_control 逐行流式（去掉整体 read()）"
```

---

## Phase D — 定向验证 + 单次统一构建 + T03-F5 seed1

### Task 14: T03-F5-W4 seed1（新目录、并发 1、外部只读监控、超限即停）

**Files:**
- Create: `runs/lsu/r6_n7_T03-F5-W4_s1/`（全新目录，**不得**复用旧名）
- Create: `runs/lsu/r6_n7_monitor.log`、`runs/lsu/r6_n7_monitor.sh`

**Interfaces:**
- Consumes: Task 11 的新二进制。
- Produces: 受控规模的样本；监控日志。

- [ ] **Step 1: 建外部只读监控脚本（每 60s，不用 `tail -f`）**

```bash
cat > /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_monitor.sh <<'EOF'
#!/bin/bash
# 每 60s 采样被监控目录的文件大小与事件数摘要；不做任何写入到被测目录。
set -u
MON=/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_monitor.log
OUT=/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1
while :; do
  [ -d "$OUT" ] || { sleep 60; continue; }
  {
    echo "=== $(date -Is) mem=$(awk '/MemAvailable/{printf "%d",$2/1048576}' /proc/meminfo)G"
    for f in armtlb_injections.log prop_evt.txt.gz run.out stats.txt; do
      [ -e "$OUT/$f" ] && echo "  $f $(stat -c%s "$OUT/$f") B"
    done
    [ -e "$OUT/prop_evt.txt.gz" ] && echo "  prop_evt rows~ $(gzip -dc "$OUT/prop_evt.txt.gz" 2>/dev/null | grep -c '^PROP-EVT:')"
    pgrep -f 'gem5.opt --outdir' >/dev/null && echo "  gem5: RUNNING" || echo "  gem5: gone"
  } >>"$MON" 2>&1
  sleep 60
done
EOF
chmod +x /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_monitor.sh
```

- [ ] **Step 2: 在 detached tmux 中启动（会话名明确）**

```bash
tmux new-session -d -s r6_n7_monitor '/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_monitor.sh'
tmux ls | grep r6_n7_monitor
```

- [ ] **Step 3: 准备运行脚本（复制 n6 runner，改目录前缀与超限闸）**

```bash
cd /home/sdc/gem5-fi-ding/runs/lsu
sed -e 's#r6_n6_#r6_n7_#g' -e 's#r6_n6_run#r6_n7_run#g' r6_n6_run.sh > r6_n7_run.sh
sed -e 's#r6_n6_#r6_n7_#g' -e 's#r6_n6_bin_identity#r6_n7_bin_identity#g' r6_n6_run.sh > /tmp/chk.sh
chmod +x r6_n7_run.sh
# 新建身份文件，指向新二进制
BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026/CHAOS/gem5/build/ARM/gem5.opt
{
  echo "BIN_PATH=$BIN"
  echo "BIN_SHA=$(sha256sum $BIN | cut -d' ' -f1)"
  echo "BIN_SIZE=$(stat -c%s $BIN)"
  echo "binary_source_head=$(git -C /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026 rev-parse HEAD)"
  echo "analysis_tool_head=$(git -C /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026 rev-parse HEAD)"
} | tee r6_n7_bin_identity.txt
# 让 runner 指向新 worktree
sed -i 's#^WT=.*#WT=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026#' r6_n7_run.sh
sed -i 's#r6_n6_bin_identity#r6_n7_bin_identity#' r6_n7_run.sh
```

- [ ] **Step 4: 在 tmux 中启动单个 seed1（并发 1）**

```bash
tmux new-session -d -s r6_n7_f5s1 "cd /home/sdc/gem5-fi-ding/runs/lsu && ./r6_n7_run.sh 1 T03-F5-W4; echo DONE >> r6_n7_run_s1.log"
sleep 30; tail -5 /home/sdc/gem5-fi-ding/runs/lsu/r6_n7_run_s1.log
```

- [ ] **Step 5: 安全停止判据（每个采样周期人工/脚本核对）**

发现下列任一情形 → 立即 `tmux kill-session -t r6_n7_f5s1` + `pkill -f 'gem5.opt --outdir .*r6_n7'`，标记 `OVER_CAP`：
- 任一单文件 > 200MB；
- `prop_evt` 行数 > 200000（EVENT_CAP）；
- 连续 3 个采样周期 `armtlb_injections.log` 增长率 > 5MB/min 且 stats.txt 仍为 0；
- `stats.txt` 仍为 0 且无终局迹象（对照 golden 的 `hostSeconds ≈ 1976.86` 推断合理墙钟上限）。

```bash
# 判据自动检查（在循环里跑）
OUT=/home/sdc/gem5-fi-ding/runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1
sz=$(stat -c%s "$OUT/armtlb_injections.log" 2>/dev/null || echo 0)
[ "$sz" -gt $((200*1024*1024)) ] && echo "OVER_CAP: injection log ${sz}B"
```

- [ ] **Step 6: 停止监控 tmux（运行结束后）**

```bash
tmux kill-session -t r6_n7_monitor 2>/dev/null; tmux ls 2>/dev/null || echo "no tmux sessions"
```

### Task 15: T03-F5-W4 seed1 验收

- [ ] **Step 1: 30 项自动验收**

```bash
cd /home/sdc/gem5-fi-ding
cp /tmp/r6_f5_base 2>/dev/null || true
cp runs/lsu/r6_n6_accept.py runs/lsu/r6_n7_accept.py
python3 runs/lsu/r6_n7_accept.py runs/lsu/r6_n7_T03-F5-W4_s1 T03-F5-W4 1
```
Expected: 全 PASS（除第 30 项 outcome 由 oracle 语义决定）。**任一项 FAIL → 停止，不跑 seed2/seed3。**

- [ ] **Step 2: 任务书 seed1 验收条件逐条核对**

```bash
cd /home/sdc/gem5-fi-ding/runs/lsu
O=r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1
grep -m1 'CHAOS_LSU_TIER_CAP' "$O/run.out"
grep -m1 'CHAOS_LSU_NOEFFECT' "$O/run.out"
grep -m1 'CHAOS_LSU_TRIGGER:' "$O/run.out"
# 真实注入存在，且注入日志中不得出现 old_pfn == new_pfn
grep -c 'effective: 1' "$O/armtlb_injections.log"
grep 'Site: arm_tlb_lookup_hit' "$O/armtlb_injections.log" \
  | awk -F'old_pfn: |, new_pfn: ' '{split($2,a," "); split($3,b," "); if (a[1]==b[1]) print "NOEFFECT-LEAK: " $0}' | head; echo "(空 = 无泄漏)"
# 文件规模受控
du -sh "$O"; ls -la "$O"
```

- [ ] **Step 3: 四方一致 + 分析峰值 RSS**

```bash
cd /home/sdc/gem5-fi-ding
python3 - <<'PY'
import resource, sys
sys.path.insert(0, ".")
from tests.test_lsu_armtlb_f5_noeffect import assert_f5_noeffect_consistency
import importlib.util, pathlib
spec = importlib.util.spec_from_file_location("t", "tests/test_lsu_armtlb_f5_noeffect.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
bad = m.assert_f5_noeffect_consistency(pathlib.Path("runs/lsu/r6_n7_T03-F5-W4_s1"))
print("violations:", bad)
print("analysis peak RSS MB:", resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0)
assert not bad
PY
```

- [ ] **Step 4: 前后规模对比表**

```bash
{
  echo "| 文件 | 修复前 | 修复后 |"; echo "|---|---|---|"
  echo "| armtlb_injections.log | 2768458486 | $(stat -c%s runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/armtlb_injections.log) |"
  echo "| prop_evt.txt.gz | 2401477771 | $(stat -c%s runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/prop_evt.txt.gz) |"
  echo "| run.out | 1612035897 | $(stat -c%s runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/run.out) |"
  echo "| prop_trace.csv.gz | 590774909 | $(stat -c%s runs/lsu/r6_n7_T03-F5-W4_s1/T03-F5-W4/seed1/prop_trace.csv.gz) |"
} | tee runs/lsu/r6_reports/R6-F5-SIZE-COMPARE.md
```

- [ ] **Step 5: 若任一条不满足 → 停止并汇报（不跑 seed2/seed3）。**

---

## Phase E — 统一二进制批次

### Task 16: T01-F1-W4 ×3 + T01-F2-W4 ×3（新 SHA，全新目录，并发 ≤2）

- [ ] **Step 1: 启动（detached tmux）**

```bash
tmux new-session -d -s r6_n7_t01 \
  "cd /home/sdc/gem5-fi-ding/runs/lsu && ./r6_n7_run.sh 1 T01-F1-W4 T01-F2-W4 && ./r6_n7_run.sh 2 T01-F1-W4 T01-F2-W4 && ./r6_n7_run.sh 3 T01-F1-W4 T01-F2-W4; echo ALLDONE >> r6_n7_run_s3.log"
```
（runner 内建两个 flock slot，故实际并发 ≤2；启动/结束各自核 binary SHA，不一致即 `FATAL sha drift`。）

- [ ] **Step 2: 逐个验收**

```bash
cd /home/sdc/gem5-fi-ding
for s in 1 2 3; do for c in T01-F1-W4 T01-F2-W4; do
  python3 runs/lsu/r6_n7_accept.py runs/lsu/r6_n7_${c}_s${s} "$c" "$s" | tail -2
done; done
```
Expected: 6/6 全 PASS，且文件规模保持 KB–MB 级。

### Task 17: T03-F5-W4 seed2/seed3（一次一个）

- [ ] **Step 1: seed2**

```bash
tmux new-session -d -s r6_n7_f5s2 "cd /home/sdc/gem5-fi-ding/runs/lsu && ./r6_n7_run.sh 2 T03-F5-W4; echo DONE >> r6_n7_run_s2.log"
```
监控同 Task 14 Step 5（重启 `r6_n7_monitor.sh`，路径通用）。

- [ ] **Step 2: seed2 验收后 seed3**（同法，`-s r6_n7_f5s3`，`./r6_n7_run.sh 3 T03-F5-W4`）。

- [ ] **Step 3: 9/9 汇总表**

```bash
cd /home/sdc/gem5-fi-ding
{
  echo "| RunID | seed | terminal | admitted | certified | violations |"
  echo "|---|---|---|---|---|---|"
  for s in 1 2 3; do for c in T01-F1-W4 T01-F2-W4 T03-F5-W4; do
    d=runs/lsu/r6_n7_${c}_s${s}/${c}
    python3 - "$d" "$c" "$s" <<'PY'
import json,sys
d,c,s=sys.argv[1],sys.argv[2],sys.argv[3]
try:
    r=json.load(open(f"{d}/chain_report.json"))
    print(f"| {c} | {s} | {r.get('terminal')} | {r.get('admitted')} | {r.get('certified')} | {r.get('violations')} |")
except Exception as e:
    print(f"| {c} | {s} | ERR | ERR | ERR | {e} |")
PY
  done; done
} | tee runs/lsu/r6_reports/R6-F5-NOEFFECT-BATCH9.md
```
Expected: 9 行全部 `admitted=True`、`certified=True`、`violations=[]`。

---

## Phase F — 提交与合入

### Task 18: 推送修复分支

- [ ] **Step 1: 确认分支与远端**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
git log --oneline origin/fi-ding..HEAD
git status --porcelain
```
Expected: 仅本计划的提交；工作区干净（`runs/` 在 worktree 外，不入此仓）。

- [ ] **Step 2: 推送**

```bash
git push -u origin fix/r6-f5-noeffect-20261026
```

### Task 19: 串行合入最新 fi-ding（不覆盖远端）并推送

- [ ] **Step 1: 拉最新并确认可快进/无冲突**

```bash
cd /home/sdc/gem5-fi-ding && git fetch origin
git log --oneline origin/fi-ding -1
```

- [ ] **Step 2: 在新 worktree 中 rebase/merge 到 origin/fi-ding**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-f5-noeffect-20261026
git rebase origin/fi-ding
```
（如冲突：**停止并汇报**，不擅自解决语义冲突。）

- [ ] **Step 3: 合入前回归 NEW FAIL = 0**（同 Task 11 Step 5 的方法，基线用 rebase 后的 `origin/fi-ding`）。

- [ ] **Step 4: 推送**

```bash
git push origin HEAD:fix/r6-f5-noeffect-20261026
# 合入 fi-ding（用户已授权串行合入；不 force，不覆盖远端）：
cd /home/sdc/gem5-fi-ding && git push origin HEAD:fi-ding   # 仅在 fi-ding 可快进时
```
**若不可快进 → 停止并汇报**，等待指示；**绝不** `--force`。

### Task 20: 最终报告

写 `runs/lsu/r6_reports/R6-F5-NOEFFECT-FINAL.md`，逐条覆盖任务书第六节的 12 项：
删除路径与释放字节数、`/home` 前后空间、权威 16/16 完整性、F5 爆炸根因、修改文件与提交、no_effect 与 effective 的新语义、测试与回归、新二进制 SHA、T03-F5 seed1 修复前后文件大小对比、9 个 seed 的 terminal/admitted/certified/violations、是否 9/9、尚未解决的问题。

---

## Self-Review

**1. Spec coverage**

| 任务书要求 | 覆盖任务 |
|---|---|
| 清理台账 md+json（路径/字节/理由/引用/大文件 SHA/时间/df） | Task 1–6 |
| 失败目录诊断包 + 删除 | Task 2 |
| 六个旧巨流目录（选项 3：只删巨流） | Task 3 |
| `RAW_STREAMS_REMOVED.md` + 不改 SIX-PROPAGATION-PATHS + 声明放弃复算 | Task 3 Step 4/7 |
| 备份盘点 | Task 4 |
| worktree 审计（先清单后执行，禁 rm -rf） | Task 5 |
| candidate≠injection / no_effect 语义 6 条 | Task 7–9 |
| F5 F0/F1 语义不得偷换、不得被 max_faults 截断 | Task 9（`permanent` 只用于 latch 与记账，`lookupTierFires` 路径不变；`max_faults` 仍只在 legacy 分支） |
| no_effect 聚合字段集 | Task 9 Step 3 |
| 四方一致 + 响亮失败 | Task 10 |
| 不得作弊（删真事件/伪 chain_end/放宽 admission/超限记 PASS） | Global Constraints + Task 15 Step 2（`NOEFFECT-LEAK` 检查） |
| F5 规范定义核对（固定位 vs 每次重选） | 规范已引：`07:60` 要求固定位 ⇒ 按规范修为固定 location；Task 7/9 |
| 分析工具流式 + EVENT_CAP | Task 12–13 |
| 定向测试/构建/回归/单次统一构建/身份记录 | Task 11 |
| 只跑 T03-F5 seed1 + 外部只读监控 | Task 14 |
| seed1 验收条件逐条 | Task 15 |
| 统一二进制重跑 6 条 + 9/9 | Task 16–17 |
| 提交/推送/串行合入/不覆盖远端/合并前后回归 | Task 18–19 |
| 最终报告 12 项 | Task 20 |
| detached tmux + 重连先查 PID/输出/完成标志 | Task 14/16/17（**重连时先** `tmux ls` + `ps -eo pid,args | grep gem5` + `cat <out>.exit_code` + `ls .done`） |

**2. Placeholder scan** — 已消除：所有步骤含可执行命令与真实期望输出；两处"以文件为准"的注记（`chaos_lsu_tier_cap::resolve` 字段名、`parse_prop_evt` 函数名）是**指向既有代码的精确指令**，非 TBD。

**3. Type consistency** — `applyStuckMask/latchStuckMask/StuckKind/StuckOutcome`（Task 7 定义）在 Task 9 按同名同签名使用；`noteOutcome/fires/no_effect/outcomes_recorded/require_outcome_accounting`（Task 8 定义）在 Task 9 Step 2 与 Task 10 解析中同名使用；`EVENT_CAP/read_stream/read_events`（Task 12 定义）在 Task 13 复用。

**4. Review Focus 对应测试** — (1)→Task 7 组(1)(3) + Task 9 Step 4 后置判定；(2)→Task 7 组(7)(8)；(3)→Task 8 Step 1 + Task 10；(4)→Task 9 Step 4 早退分支 + Task 15 Step 2 的 `NOEFFECT-LEAK` 检查；(5)→Task 12 Step 1 的 `test_peak_rss_bounded_on_huge_stream` + Task 13 Step 1。

---

## Execution Handoff

执行方式：**Subagent-driven**（用户已选定）——每个任务派新 subagent 实现，再由新 subagent 独立复核后才进入下一任务；Task 11/15/17 完成后各跑一次整分支复核。
