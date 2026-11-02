# LSU C 单元（L1d Cache）完整验证 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 C 单元全部 31 个「可运行、非 F6」权威 RunID 各完成 3 个合格 seed，每个 seed 具备 L0→L5 完整真实观测链、逐 fault 可复现 Markdown，并完成证据审计、索引、全量回归与 `origin/fi-ding` 合并部署。

**Architecture:** 复用 R6-S W1 已冻结的 SE 观测管线（`tools/lsu_campaign.py` 每样本自动挂 `--chaos_propagation`，产出 `prop_evt.txt.gz` + `chain_report.json`），新建 C 单元专用证据目录 `runs/lsu/r6_c_unit/`。证据读取/文档生成/审计工具从 W1 的 LSQFwd 专用实现泛化为 cache 族（新文件，不改动 W1 工具的行为）。运行由单 seed 启动器 + 并行队列驱动（每 seed 独立锁/目录/manifest，最多 8 并发，12h/seed）。

**Tech Stack:** bash 5.2（flock、后台 tmux）、Python 3（gzip/json/csv）、gem5.opt（SE classic cache + CHAOSCache + CHAOSPropagation）、pytest。

**Spec:** 本计划自身即规格；上游依据 `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-07-展开执行矩阵.md` §C 行与 `runs/lsu/r6_matrix_325.csv`（C 行「记录状态=试跑」）。

## Global Constraints

- 基线：`origin/fi-ding = f129106748a11a2f6c6f0a8a229c97fa66a09395`。工作分支 `fix/r6-c-unit-20261102`，工作树 `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102`。
- 权威二进制：`/home/sdc/gem5-fi-ding-cleanup-20261029/binaries/gem5.opt-6db026e7`，SHA-256 必须为 `6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4`。任何 SHA 漂移立即停批。
- 一律以 `LSU_GEM5_BIN=<上述路径>` 显式指定二进制；不得使用任何 worktree 内旧 `build/`。
- 目标集合固定为 31 个 RunID（`记录状态=试跑` 且 `频率≠F6`）：
  `C01-F0-W6,C01-F1-W6,C01-F2-W6,C02-F0-W6,C02-F2-W6,C03-F5-W6,C03-F5-W10,C04-F0-W6,C04-F1-W6,C04-F2-W6,C05-F0-W6,C05-F2-W6,C06-F0-W6,C06-F2-W6,C06-F5-W6,C07-F0-W6,C07-F2-W6,C07-F5-W6,C08-F0-W6,C08-F2-W6,C08-F5-W6,C09-F0-W6,C09-F0-W10,C09-F2-W6,C09-F2-W10,C10-F0-W6,C10-F0-W10,C10-F3-W6,C10-F3-W10,C10-F5-W6,C10-F5-W10`
- 每个 RunID 恰好 seed 1/2/3 各一次；**不重跑**已合格 seed；失败 seed 保留现场，只有锁冲突（rc=3）自动重试。
- 排除：所有 F6、W1（fs-infra）、W7（multicore）、W11（SPEC license）、C11/C12/C14/C15（consumer-side 未实现）、C13（B0 N/A）。**不启动 L/O/P 单元。**
- 权威证据/文档根：`/home/sdc/gem5-fi-ding/runs/lsu/`。主工作树 `/home/sdc/gem5-fi-ding` 是脏树，**只写 `runs/lsu/`，不执行 reset/checkout/merge/commit/删除**。
- 并发：SE 最多 8 个 gem5；门禁 MemAvailable≥12GiB、`/home`≥30GiB、swap 下降>2GiB 停批。每 seed 墙钟上限 43200s；外层 `timeout --signal=INT --kill-after=120`（campaign 需 SIGINT 优雅收尾）。
- 诚实口径：`n/a` 不填零；`chain_end` 永不充当 L5；超限事件流用 `regrade_r6_w1_event_cap.py` 的等价逻辑复判并保留原件 SHA  provenance；任何未闭合链如实记录，不升格。
- Git：显式 `git add <路径>`，绝不 `git add -A`；每个任务一个提交；提交后自动 `git push origin fix/r6-c-unit-20261102`；不 push `main`。

## Review Focus

- 注入确实发生（`cache_injections.log` 有 `Tick:` 行）但 `prop_evt` 无对应 L0 `inj` 事件 → 判定为传播模型缺口，必须诊断而非当成 Masked 通过。
- F5/stuck-at 的 `no_effect` 必须使 `fires = injected + no_effect` 守恒；不守恒即工具缺陷。
- `chain_report.json` 的 `truncated=True` 可能只是 `EVENT_CAP` 分析上限（W1 已实证），必须用 gzip EOF + 事件总数复核后再判。
- 缓存族 `KIND_LAYER` 缺失会让文档把真实层显示为 `—`；审计必须与 `chain_report.edges` 逐条交叉核验。
- 同一 RunID 的 seed 必须真的不同（RNG seed 生效），三个 seed 的注入地址/时间不得完全一致。

---

### Task 1: 基线与 canary 验证（决定后续路线）

**Files:**
- Create: `tools/r6_c_canary.sh`
- Output: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary/C01-F0-W6_s1/`

**Interfaces:**
- Consumes: `tools/lsu_campaign.py`（f1291067 版本，`resolve_g5()` 读 `LSU_GEM5_BIN`；`propagation_flags()` 自动挂 `--chaos_propagation`）。
- Produces: 一份可审计的 C 样本目录，供 Task 2/3 用真实数据开发；决定是否进入 Task 2A（C++ 传播模型修复）分支。

- [x] **Step 1: 记录基线事实**（HEAD=f1291067；SHA=6db026e7…fef4；无并发 gem5；MemAvailable 25G；/home 42G）

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102
git rev-parse HEAD                      # 期望 f1291067...
sha256sum /home/sdc/gem5-fi-ding-cleanup-20261029/binaries/gem5.opt-6db026e7
free -g; df -h /home
pgrep -fa 'gem5.opt|lsu_campaign' || true
```

期望：HEAD=f1291067；SHA=6db026e7…fef4；无 gem5/campaign 在跑；MemAvailable≥12GiB；/home≥30GiB。

- [x] **Step 2: 写 canary 启动器**（`tools/r6_c_canary.sh`，提交 85187831）

`tools/r6_c_canary.sh`：

```bash
#!/usr/bin/env bash
set -u
RUN_ID="${1:?run id}"; SEED="${2:?seed}"; TIMEOUT="${3:-43200}"
WT=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102
BIN=/home/sdc/gem5-fi-ding-cleanup-20261029/binaries/gem5.opt-6db026e7
OUTROOT=/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary
DIR="$OUTROOT/${RUN_ID}_s${SEED}"
LOG=/home/sdc/gem5-fi-ding-cleanup-20261029/r6c-canary-${RUN_ID}-s${SEED}.log
mkdir -p "$OUTROOT"
[ -e "$DIR/.done" ] && { echo "ALREADY DONE: $DIR"; exit 0; }
[ -d "$DIR" ] && [ -n "$(ls -A "$DIR" 2>/dev/null)" ] && { echo "REFUSED: non-fresh $DIR" >&2; exit 4; }
mkdir -p "$DIR"
SHA=$(sha256sum "$BIN" | awk '{print $1}')
[ "$SHA" = "6db026e7ffa1ec3c95d1bc3065188cffdb61290633c6aa7a7e97456a028f9ef4" ] || { echo "SHA DRIFT" >&2; exit 7; }
START=$(date -Iseconds)
python3 - "$DIR/manifest.json" "$RUN_ID" "$SEED" "$BIN" "$SHA" "$START" "$DIR" "$LOG" <<'PY'
import json, os, sys
p, run, seed, binp, sha, start, outdir, log = sys.argv[1:9]
json.dump({"run_id":run,"seed":int(seed),"binary_path":binp,"binary_sha256":sha,
 "binary_source_head":"43d1bb08","analysis_tool_head":os.popen("git -C %s rev-parse HEAD" % os.environ.get("WT",".")).read().strip(),
 "start_time":start,"launcher_pid":os.getpid(),"output_dir":outdir,"log":log,
 "status":"RUNNING"}, open(p,"w"), indent=1)
PY
cd "$WT" || exit 5
LSU_GEM5_BIN="$BIN" timeout --signal=INT --kill-after=120 "$((TIMEOUT+900))" \
  python3 "$WT/tools/lsu_campaign.py" \
  --matrix /home/sdc/gem5-fi-ding/runs/lsu/r6_matrix_325.csv \
  --outdir "$DIR" --cells "$RUN_ID" --phase trial --seed-start "$SEED" \
  --max-seeds-per-cell 1 --max-parallel 1 --timeout "$TIMEOUT" >>"$LOG" 2>&1
RC=$?; END=$(date -Iseconds); echo "$RC" > "$DIR/.exit_code"
python3 - "$DIR/manifest.json" "$END" "$RC" <<'PY'
import json,sys
p,end,rc=sys.argv[1],sys.argv[2],int(sys.argv[3]); d=json.load(open(p))
d.update({"end_time":end,"exit_code":rc,"status":"FINISHED" if rc==0 else "FAILED"})
json.dump(d,open(p,"w"),indent=1)
PY
touch "$DIR/.done"
echo "END $RUN_ID seed$SEED rc=$RC"
```

- [x] **Step 3: 运行 canary（前台，超时 1800s）**（rib=0；92 事件；注入真实）

```bash
chmod +x tools/r6_c_canary.sh
WT=$PWD tools/r6_c_canary.sh C01-F0-W6 1 1800
```

期望：`END C01-F0-W6 seed1 rc=0`，`.done` 存在。

- [x] **Step 4: 七项硬门禁核验**（结果：gzip/stats/注入 PASS；`admitted=False`、`terminal=provable_to_L4_then_unknown`、violations 含 `cross_branch_edge`）

```bash
D=/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary/C01-F0-W6_s1
find "$D" -name prop_evt.txt.gz -exec gzip -t {} \; && echo GZIP_OK
find "$D" -name stats.txt -size +0 -print
find "$D" -name chain_report.json -print
python3 - <<'PY'
import json,glob
p=glob.glob('/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary/C01-F0-W6_s1/**/chain_report.json',recursive=True)[0]
d=json.load(open(p))
for k in ('stream_present','truncated','event_count','terminal','provable_to','chain_valid','admitted','certified','oracle_outcome','exit_code'):
    print(k,'=',d.get(k))
print('faults =',len(d.get('faults') or []))
for f in (d.get('faults') or [])[:5]:
    print(' fault', {k:f.get(k) for k in ('fault_id','outcome','terminal','provable_to','activated')})
PY
grep -c 'Tick:' "$D"/*/*/cache_injections.log 2>/dev/null || echo NO_INJ_LOG
```

期望：GZIP_OK；stats>0；`event_count>0`；`admitted=True`、`certified=True`、`violations=[]`；`faults` 非空；`cache_injections.log` 有 `Tick:`。

- [x] **Step 5（决策点）: 若 canary 失败** — 命中类型 1：`errant_commit` 的 parent 落到 owner 请求分支（event 3），未接 taint_reg（event 8），导致 L4→L5 单链断裂。已定位 `CHAOSPropagation.cc` `noteCommit`，修复进行中；需重建 + 重跑 canary 验证。

按失败类型进入最小修复（先写失败测试，再修，再重建/重跑 canary）：
1. `prop_evt` 无 `inj` 事件但注入日志有 `Tick:` → C++ 传播模型问题（CHAOSCache 未调用 `chaos_chain` 记录 L0）。诊断 `CHAOS/gem5/src/mem/cache/CHAOSCache/`，补 L0 registration，`scons -j16 build/ARM/gem5.opt`，记录新 SHA，仅重跑受影响 RunID。
2. `chain_report` 缺失 → campaign 在 cache 分支未写报告，修 `lsu_campaign.py` 的 cache 分支。
3. `admitted=False` → 用 `tools/lsu_chain_check.py` 对原始流离线复判，区分真断链 vs 检查器缺口。

- [ ] **Step 6: 提交 canary 工具**

```bash
git add tools/r6_c_canary.sh
git commit -m "[LSU][C-UNIT][TOOLS] add C-unit canary launcher"
git push origin fix/r6-c-unit-20261102
```

---

### Task 2: C 单元证据读取与 Markdown 生成（cache 族泛化）

**Files:**
- Create: `tools/r6_c_evidence.py`
- Create: `tools/gen_r6_c_docs.py`
- Test: `tests/test_r6_c_evidence.py`

**Interfaces:**
- `r6_c_evidence.load_sample(seed_root)` → `dict`：`manifest/chain/events/kinds/census/sha`；复用 gzip 流解析与 `chain_report.json`，不复制 W1 的状态判据。
- `r6_c_evidence.CACHE_KIND_LAYER` / `CACHE_KIND_SEMANTICS`：cache 族事件层映射（`inj`→L0、`cache_access`/`set_way`→L1、`mem_req`/`fill`→L2、`cache_fill`/`cache_writeback`/`resp`→L3、`consumer`/`taint_reg`→L4、检测事件→L5）。
- `gen_r6_c_docs.generate(seed_root)` → Markdown 字符串；`--deploy` 才复制到 `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`。

- [ ] **Step 1: 写失败测试（用 canary 真实目录）**

`tests/test_r6_c_evidence.py`：

```python
import json, os, glob
import pytest
from tools import r6_c_evidence as ev

ROOT = "/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary/C01-F0-W6_s1"
pytestmark = pytest.mark.skipif(not os.path.isdir(ROOT), reason="canary absent")

def test_load_sample_has_chain_and_stream():
    s = ev.load_sample(ROOT)
    assert s["chain"]["stream_present"] is True
    assert s["chain"]["event_count"] > 0
    assert s["manifest"]["binary_sha256"].startswith("6db026e7")

def test_cache_kinds_are_mapped_to_layers():
    s = ev.load_sample(ROOT)
    for fault in s["chain"].get("faults") or []:
        for kind in (fault.get("edges") or {}):
            if kind.endswith("_witness"):
                continue
            assert kind in ev.CACHE_KIND_LAYER or kind in ev.GENERIC_KIND_LAYER, kind

def test_doc_contains_injection_and_verdict():
    from tools import gen_r6_c_docs as g
    s = ev.load_sample(ROOT)
    md = g.generate(s)
    assert s["chain"]["run_id"] in md
    assert "L0" in md and "注入" in md
    assert s["manifest"]["binary_sha256"] in md
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python3 -m pytest tests/test_r6_c_evidence.py -q`
Expected: FAIL（`ModuleNotFoundError: tools.r6_c_evidence`）。

- [ ] **Step 3: 实现 `tools/r6_c_evidence.py`**

要求：
- `discover_seeds(root)`：递归找 `manifest.json` + 其下 `<RUNID>/<seedN>/chain_report.json`，返回 `run_id/seed/seed_root`。
- `load_sample`：读取 manifest、chain_report、`seed*/prop_evt.txt.gz`（逐行 JSON）；统计 `kind` census 与全流 SHA-256；不推断 L 层。
- `CACHE_KIND_LAYER` 至少覆盖 `inj, cache_access, cache_return, cache_fill, cache_evict, cache_writeback, mem_req, resp, taint_reg, consumer, squash_discarded, errant_commit, store_not_retired, chain_end`。
- 未知名保留在 `GENERIC_KIND_LAYER` 回退，并在 census 标 `unmapped`（不静默）。

- [ ] **Step 4: 运行测试通过**

Run: `python3 -m pytest tests/test_r6_c_evidence.py -q`
Expected: 3 passed。

- [ ] **Step 5: 实现 `tools/gen_r6_c_docs.py`**

每份文档必须含：样本身份（RunID/seed/二进制 SHA/来源 head）、run 级判定（oracle、terminal、provable_to、admitted/certified）、逐 fault 注入清单（event_id/tick/site/field/bit/before→after）、逐 fault 规范路径（layer/kind/event_id/parent/tick/request_id/dyn_inst_seq/地址）、层边 witness、路径外生命周期事件、全流 kind census + SHA、stats/命令、诚实边界（`n/a` 显式）。

- [ ] **Step 6: 生成 canary 文档并人工核对**

```bash
python3 tools/gen_r6_c_docs.py --root /home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/canary --out /tmp/r6c_docs
sed -n '1,120p' /tmp/r6c_docs/C01-F0-W6/C01-F0-W6-seed1.md
```

Expected：完整、无 `—` 冒充真实层、地址缺失处写 `n/a`。

- [ ] **Step 7: 提交**

```bash
git add tools/r6_c_evidence.py tools/gen_r6_c_docs.py tests/test_r6_c_evidence.py
git commit -m "[LSU][C-UNIT][TOOLS] add cache-family evidence reader and doc generator"
git push origin fix/r6-c-unit-20261102
```

---

### Task 3: C 文档独立审计与索引更新器

**Files:**
- Create: `tools/audit_r6_c_docs.py`
- Create: `tools/update_r6_c_indexes.py`
- Test: `tests/test_r6_c_docs_audit.py`

**Interfaces:**
- `audit_r6_c_docs.audit(docs_root, evidence_root)` → `{"docs": N, "errors": [...], "ok": bool}`；逐条比文档声称的 event_id/tick/SHA 与原始流。
- `update_r6_c_indexes.update(docs_root, runs_root)` → 更新 `INDEX.md`/`INDEX.json`/`CATALOG.tsv`/`STATUS`/`README`，**在审计非全 PASS 时拒绝运行**。

- [ ] **Step 1: 写失败测试**

```python
import os, pytest
from tools import audit_r6_c_docs as a

def test_audit_detects_unknown_event_id(tmp_path):
    # 构造一份声称 event_id=999999 的最小文档 + 空证据，必须报错
    ...
```

（用 canary 真实文档 + 篡改一行做负控；正控 0 errors。）

- [ ] **Step 2: 运行确认失败** — `python3 -m pytest tests/test_r6_c_docs_audit.py -q` → FAIL。

- [ ] **Step 3: 实现审计器与索引器**，正控 canary 0 errors，负控（事件 id 改一位/哈希改一位）必报错。

- [ ] **Step 4: 运行通过并提交**

```bash
python3 -m pytest tests/test_r6_c_docs_audit.py -q
git add tools/audit_r6_c_docs.py tools/update_r6_c_indexes.py tests/test_r6_c_docs_audit.py
git commit -m "[LSU][C-UNIT][TOOLS] add C doc auditor and index updater"
git push origin fix/r6-c-unit-20261102
```

---

### Task 4: 单 seed 启动器与并行队列

**Files:**
- Create: `tools/r6_c_seed.sh`
- Create: `tools/r6_c_parallel.sh`
- Test: `tests/test_r6_c_parallel.py`

**Interfaces:**
- `r6_c_seed.sh <RUN_ID> <SEED> [timeout]`：独立输出目录 `runs/lsu/r6_c_unit/runs/<RUN_ID>_s<SEED>/`、独立 flock 锁、manifest 终态、`.done`、`.exit_code`；SHA 漂移即退出 7；锁冲突退出 3。
- `r6_c_parallel.sh`：读任务表（31×3），最多 `R6C_MAXJOBS`（默认 8）并发；门禁 MemAvailable/磁盘/swap/SHA；`--dry-run` 输出 `ALLOCATION_OK`。

- [ ] **Step 1: 写失败测试（假 launcher 自测）**

```python
def test_dry_run_allocates_93_unique(tmp_path):
    out = subprocess.run(["bash","tools/r6_c_parallel.sh","--dry-run"],capture_output=True,text=True)
    assert "ALLOCATION_OK" in out.stdout and "93 unique" in out.stdout
```

- [ ] **Step 2: 运行确认失败** → `python3 -m pytest tests/test_r6_c_parallel.py -q` FAIL。

- [ ] **Step 3: 实现启动器与队列**；修复 bash `set -u` 下空关联数组计数（沿用 `declare -A RUNNING=()` + `RUNNING_N`）；预置已合格 seed 不重跑。

- [ ] **Step 4: 验证**

```bash
bash -n tools/r6_c_seed.sh tools/r6_c_parallel.sh
python3 -m pytest tests/test_r6_c_parallel.py -q
bash tools/r6_c_parallel.sh --dry-run
```

Expected：`ALLOCATION_OK`；93 unique；无重复。

- [ ] **Step 5: 提交**

```bash
git add tools/r6_c_seed.sh tools/r6_c_parallel.sh tests/test_r6_c_parallel.py
git commit -m "[LSU][C-UNIT][TOOLS] add per-seed launcher and parallel queue"
git push origin fix/r6-c-unit-20261102
```

---

### Task 5: 执行 93 个 seed（无人值守）

**Files:**
- Output: `/home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/runs/`
- State: `/home/sdc/gem5-fi-ding-cleanup-20261029/R6C_STATE.json`

**Interfaces:**
- Consumes: Task 4 队列；canary 的 C01-F0-W6_s1 以 PRESEED 计入，不重跑。
- Produces: 93 个 `runs/<RUNID>_s<SEED>/` 目录。

- [ ] **Step 1: 预检与启动**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102
bash tools/r6_c_parallel.sh --dry-run        # 必须先 ALLOCATION_OK
tmux new-session -d -s r6c-parallel "bash tools/r6_c_parallel.sh"
```

- [ ] **Step 2: 周期性检查（每次只读简短状态，不 tail -f 大日志）**

```bash
ls /home/sdc/gem5-fi-ding/runs/lsu/r6_c_unit/runs/*/.done 2>/dev/null | wc -l
pgrep -fa 'gem5.opt' | wc -l
tail -n 5 /home/sdc/gem5-fi-ding-cleanup-20261029/r6c-parallel.log
```

- [ ] **Step 3: 失败处置**

每个非零 `.exit_code`：读 `run.err`/`run.out`，按 Global Constraints 的失败分类做最小修复；只重跑受影响 seed；不掩盖。

- [ ] **Step 4: 收口判定**

`R6C_PARALLEL_DONE` 存在且 93 个目录均有 `.done`；否则如实记录未完成项。

---

### Task 6: 证据审计 + EVENT_CAP 复判

**Files:**
- Create: `tools/audit_r6_c_evidence.py`
- Output: `/home/sdc/gem5-fi-ding-cleanup-20261029/R6C_EVIDENCE_AUDIT/`

- [ ] **Step 1: 对 93 个样本重算**：binary SHA、gzip EOF×2、stats>0、`admitted/certified/truncated/violations/conservation`、逐 fault ancestry 闭合、注入日志计数与 L0 事件数一致性。
- [ ] **Step 2: `truncated=True` 的样本** 用 gzip EOF + 全流事件数与 `EVENT_CAP` 对比；确认是分析上限后用 cap=n+1 复判，备份原件、记录口径与 SHA。
- [ ] **Step 3: 零容忍**：任一 FAIL 先修复再继续；审计 JSONL 落盘。
- [ ] **Step 4: 提交审计工具与报告**

---

### Task 7: 生成并部署 93 份 Markdown

**Files:**
- Output: `/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`

- [ ] **Step 1: 生成到 staging** `runs/lsu/R6_C_UNIT_DOCS_STAGE/`。
- [ ] **Step 2: `audit_r6_c_docs.py` 全 PASS（0 errors）**。
- [ ] **Step 3: 原子部署**，部署后逐文件 SHA 与 staging 比对。
- [ ] **Step 4: 提交文档与索引（显式路径）。**

---

### Task 8: 索引与统计

- [ ] **Step 1:** 统计 C seed 文档数、COMPLETE_3_OF_3 数、CATALOG 行数。
- [ ] **Step 2:** 更新 `INDEX.md`、`INDEX.json`、`CATALOG.tsv`、`STATUS.md`、`RESULTS/README.md`、C 单元最终报告。
- [ ] **Step 3:** 断链检查 = 0：`python3 tools/update_r6_c_indexes.py --check`。
- [ ] **Step 4:** 提交。

---

### Task 9: 全量回归

- [ ] **Step 1:**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102
LSU_GEM5_BIN=/home/sdc/gem5-fi-ding-cleanup-20261029/binaries/gem5.opt-6db026e7 \
  python3 -m pytest tests -q --ignore=tests/test_lsu_r6_reconcile_realroot.py \
  > /home/sdc/gem5-fi-ding-cleanup-20261029/r6c-regression.log 2>&1
tail -n 5 /home/sdc/gem5-fi-ding-cleanup-20261029/r6c-regression.log
```

- [ ] **Step 2:** 与基线 `f1291067`（254 passed / 9 failed）逐名比对；**NEW FAIL 必须为 0**，否则修复后重跑。
- [ ] **Step 3:** 记录日志路径到计划与 STATUS。

---

### Task 10: 提交、推送、合并、部署

- [ ] **Step 1:** 检查工作树仅含本轮显式路径改动。
- [ ] **Step 2:** 推送分支；`git push origin fix/r6-c-unit-20261102`。
- [ ] **Step 3:** 在干净的 merge worktree 验证后，`git push origin fix/r6-c-unit-20261102:fi-ding`（仅快进；远端有新提交则先合并再验证，不 force）。
- [ ] **Step 4:** `git ls-remote` 复核 `origin/fi-ding` 指向本轮最终提交。
- [ ] **Step 5:** 权威主树 `runs/lsu/` 部署复核（文档/索引/断链），记录事实。

---

## Self-Review（计划自检）

- **Spec coverage:** 31 RunID × 3 seed（Task 5）→ 完整链（Task 2/6）→ 逐 seed MD（Task 7）→ 审计（Task 3/6）→ 索引（Task 8）→ 回归（Task 9）→ 合并部署（Task 10）。✅
- **Placeholder scan:** 每个任务给出真实命令/路径；Task 1/4 的代码块为可执行实现；Task 2/3 的测试给出断言，实现细节以接口约束列明。✅
- **Type consistency:** `load_sample` 返回键（`manifest/chain/events/kinds/census/sha`）在 Task 2/3/7 一致；`discover_seeds` 输出 `run_id/seed/seed_root` 与队列命名 `<RUNID>_s<SEED>` 一致。✅
- **Review Focus:** 五项风险均有对应任务/门禁（Task 1 step 5、Task 6 step 1-3、Task 2 step 3、Task 3 step 4、Task 5 step 3）。✅
