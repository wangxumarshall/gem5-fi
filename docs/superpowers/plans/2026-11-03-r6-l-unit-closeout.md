# R6-L（Load Queue）单元收口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 L 工作树保全已验证的 L03/checker 修复，定量诊断 25 个 NO_INJECTION seed，用“同负载有界重复”补足 eligible 供给，使 14 个 RunID × 3 seed = 42/42 全部合格，部署 42 份逐 seed 传播文档并完成状态/索引/回归/推送。

**Architecture:** 不改变 F0/F1/F2/F4 频率定义、注入字段/注入点/RunID 身份或原始证据。复用仓库既有的 `chaos_repeat.h`（workload 侧 argv[1] 有界重复）+ `lsu_proxy.py --chaos_repeat` + `lsu_campaign.py REPEAT_FACTOR/REPEAT_EVIDENCE` + `tools/lsu_repeat_census.py`（真实 census）机制，仅把该机制的路由扩展到 L 单元（L01/L02 addrpath、L03 lsqfwd），并为 W12 `sqlite_like` 增加同源 repeat 包装（repeat=1 输出逐字节不变）。所有新运行使用全新目录、独锁、manifest、真实 census 因子与 canary 门禁。

**Tech Stack:** gem5 v25.1.0.1（已构建二进制 `8f57313a…`，源文件与 L 工作树逐字节一致）、Python 3.11、bash、pytest、gzip/JSONL 证据。

**Spec:** 用户 2026-11-03 L 单元接续工作令（本会话首条消息）；`docs/gem5-fi/lsu/05-frequency-and-sampling.md`（F0–F6 定义）；`workloads/directed/chaos_repeat.h`（有界重复契约）；`tools/lsu_repeat_census.py`（R6-A4 census 方法）。

## Global Constraints

- 基线 `d69ae2884dc360db285f1256e0426e2663e2f34b`；分支 `fix/r6-l-unit-20261103`；不得合并 `fi-ding` 直到全部收口条件满足。
- 禁止：把 NO_INJECTION 计为合格；把 injected=0 改写为 Masked；伪造 inj/传播事件；缩短 F1/F2/F4 间隔；挑选 seed4+ 替换 seed1/2/3；放宽 admission/certification/conservation；修改原始证据。
- 不得重跑已合格的 17 个 seed（依赖审计：C++ diff 仅触及 `CHAOSLSQFwd` L03 与 `lsq_unit.cc` 调用点；L01/L02 走 CHAOSAddrPath，语义不受影响）。
- 有界重复上限：`CHAOS_REPEAT_MAX=131072`（workload）与 `CHAOS_REPEAT_CAP=131072`（config）；每样本墙钟预算 ≤3600 s；事件量以 `--chaos_repeat` 因子与 manifest 记录为准。
- 并发：gem5 最大 2（canary 稳定后最多 4）；构建时 gem5=0；MemAvailable <12 GiB 或 /home 可用 <30 GiB 时暂停；不得持续 tail 大日志。
- 每个 RunID+seed 独占锁；新目录必须写 manifest（完整命令、PID/PGID、binary SHA、source head、tool head、起止时间、exit_code、done 标记）。
- 提交纪律：一个逻辑单元一个 commit；只 stage 明确路径，禁止 `git add -A`；commit message 不得包含 `Co-Authored-By: Claude`。
- 诚实边界：`chain_end` 永不充当 L5；oracle 与链终局不一致时并列记录；`n/a` 不写成 0。

## Review Focus

- **重复后的 oracle 语义**：`sqlite_like` 每次重复必须重置页池，使每个 `ITER` 行都等于冻结 golden；若状态累积，campaign 的逐迭代 oracle 会把合法重复误判为 SDC。
- **F0 重复的抽样语义**：L03-F0-W5 seed3 的 `draw_next_fire=561` 是 eligible 序号空间中的固定阈值；重复只增加供给，不得改变 warmup/span/seed。
- **重复因子的真实标定**：必须用 `lsu_repeat_census.py` 实测 E1/delta，不得用整次流长 × N 推算。
- **二进制/源身份**：现有 42 个 run 存在三个二进制 SHA；最终状态必须逐 seed 记录真实 SHA，并证明 L01/L02 的旧 SHA 与新 SHA 在 addrpath 路径上语义等价。
- **文档证据一致性**：42 份 Markdown 的每个事件行必须能在该 seed 自己的 `prop_evt.txt.gz` 中找到；SHA 必须与原始文件一致；broken links=0。

---

## 已核实的基线事实（2026-11-03）

### 当前 42 个 run 的真实状态

| 状态 | 数量 | RunID |
|---|---|---|
| QUALIFIED | 17 | L01-F0-W12(3), L01-F0-W5(3), L02-F0-W12(3), L02-F0-W5(3), L03-F0-W12(3), L03-F0-W5(1,2) |
| NO_INJECTION | 25 | L01-F1-W12(3), L01-F1-W5(3), L01-F2-W12(3), L01-F2-W5(3), L02-F2-W12(3), L02-F2-W5(3), L03-F4-W12(3), L03-F4-W5(3), L03-F0-W5(3) |

### 25 个 NO_INJECTION 的只读定量诊断（已从 run.out 实测）

首火位公式（`chaos_lsu_trigger.hh::scheduleNext`，warmup=0）：
`first_fire = iv/2 + lcg(seed) % iv`，`iv(F1)=1,000,000`，`iv(F2)=iv(F4)=100,000`。

| RunID | seed | tier | attempted | eligible | first_fire | 差距 |
|---|---|---|---|---|---|---|
| L01-F1-W12 | 1/2/3 | F1 | 35773 | 11306 | 1256412 / 1049417 / 1290806 | 1245106 / 1038111 / 1279500 |
| L01-F1-W5 | 1/2/3 | F1 | 2572 | 1262 | 1256412 / 1049417 / 1290806 | 1255150 / 1048155 / 1289544 |
| L01-F2-W12 | 1/2/3 | F2 | 35773 | 11306 | 106412 / 99417 / 140806 | 95106 / 88111 / 129500 |
| L01-F2-W5 | 1/2/3 | F2 | 2572 | 1262 | 106412 / 99417 / 140806 | 105150 / 98155 / 139544 |
| L02-F2-W12 | 1/2/3 | F2 | 35773 | 11306 | 106412 / 99417 / 140806 | 95106 / 88111 / 129500 |
| L02-F2-W5 | 1/2/3 | F2 | 2572 | 1262 | 106412 / 99417 / 140806 | 105150 / 98155 / 139544 |
| L03-F4-W12 | 1/2/3 | F4 | 18681 | 18681 | 106412 / 99417 / 140806 | 87731 / 80736 / 122125 |
| L03-F4-W5 | 1/2/3 | F4 | 540 | 540 | 106412 / 99417 / 140806 | 105872 / 98877 / 140266 |
| L03-F0-W5 | 3 | F0 | 540 | 540 | draw_next_fire=561（span=571, warmup=1） | +21 |

结论：所有 25 个 seed 的 hook 都真实触发（attempted>0），tier 已挂载，计数器前进，无路由错误；`injected=0` 的唯一原因是工作负载 eligible 供给小于首火位。原始报告中的 `reason_no_fire` 与此表一致。

### 二进制身份

| SHA-256 | 使用该 SHA 的 seed |
|---|---|
| `105a246f3296458c59d49ba07a865312b2d685ef6018d54bf79a9efcdacc1be8` | 34 |
| `8f57313a22a89ffefd07b029c795133d5b9777847cffe65ea384e00d8d19c19a` | 6（全部 L03-F0） |
| `f0233ef14217a7cc995443f7558c17c18afac28002c62cf930fcf82c28447945` | 2（L01-F0-W5 s2、L02-F0-W5 s1） |

当前 C 工作树二进制 `8f57313a…`（2026-11-03 09:52 构建）与 L 工作树的 3 个 C++ 源文件逐字节一致；该二进制真实产出 L03 `inj(L0)+addr_form(L1)`、`stats.numFaultsInjected=1`。L01/L02 仅走 `CHAOSAddrPath`，不受 `CHAOSLSQFwd`/`lsq_unit.cc` 改动影响（依赖审计结论）。

---

## Task 1: 保全并提交已验证的 L03 注入登记 + stats 计数

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc:666-710`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh:118`
- Modify: `CHAOS/gem5/src/cpu/o3/lsq_unit.cc:648-651`
- Test: `tests/test_lsu_hook_sq.py`, `tests/test_lsu_chain_check.py`

**Interfaces:**
- Consumes: `CHAOSPropagation::instance()->registerInjection(site, seq, old_addr, new_addr, is_load, old_size, new_size)`
- Produces: L03 fault chain with `inj` (L0) + `addr_form` (L1) + `stats.numFaultsInjected` increment.

- [ ] **Step 1: 确认 C/L 工作树三个 C++ 源文件逐字节一致**

```bash
for f in CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc \
         CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh \
         CHAOS/gem5/src/cpu/o3/lsq_unit.cc; do
  cmp -s "/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102/$f" "$f" \
    && echo "IDENTICAL $f" || echo "DIFF $f"
done
```

Expected: 三行 `IDENTICAL`。

- [ ] **Step 2: 运行定向测试**

```bash
python3 -m pytest -q tests/test_lsu_hook_sq.py tests/test_lsu_chain_check.py
```

Expected: 全部通过（允许 `tests/test_lsu_freq_policy.py` 因 L 工作树无 `build/ARM/gem5.opt` 的既有环境失败，不在本组）。

- [ ] **Step 3: 引用真实功能证据（已存在的 L03 运行，不重跑）**

```bash
R=/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/runs
grep -E 'numFaultsInjected' $R/L03-F0-W5_s1/*/seed1/stats.txt
cat $R/L03-F0-W5_s1/*/seed1/*_injections.log
python3 -c "import json,glob;d=json.load(open(glob.glob('$R/L03-F0-W5_s1/*/seed1/chain_report.json')[0]));print(d['event_count'],d['terminal'],d['provable_to'],d['admitted'],d['certified'])"
```

Expected：`numFaultsInjected 1`；日志有 `Cycle: ..., Site: checkViolations_L03`；链报告 `3 injected_not_activated L1 True True`。

- [ ] **Step 4: 提交**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.cc \
        CHAOS/gem5/src/cpu/o3/CHAOSLSQFwd/CHAOSLSQFwd.hh \
        CHAOS/gem5/src/cpu/o3/lsq_unit.cc
git commit -m "[LSU][MDSPEC][R6-L-UNIT][CPP] register L03 violation-view injection and count it in stats"
```

---

## Task 2: 保全并提交 checker 的 LQ 翻译故障 crash 终局（L2）

**Files:**
- Modify: `tools/lsu_chain_check.py:497-505`
- Test: `tests/test_lsu_crash_translation_terminal.py`

**Interfaces:**
- Produces: `_crash_candidate_reason(events, family="lq", ...)` accepts a contiguous L0..L2 ancestry and returns `crash_translation_fault` at `provable_to="L2"`; other families keep the L3 requirement.

- [ ] **Step 1: 运行测试**

```bash
python3 -m pytest -q tests/test_lsu_crash_translation_terminal.py
```

Expected: PASS。

- [ ] **Step 2: 提交**

```bash
git add tools/lsu_chain_check.py
git commit -m "[LSU][MDSPEC][R6-L-UNIT][CHECK] accept LQ translation fault as L2 crash terminal"
```

---

## Task 3: 保全并提交 checker 的严格 injected_not_activated（L1 视图）+ stats 来源回退

**Files:**
- Modify: `tools/lsu_chain_check.py:782-895`
- Test: `tests/test_lsu_injected_not_activated.py`

**Interfaces:**
- Produces: `injected_not_activated_verdict(...)` returns `provable_to="L1"`, `subkind="latent_no_effect"`, `shape="L1"` for `[inj, addr_form(parent=inj, corr in _CHAIN_CORR)]`; falls back across `board.chaos_l1d`, `board.chaos_lsqfwd`, `board.chaos_addrpath`.

- [ ] **Step 1: 运行测试**

```bash
python3 -m pytest -q tests/test_lsu_injected_not_activated.py
```

Expected: PASS。

- [ ] **Step 2: 提交**

```bash
git add tools/lsu_chain_check.py
git commit -m "[LSU][MDSPEC][R6-L-UNIT][CHECK] certify strict L1 latent-no-effect view and lsqfwd stat source"
```

---

## Task 4: 提交 L 单元运行/收口脚本

**Files:**
- Create: `tools/r6_l_seed.sh`
- Create: `tools/r6_l_parallel.sh`
- Create: `tools/r6_l_finalize.py`

**Interfaces:**
- `r6_l_seed.sh <RUN_ID> <SEED> [timeout]` → one fresh dir + flock + manifest + `.done`.
- `r6_l_parallel.sh [--dry-run]` → 42-task queue, maxjobs default 2, gates.
- `r6_l_finalize.py --regrade --deploy` → strict offline qualification + docs.

- [ ] **Step 1: 语法/分配自检**

```bash
bash -n tools/r6_l_seed.sh && bash -n tools/r6_l_parallel.sh
python3 -m py_compile tools/r6_l_finalize.py
bash tools/r6_l_parallel.sh --dry-run
```

Expected: `tasks=42 unique=42 dup=0 new runids=14` 与 `ALLOCATION_OK`。

- [ ] **Step 2: 提交**

```bash
git add tools/r6_l_seed.sh tools/r6_l_parallel.sh tools/r6_l_finalize.py
git commit -m "[LSU][MDSPEC][R6-L-UNIT][TOOLS] add L seed launcher, parallel queue, and finalize"
```

---

## Task 5: 新增只读 NO_INJECTION 诊断工具与诊断报告

**Files:**
- Create: `tools/r6_l_no_injection_diagnosis.py`
- Create (repo doc): `docs/gem5-fi/lsu/evidence/R6-L-NO-INJECTION-DIAGNOSIS.md`
- Test: `tests/test_r6_l_no_injection_diagnosis.py`

**Interfaces:**
- Produces: for each NO_INJECTION seed dir: `{run_id, seed, tier, attempted, eligible, first_fire, draw_next_fire, gap, routing_ok, counter_advanced, tier_mounted, conclusion}`.
- Routing checks: manifest command contains the model's mount flag and the correct `--*_lsu_tier`; `attempted>0`; `eligible>0`; `injected==0`; no `BLOCKED` in campaign cell JSON.

- [ ] **Step 1: 写失败测试**

```python
def test_diagnosis_flags_supply_gap(tmp_path):
    from r6_l_no_injection_diagnosis import diagnose_seed
    rec = diagnose_seed("L01-F1-W5", 1, runs_root=REAL_RUNS)
    assert rec["tier"] == "F1"
    assert rec["injected"] == 0
    assert rec["attempted"] > 0 and rec["eligible"] > 0
    assert rec["first_fire"] == 1_256_412
    assert rec["gap"] == rec["first_fire"] - rec["eligible"]
    assert rec["routing_ok"] is True
    assert rec["conclusion"] == "workload-supply-insufficient"
```

- [ ] **Step 2: 实现工具（解析 run.out 的 `CHAOS_LSU_TRIGGER` 行 + LCG 重算 + manifest/command 检查；输出 JSONL + Markdown）**

- [ ] **Step 3: 运行测试与全量诊断**

```bash
python3 -m pytest -q tests/test_r6_l_no_injection_diagnosis.py
python3 tools/r6_l_no_injection_diagnosis.py \
  --runs-root /home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/runs \
  --out docs/gem5-fi/lsu/evidence/R6-L-NO-INJECTION-DIAGNOSIS.md
```

Expected: 25 seeds, 0 routing errors, 25 `workload-supply-insufficient`。

- [ ] **Step 4: 提交**

```bash
git add tools/r6_l_no_injection_diagnosis.py tests/test_r6_l_no_injection_diagnosis.py \
        docs/gem5-fi/lsu/evidence/R6-L-NO-INJECTION-DIAGNOSIS.md
git commit -m "[LSU][MDSPEC][R6-L-UNIT][DIAG] quantify 25 no-injection seeds as workload supply gaps"
```

---

## Task 6: 把有界重复路由扩展到 L 模型（L01/L02/L03）

**Files:**
- Modify: `tools/lsu_campaign.py:2125-2165`（repeat routing condition）
- Modify: `tools/lsu_campaign.py:1167-1200`（REPEAT_FACTOR header + L entries placeholder is NOT allowed; entries land in Task 9 with census data）
- Create: `tests/test_lsu_l_repeat.py`

**Interfaces:**
- Consumes: `REPEAT_FACTOR[(model, freq, binary, submodel)]`, `REPEAT_MAX`.
- Produces: `resolve_cell(cell, seed=N)` appends `--chaos_repeat R` for L01/L02 addrpath F1/F2/F4 and L03 lsqfwd F4/F0 when a factor exists; refuses loudly when unmeasured; `L_F0_REPEAT[(model, binary, seed)]` supplies the per-seed F0 factor (Task 9).

- [ ] **Step 1: 写失败测试**

```python
def test_l01_f1_w5_gets_repeat_flag():
    flags, golden, binary = C.resolve_cell(cell("L01-F1-W5"), seed=1)
    assert "--chaos_repeat" in flags
    assert int(flags[flags.index("--chaos_repeat") + 1]) == C.REPEAT_FACTOR[
        ("L01", "F1", "sq_forward", "")]

def test_l03_f0_w5_seed3_gets_seed_keyed_repeat():
    flags, _, _ = C.resolve_cell(cell("L03-F0-W5"), seed=3)
    assert flags[flags.index("--chaos_repeat") + 1] == str(
        C.L_F0_REPEAT[("L03", "sq_forward", 3)])

def test_l_unmeasured_repeat_refuses_loudly(monkeypatch):
    monkeypatch.delitem(C.REPEAT_FACTOR, ("L01", "F2", "sqlite_like", ""))
    flags, golden, _ = C.resolve_cell(cell("L01-F2-W12"), seed=1)
    assert flags is None and "repeat-factor-unmeasured" in golden
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python3 -m pytest -q tests/test_lsu_l_repeat.py
```

Expected: FAIL（当前 L 模型不追加 repeat）。

- [ ] **Step 3: 最小实现**

```python
L_REPEAT_MODELS = frozenset({"L01", "L02", "L03"})
L_F0_REPEAT = {}   # (model, binary, seed) -> repeat; filled by Task 9 census

def _l_repeat_applies(family, model, freq):
    return (model in L_REPEAT_MODELS and freq in ("F1", "F2", "F4")) or (
        model == "L03" and freq == "F0")
```

在 `resolve_cell` 中把原条件
`if family == "addrpath" and model.startswith("A") and freq in ("F1","F2","F4"):`
替换为 `if _l_repeat_applies(family, model, freq):`，并对 F0 分支使用
`L_F0_REPEAT.get((model, binary, seed))`（未登记则响亮 BLOCKED）。

- [ ] **Step 4: 运行测试确认通过（本任务先临时注入测试用因子，Task 9 落地真实值后移除）**

```bash
python3 -m pytest -q tests/test_lsu_l_repeat.py
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add tools/lsu_campaign.py tests/test_lsu_l_repeat.py
git commit -m "[LSU][MDSPEC][R6-L-UNIT][CAMPAIGN] route bounded repeat to L models"
```

---

## Task 7: 为 W12 `sqlite_like` 增加同源有界重复载体

**Files:**
- Modify: `workloads/directed/sqlite_like.c`
- Test: `tests/test_r6_l_sqlite_repeat.py`

**Interfaces:**
- Consumes: `chaos_repeat.h` (`chaos_repeat_count`, `chaos_emit_iter`).
- Produces: `sqlite_like [reps]`; `reps==1` prints only the bare 16-hex checksum (byte-identical to the frozen golden `33f836327a416d35`); `reps>1` prints `ITER:<n>:<checksum>` per iteration then the bare final checksum; every iteration resets `pages/meta` and runs the identical step 1–8 sequence.

- [ ] **Step 1: 写失败测试（native 侧）**

```python
def test_sqlite_repeat_golden(tmp_path):
    run = subprocess.run([str(REPO/"workloads/directed/sqlite_like"), "5"],
                         capture_output=True, text=True)
    lines = run.stdout.strip().splitlines()
    assert lines[-1] == GOLDEN_SQLITE
    iters = [l for l in lines if l.startswith("ITER:")]
    assert len(iters) == 5
    assert all(l.split(":")[2] == GOLDEN_SQLITE for l in iters)
```

- [ ] **Step 2: 运行测试确认失败**

```bash
python3 -m pytest -q tests/test_r6_l_sqlite_repeat.py
```

Expected: FAIL（当前二进制忽略 argv）。

- [ ] **Step 3: 实现**

把 `main` 的步骤 1–8 移入 `static unsigned long probe_once(void)`，函数开头重置
`pages/meta`（`memset(pages,0,sizeof pages); memset(meta,0,sizeof meta);`），
`main` 改为：

```c
int main(int argc, char **argv) {
    int reps = chaos_repeat_count(argc, argv);
    unsigned long acc = 0;
    for (int r = 0; r < reps; ++r) {
        acc = probe_once();
        if (reps > 1) chaos_emit_iter(r, acc);
    }
    put_hex(acc);
    return 0;
}
```

- [ ] **Step 4: 重建并验证 repeat=1 与多重复**

```bash
gcc -O2 -static -o workloads/directed/sqlite_like workloads/directed/sqlite_like.c
./workloads/directed/sqlite_like              # expect 33f836327a416d35
./workloads/directed/sqlite_like 5            # expect 5 ITER lines all 33f836327a416d35 + final
```

Expected: 与上一致。

- [ ] **Step 5: gem5 侧 quick canary（1 个 seed，repeat=2）**

```bash
build/ARM/gem5.opt --outdir=/tmp/r6l-sqlite-repeat-check \
  configs/se/lsu_proxy.py --cmd workloads/directed/sqlite_like --cpu O3 \
  --chaos_addrpath --addrpath_lsu_tier F2 --addrpath_warmup_events 0 \
  --addrpath_span_events 1000 --agu_pre_mode l01_load_addr --addrpath_rng_seed 1 \
  --chaos_repeat 2
```

Expected: run.out 有 2 条 `ITER:` 行且都等于 golden；无 gzip 证据要求（本步只验证 oracle）。

- [ ] **Step 6: 提交**

```bash
git add workloads/directed/sqlite_like.c sources tests/test_r6_l_sqlite_repeat.py
git commit -m "[LSU][MDSPEC][R6-L-UNIT][WORKLOAD] add bounded same-source repeat to sqlite_like"
```

（`workloads/directed/sqlite_like` ELF 若被 .gitignore 忽略，只提交 `.c` 与测试；manifest 记录 ELF SHA。）

---

## Task 8: 把 repeat census 泛化到 L tier/键并实测 E1/delta

**Files:**
- Modify: `tools/lsu_repeat_census.py`（`_k`/`cell_for`/`analyse_key` 接受 tier；新增 `L_CENSUS_KEYS`）
- Create: `tests/test_lsu_l_repeat_census.py`
- Evidence: `/home/sdc/gem5-fi-ding/runs/lsu/r6_l_census_20261103/summary.json`

**Interfaces:**
- `_k(key, runid, model, workload, binary, seed, tier="F2")`
- `build_command(rec, repeat, ...)` 使用 `rec["tier"]`；no-fire warmup 对 addrpath 与 lsqfwd 分别覆盖正确旗标。
- `analyse_key` 用 `rec["tier"]` 计算 `first_fire`/`max_first_fire`。

- [ ] **Step 1: 写失败测试（首火位与键解析）**

```python
def test_l_key_tiers():
    from lsu_repeat_census import first_fire, L_CENSUS_KEYS
    assert first_fire("F1", 1) == 1256412
    assert first_fire("F4", 3) == 140806
    keys = {k["key"]: k for k in L_CENSUS_KEYS}
    assert keys["L01-F1-W5"]["tier"] == "F1"
    assert keys["L03-F4-W12"]["binary"] == "sqlite_like"
```

- [ ] **Step 2: 运行确认失败，随后实现**

- [ ] **Step 3: 真实 census（并发 2，后台 detached；不 tail）**

```bash
mkdir -p /home/sdc/gem5-fi-ding-cleanup-20261029/r6l-census-logs
setsid nohup env LSU_FROZEN_SHA=8f57313a22a89ffefd07b029c795133d5b9777847cffe65ea384e00d8d19c19a \
  LSU_GEM5_BIN=/home/sdc/gem5-fi-ding/.claude/worktrees/r6-c-unit-20261102/CHAOS/gem5/build/ARM/gem5.opt \
  LSU_CENSUS_OUTROOT=/home/sdc/gem5-fi-ding/runs/lsu/r6_l_census_20261103 \
  python3 tools/lsu_repeat_census.py --l-unit --repeats 1,5,10 --jobs 2 --verify \
  > /home/sdc/gem5-fi-ding-cleanup-20261029/r6l-census-logs/census.log 2>&1 &
echo $! > /home/sdc/gem5-fi-ding-cleanup-20261029/r6l-census-logs/census.pid
```

Expected（完成后读取 summary.json）：9 个键（8 个 interval 键 + L03-F0-W5 seed3），每键 `E1/eligible@5/delta/R` 齐全；`verify.injected>=1`；`R<=131072`。

- [ ] **Step 4: 记录真实输出并提交**

```bash
git add tools/lsu_repeat_census.py tests/test_lsu_l_repeat_census.py
git commit -m "[LSU][MDSPEC][R6-L-UNIT][CENSUS] generalize repeat census to L tiers and keys"
```

---

## Task 9: 落盘 L 重复因子与证据，并跑 4 类代表 canary

**Files:**
- Modify: `tools/lsu_campaign.py`（`REPEAT_FACTOR` + `REPEAT_EVIDENCE` + `L_F0_REPEAT`）
- Create: `docs/gem5-fi/lsu/evidence/R6-L-REPEAT-CENSUS.md`
- Evidence: `/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/canary_20261103/`

**Interfaces:**
- Consumes: Task 8 `summary.json` 的真实 E1/delta/R。
- Produces: 生产路径可解析的 L 因子；canary 通过后才允许批量重跑。

- [ ] **Step 1: 写入真实因子（数值取自 summary.json，逐项引用 census 目录）**

示例形状（最终数值以 census 为准）：

```python
REPEAT_FACTOR.update({
    ("L01", "F1", "sq_forward", ""): <R_F1_W5>,
    ("L01", "F1", "sqlite_like", ""): <R_F1_W12>,
    ("L01", "F2", "sq_forward", ""): <R_F2_W5>,
    ("L01", "F2", "sqlite_like", ""): <R_F2_W12>,
    ("L02", "F2", "sq_forward", ""): <R_F2_W5_L02>,
    ("L02", "F2", "sqlite_like", ""): <R_F2_W12_L02>,
    ("L03", "F4", "sq_forward", ""): <R_F4_W5>,
    ("L03", "F4", "sqlite_like", ""): <R_F4_W12>,
})
L_F0_REPEAT[("L03", "sq_forward", 3)] = <R_F0_SEED3>  # draw=561, E1=540
```

- [ ] **Step 2: canary 运行（4 个代表，独占目录+锁，gem5 并发 1）**

```bash
R6L_MAXJOBS=1 R6L_OUTROOT=/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/canary_20261103 \
R6L_LOCKROOT=/home/sdc/gem5-fi-ding-cleanup-20261029/r6l_canary_locks \
  bash tools/r6_l_parallel.sh --runids L01-F1-W5,L01-F2-W12,L03-F4-W5,L03-F0-W5
```

（若脚本没有 `--runids`，先用 `R6L_RUNIDS=...` 环境变量；F2 代表可选 L02-F2-W5 作第二确认。）

- [ ] **Step 3: canary 验收（每个 seed 必须全部满足）**

```bash
python3 tools/r6_l_finalize.py --root <canary_root> --regrade
```

逐项核对：`injected=1`；log/stream/stats 三方一致；`gzip.open().read()` EOF 正常；
`simTicks>0` 且 `numFaultsInjected>=1`；terminal 为 `full` / 真实 `crash_*` /
严格 `injected_not_activated`；`admitted=True`、`certified=True`、`violations=[]`、
`conservation=OK`；campaign/checker/auditor 一致；运行前后二进制 SHA 不漂移。

- [ ] **Step 4: 提交因子与 canary 报告**

```bash
git add tools/lsu_campaign.py docs/gem5-fi/lsu/evidence/R6-L-REPEAT-CENSUS.md
git commit -m "[LSU][MDSPEC][R6-L-UNIT][CENSUS] land measured L repeat factors and canary proof"
```

---

## Task 10: 重跑 25 个 NO_INJECTION seed（全新目录，保留旧证据）

**Files:**
- Evidence: `/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/runs_repeat_20261103/`
- Preserve: `/home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/runs/`（不移动、不删除；在状态中标注 superseded）

**Interfaces:**
- Consumes: Task 9 的因子；`tools/r6_l_seed.sh`。
- Produces: 25 个新 seed 目录，每个含 `.done`、`.exit_code`、`manifest.json`（含 repeat 因子/原 workload/eligible 目标/实际 eligible/触发位置/退出原因）。

- [ ] **Step 1: 扩展 `r6_l_seed.sh` manifest（若尚未记录 repeat）**

在 `manifest.json` 增加：`repeat_factor`、`original_workload`、`eligible_target`、
`actual_eligible`、`first_fire`、`exit_reason`、`process_group_id`、`source_file_sha256`。

- [ ] **Step 2: dry-run 分配（25 个，无重复）**

```bash
R6L_RUNIDS="<25 RunID 列表去掉 8 个 RunID 的已合格 seed>" \
R6L_MAXJOBS=2 R6L_OUTROOT=.../runs_repeat_20261103 bash tools/r6_l_parallel.sh --dry-run
```

Expected: `tasks=25 unique=25 dup=0 ALLOCATION_OK`。

- [ ] **Step 3: detached 启动（先 2 并发；canary 稳定后最多 4）**

```bash
setsid nohup env R6L_MAXJOBS=2 R6L_OUTROOT=.../runs_repeat_20261103 \
  R6L_LOCKROOT=/home/sdc/gem5-fi-ding-cleanup-20261029/r6l_locks_repeat \
  R6L_WANT_SHA=8f57313a... bash tools/r6_l_parallel.sh \
  > /home/sdc/gem5-fi-ding-cleanup-20261029/r6l-repeat-parallel.log 2>&1 &
echo $! > /home/sdc/gem5-fi-ding-cleanup-20261029/r6l-repeat-parallel.pid
```

- [ ] **Step 4: 重连检查（不 tail）**

```bash
# 只查 PID / PGID / 锁 / .done 计数 / 门禁
ps -o pid,pgid,etime,cmd -p $(cat .../r6l-repeat-parallel.pid)
find .../runs_repeat_20261103 -name .done | wc -l
awk '/MemAvailable/{print int($2/1024)" GiB"}' /proc/meminfo
df -Pk /home | awk 'NR==2{print int($4/1024/1024)" GiB"}'
```

Expected: 25 个 `.done`，rc 全 0，SHA 不漂移。

- [ ] **Step 5: 全量严格重判**

```bash
python3 tools/r6_l_finalize.py --roots .../runs,.../runs_repeat_20261103 --audit-only
```

Expected: `seeds=42 qualified=42 no_injection=0 not_qualified=0`。

---

## Task 11: 扩展 finalize/文档生成并部署 42 份逐 seed Markdown

**Files:**
- Modify: `tools/r6_l_finalize.py`（多 root、repeat 元数据、更丰富的事件/证据/边界段）
- Deploy: `/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`

**Interfaces:**
- `--roots a,b` 合并两个证据根；同一 (run_id, seed) 出现两次时以新根为准并记录 superseded。
- `doc()` 增加：workload 原始名 + repeat 因子；eligible 目标/实际/首次触发位置/退出原因；
  逐 event 的 `event_id/parent/tick/kind`；VA/PA/PFN/地址来源；load seq/请求身份；
  翻译、LQ、cache/MSHR、寄存器/提交经过；crash/containment/masked/latent 表现；
  原始流 SHA；gzip/stats/conservation/admission/certification；诚实边界。

- [ ] **Step 1: 生成到 stage 并逐份人工抽检 4 份（每个 tier 一份）**

```bash
python3 tools/r6_l_finalize.py --roots .../runs,.../runs_repeat_20261103 \
  --stage /home/sdc/gem5-fi-ding-cleanup-20261029/R6L_DOCS_STAGE_20261103
ls /home/sdc/gem5-fi-ding-cleanup-20261029/R6L_DOCS_STAGE_20261103/*/*.md | wc -l
```

Expected: 42。

- [ ] **Step 2: 部署**

```bash
python3 tools/r6_l_finalize.py --roots ... --deploy
```

Expected: `R6_COMPLETE_PROPAGATION_PATHS/L01..L03/*` 共 42 份，SHA 与 stage 一致。

- [ ] **Step 3: 提交工具改动**

```bash
git add tools/r6_l_finalize.py
git commit -m "[LSU][MDSPEC][R6-L-UNIT][TOOLS] finalize 42 L seeds with repeat provenance"
```

---

## Task 12: 独立审计 42 份文档与原始证据

**Files:**
- Create: `tests/test_lsu_l_prop_docs.py`
- Create: `tools/r6_l_docs_audit.py`

**Interfaces:**
- 对每份 doc：RunID/seed 归属正确；每行事件能在该 seed 的 `prop_evt.txt.gz` 找到；
  parent 存在且 tick 不晚于子事件；终局与 `chain_report.json` 一致；
  SHA-256 与原始文件一致；无 broken link；`chain_end` 未被当作 L5。

- [ ] **Step 1: 写审计并运行**

```bash
python3 -m pytest -q tests/test_lsu_l_prop_docs.py
python3 tools/r6_l_docs_audit.py --docs /home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS \
  --runids L01,L02,L03 --out /home/sdc/gem5-fi-ding/runs/lsu/r6_l_unit/R6L_DOCS_AUDIT.json
```

Expected: `docs=42 broken_links=0 mismatches=0`。

- [ ] **Step 2: 提交**

```bash
git add tests/test_lsu_l_prop_docs.py tools/r6_l_docs_audit.py
git commit -m "[LSU][MDSPEC][R6-L-UNIT][AUDIT] independently verify 42 L propagation docs"
```

---

## Task 13: 更新状态、最终报告、CATALOG/EVIDENCE/INDEX

**Files:**
- Modify: `/home/sdc/gem5-fi-ding/runs/lsu/RESULTS/STATUS/R6-L-UNIT-STATUS.json`
- Modify: `/home/sdc/gem5-fi-ding/runs/lsu/r6_reports/R6-L-UNIT-FINAL-REPORT.md`
- Modify: `/home/sdc/gem5-fi-ding/runs/lsu/RESULTS/CATALOG.tsv`
- Modify: `/home/sdc/gem5-fi-ding/runs/lsu/R6-AUTHORITATIVE-EVIDENCE.{json,md}`
- Modify: `/home/sdc/gem5-fi-ding/runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/INDEX.{json,md}`

**Interfaces:**
- 状态必须区分“原 17 份（旧 SHA，superseded 证据保留）+ 新 25 份（repeat 因子与 SHA）”，
  逐 seed 记录 binary_sha256 / repeat_factor / terminal / provable_to / admitted / certified / doc 路径。

- [ ] **Step 1: 生成状态（不手写数字，全部从 finalize 审计 JSON 汇总）**

```bash
python3 tools/r6_l_finalize.py --roots ... --status-out .../R6-L-UNIT-STATUS.json
```

Expected: `qualified_seeds=42, no_injection_seeds=0, complete_3_of_3` 含全部 14 个 RunID。

- [ ] **Step 2: 更新报告与索引（RunID × seed 表、42 份文档路径、census/canary/审计引用、诚实边界）**

- [ ] **Step 3: 一致性检查**

```bash
python3 - <<'PY'
import json
s=json.load(open('/home/sdc/gem5-fi-ding/runs/lsu/RESULTS/STATUS/R6-L-UNIT-STATUS.json'))
assert s['qualified_seeds']==42 and s['no_injection_seeds']==0
assert len(s['complete_3_of_3'])==14
print('STATUS OK', s['qualified_seeds'], len(s['complete_3_of_3']))
PY
```

- [ ] **Step 4: 提交（仓库内文档与工具；runs/ 证据按仓库惯例不入 git）**

```bash
git add docs/gem5-fi/lsu/evidence/... 2>/dev/null || true
git commit -m "[LSU][MDSPEC][R6-L-UNIT][DOCS] record 42/42 L-unit closeout"
```

---

## Task 14: 完整回归、推送分支、快进 fi-ding、复核远端

**Files:**
- Log: `/home/sdc/gem5-fi-ding-cleanup-20261029/r6l-regression-final.log`

- [ ] **Step 1: 完整回归（预计 240 s）**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-l-unit-20261103
python3 -m pytest -q > /home/sdc/gem5-fi-ding-cleanup-20261029/r6l-regression-final.log 2>&1
tail -3 /home/sdc/gem5-fi-ding-cleanup-20261029/r6l-regression-final.log
grep -E '^FAILED' /home/sdc/gem5-fi-ding-cleanup-20261029/r6l-regression-final.log
```

Expected: 与基线逐名一致（`test_real_run_injects_at_R_with_three_way_count_consistency`
+ 8 个 `test_lsu_s_prop_docs.py`），NEW FAIL=0。

- [ ] **Step 2: 推送分支**

```bash
git push origin fix/r6-l-unit-20261103
```

- [ ] **Step 3: 确认可快进后推送 fi-ding**

```bash
git fetch origin fi-ding
git merge-base --is-ancestor origin/fi-ding HEAD && echo FAST_FORWARD_OK
git push origin HEAD:fi-ding
```

- [ ] **Step 4: 复核远端 SHA**

```bash
git ls-remote origin refs/heads/fi-ding refs/heads/fix/r6-l-unit-20261103
git rev-parse HEAD
```

Expected: 远端 `fi-ding` == 本地 HEAD；分支 SHA 一致。

- [ ] **Step 5: 停止并汇报（不启动 O/P 单元）**

---

## 最终验收清单

- [ ] 14/14 RunID 达到 3/3。
- [ ] 42/42 seed qualified；NO_INJECTION=0。
- [ ] 42/42 Markdown 已部署并通过独立审计；broken links=0。
- [ ] 回归 NEW FAIL=0；二进制 SHA 前后不漂移。
- [ ] 原始证据未修改（旧目录保留并标注 superseded）。
- [ ] 状态表、CATALOG、EVIDENCE、INDEX 与报告一致。
- [ ] 分支与 `origin/fi-ding` 已推送，远端 SHA 复核一致。
