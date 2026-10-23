# R6-GATE-B report — LSU formal-admission HARD GATE (Agent B)

- Worktree: `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-gate` (branch `r6-gate`,
  base `lsu-mdspec-20261019` @ `97f74786`)
- Commits (pushed to `origin/r6-gate`):
  - `9a7da7cf` `[R6-GATE] check_admission hard gate: activated sample READY requires full chain or explicit containment`
  - `ec75cdb1` `[R6-GATE] ready_contract READY now requires chain admission (hard gate)`
  - `5a8841db` `[R6-GATE] regenerate contract under the chain gate: READY 241->0, BLOCKED 84->325`
  - (this report) `[R6-GATE] R6-GATE-B report`
- Plan: `docs/superpowers/plans/2026-10-23-r6-gate-b-admission-hard-gate.md`

## Files changed

| File | Change |
|---|---|
| `tools/lsu_chain_check.py` | **new** `check_admission(bundle)` + `GATE_VIOLATIONS`, `MANDATORY_METRICS`, splice/request/time detectors (additive; `check_chain` unchanged) |
| `tools/lsu_ready_contract.py` | `chain_admission()` per-RunID gate; `build_contract(..., pilots, evidence_root)`; READY requires admission; new categories; `chain` per-row record + `chain_gate` summary |
| `tools/lsu_blocked_triage.py` | two new categories in the single classifier (`CONTRACT_CATS`/`CLASS_ORDER`) + evidence-gate mechanism text |
| `tests/test_lsu_chain_check.py` | new section `[12]` — the gate RED→GREEN cases |
| `tests/test_lsu_ready_contract_gate.py` | **new** — contract-level gate RED→GREEN |
| `tests/test_lsu_ready_contract_category.py`, `_verdict.py` | updated to the gated contract |
| `docs/gem5-fi/lsu/mdspec/ready_contract.json` / `.md`, `blocked_triage.md`, `blockers_for_approval.md` | regenerated |

Ownership respected: no C++ file, `lsu_campaign.py`, `lsu_runid_map.py`,
`lsu_coverage_matrix.py`, `lsu_prop_fields.py`, `lsu_audit.py` touched.

## The gate (what READY now means)

`check_admission(bundle)` is a pure function over one *activated* PROP-EVT sample
(`bundle = {run_id, activated, events, [rc], [oracle_outcome], [containment]}`).
An activated sample is `admitted` **only if** option (1) a family-specific
COMPLETE L0→L5 chain on one parent-event DAG, or option (2) propagation stopped
with an explicit containment layer + reason + per-layer metrics and every later
layer `N/A(contained)`. It fails LOUDLY with a named token for each forbidden
outcome:

`unknown_in_activated_chain`, `tlb_l1_faked_by_cache_access`, `tlb_l1_missing`,
`cross_branch_edge`, `cross_request_edge`, `time_reversed_edge`,
`ready_by_activated_only`, `ready_by_rc0`, `ready_by_chain_end_only`,
`missing_mandatory_metric`, `contained_without_later_na`,
`no_closed_chain_and_no_containment`.

`ready_contract.build_contract` calls it per RunID (over that RunID's
`pilot_evidence.json` PROP-EVT samples, first-fault chains, event cap 4000).
Non-admitted covered rows become `BLOCKED` with `CHAIN-UNPROVEN` (evidence
present, chain bad) or `CHAIN-EVIDENCE-MISSING` (no evidence / unreachable);
`why` names the RunID and the rule tokens.

## Per-rule RED → GREEN evidence (real output)

### Unit A — gate function (in `tests/test_lsu_chain_check.py`)

RED (before `check_admission` existed):

```
[12] R6-GATE hard-admission gate（activated 样本 READY 判定的硬门）
Traceback (most recent call last):
  File ".../tests/test_lsu_chain_check.py", line 358, in main
    good = adm(full_chain)
  File ".../tests/test_lsu_chain_check.py", line 355, in adm
    return CC.check_admission(bundle)
AttributeError: module 'lsu_chain_check' has no attribute 'check_admission'
```

GREEN (`python3 tests/test_lsu_chain_check.py`):

```
[12] R6-GATE hard-admission gate（activated 样本 READY 判定的硬门）
  PASS full 链 admitted=True（对照组）
  PASS full 链 path=full_chain
  PASS Unknown activated 样本被拒（unknown_in_activated_chain）
  PASS TLB L1 被 cache_access 冒充被拒
  PASS 跨分支拼接被拒（cross_branch_edge）
  PASS 跨请求拼接被拒（cross_request_edge）
  PASS 时间倒挂拼接被拒（time_reversed_edge）
  PASS READY-by-activated-only 被拒
  PASS READY-by-RC0 被拒
  PASS READY-by-chain_end-only 被拒
  PASS 缺逐层必录指标被拒（missing_mandatory_metric）
  PASS containment 路径 admitted=True
  PASS containment path=contained
  PASS containment 后续层未全 N/A 被拒（contained_without_later_na）

ALL PASS
```

### Unit B — contract wiring (in `tests/test_lsu_ready_contract_gate.py`)

RED:

```
PASS check_admission 可导入
FAIL chain_admission 可导入   <-
Traceback (most recent call last):
  ...
TypeError: build_contract() got an unexpected keyword argument 'pilots'
```

GREEN:

```
PASS check_admission 可导入
PASS chain_admission 可导入
PASS 完整链 RunID 保持 READY
PASS 无真链的 RunID 降为 BLOCKED（RED→GREEN 核心）
PASS 降级理由响亮点名 RunID 与违规规则
PASS 无链证据 → BLOCKED/CHAIN-EVIDENCE-MISSING
PASS 计数自洽

ALL PASS
```

The RED→GREEN core in one line (real `why` from the downgraded row):

```
A04-F0-W3 链未准入（违规规则 ['no_closed_chain_and_no_containment',
'ready_by_activated_only', 'ready_by_rc0']）: no_closed_chain_and_no_containment:
A04-F0-W3 既无 family-specific L0→L5 完整链，也无显式 containment——不得判 READY ; ...
```

## New contract numbers (honest)

```
[ready_contract] total=325 READY=0 PARTIAL=0 BLOCKED=325 self_consistent=True
[ready_contract] blocked_by_category={'CHAIN-UNPROVEN': 43, 'CHAIN-EVIDENCE-MISSING': 198,
  'RULING': 6, 'FS-INFRA': 24, 'MODE-UNIMPL': 3, 'UNRESOLVED': 4, 'FS-MULTICORE': 35, 'LICENSE': 12}
[ready_contract] chain_gate admitted=0 unproven=43 evidence_missing=198
  root=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019
[verdict] NO-GO
```

- **READY 241 → 0; BLOCKED 84 → 325** (self-consistent). This drop is CORRECT and
  expected: the old READY rested on coverage PASS (= the unit's node *kinds* were
  once observed), which is exactly the basis the mission forbids. No row has an
  admissible chain.
- Of the 43 RunIDs that *do* have pilot PROP-EVT, `chain_admission` evaluated
  them all and admitted **0**. Evidence: 124 `no_closed_chain_and_no_containment`
  + `ready_by_activated_only` + `ready_by_rc0`, 59 `ready_by_chain_end_only`,
  10 `chain_evidence_too_large`. Their chains stop at L4 with `beyond=Unknown`
  (e.g. `A04-F0-W3` → `provable_to_L4_then_unknown`, `A01-F0-W3` →
  `detected_translation_outcome_pending`) — never a family-specific L0→L5 full
  chain, never an option-2 containment record. Under the mission's rule ("any
  `Unknown` in an activated sample" is forbidden, READY needs a real chain) these
  cannot be READY.
- The other 198 RunIDs have **no pilot PROP-EVT recorded** in
  `pilot_evidence.json` at all → `CHAIN-EVIDENCE-MISSING` (chain not provable;
  no silent pass).

Two evidence roots were tried and give the **same category census** (43/198):
the default `REPO` and the base worktree that actually holds the untracked
`runs/lsu/mdspec_pilot` PROP-EVT. The committed contract records the base-worktree
root because only there do the 43 rows carry real rule detail instead of
`chain_evidence_missing`.

## Full-suite result (real)

```
$ python3 tools/lsu_test_runner.py
[lsu_test_runner] suites=53 ENV=5 FAIL=13 PASS=34 SKIP=1
[lsu_test_runner] DISCLOSURE: 5 个套件因环境（缺二进制/资产）无法判定 —— 不计入 PASS。
```

vs the **base commit 97f74786** (temp worktree `/tmp/r6base`):

```
[lsu_test_runner] suites=52 ENV=5 FAIL=13 PASS=33 SKIP=1
NEW FAIL vs base: []
```

The 13 FAILs are **identical and pre-existing** (commit `317c71bf`'s stricter
family-aware chain semantics broke the hook suites' legacy edge expectations;
plus the missing `build/ARM/gem5.opt`). Zero new FAIL; my one new suite
(`test_lsu_ready_contract_gate.py`) PASSes (PASS 33 → 34). The 5 ENV suites and
1 SKIP are environment (no gem5 binary / no FS assets), unchanged from base.

## Unresolved risks / honesty notes

- **READY=0 is dominated by evidence availability, not by proof of fakery**: 198
  of 325 rows simply have no pilot PROP-EVT in `pilot_evidence.json`. The gate
  says "not proved" (BLOCKED/CHAIN-EVIDENCE-MISSING), which is the honest
  statement; it does not claim those chains are fake.
- **Evidence root is a live path**: the committed `ready_contract.json` records
  `LSU_CHAIN_EVIDENCE_ROOT=.../worktrees/lsu-mdspec-20261019`, which holds the
  untracked `runs/`. If that worktree is removed, regeneration downgrades the 43
  rows' detail to `chain_evidence_missing`; the category census is unchanged.
  This mirrors the pre-existing hard-coded `DEFAULT_CKPT` path.
- **Event cap 4000**: 10 of the evaluated samples exceed it and are *loudly* not
  evaluated (`chain_evidence_too_large`), never default-passed. The cause is
  `check_chain`'s super-linear path search on very large streams; a full sweep of
  those samples is deferred.
- **Splice / time-reversal detection is a heuristic**: `cross_branch_edge` fires
  when pairwise (DAG-blind) edge joining proves more edges than the single DAG
  path; the primary guarantee remains `check_chain`'s single-ancestry path. It is
  sound for the synthetic cases but is not a formal proof for adversarial inputs.
- **`check_admission` requires all of a RunID's evaluated samples to be
  admissible** (strict reading of "any `Unknown` in an activated sample"). A
  single bad sample blocks the RunID.
- **Triage-ledger semantic caveat**: `blocked_triage.md` shows `CHAIN-*` under
  the "需用户批准延期清单" section because the frozen `tests/test_lsu_triage_ledger.py`
  (not in Agent B's file ownership) accepts a blocked category only if it is a
  deferrable or a MODE/HOOK-UNIMPL. The generated mechanism text labels them
  explicitly as **evidence gates, not scope deferrals**.
- No gem5 build was available or needed (Python-only); the 5 ENV suites were not
  executed to a verdict.
