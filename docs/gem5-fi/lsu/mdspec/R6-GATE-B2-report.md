# R6-GATE B2-v2 report — chain-gate defect fixes (D1–D5)

- Worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/r6-gate` (branch `r6-gate`).
- Base `2b87cd9d` (B1 hard gate). Plan:
  `docs/superpowers/plans/2026-10-23-r6-gate-b2-chain-gate-defects.md`.
- Commits: `2fccab60` (D1/D5), `1142a511` (D3), `de7e5bd1` (D4), `23ddfb48` (D2),
  final (contract regeneration + this report). Pushed to `origin/r6-gate`.

## Inherited partial state

The dead predecessor left `ready_contract.json`/`.md` modified but uncommitted:
it re-pointed `chain_gate.evidence_root` at *this* worktree, so **every** pilot
row degraded to `CHAIN-EVIDENCE-MISSING` even though the referenced PROP-EVT
files exist under `.claude/worktrees/lsu-mdspec-20261019` (the root recorded at
HEAD, where `pilot_evidence.json`'s relative paths resolve — all 154 checked).
That per-row rewrite was discarded; the `.md` gate-verdict line it also
regenerated was reproduced faithfully by a real `--gate` run at the end.

## Per-defect RED → GREEN (real output)

| Defect | RED (real) | GREEN (real) |
|---|---|---|
| D1 `chain_end` masquerading as L5 | `[13] FAIL T04 形状终局非 full … full` and `L4->L5: proven … L5:chain_end@t7` | `[13] PASS chain_end 生命周期标记不证明 L4->L5` / `PASS T04 形状终局非 full（止于 L4 Unknown）` / `PASS _explicit_l5 要求链关联 corr（corr=none 不算）` |
| D5 real T04 must not be `full` | `TERMINAL full; admitted=True path=full_chain` | `PASS 真实 T04 终局非 full` / `PASS 真实 T04 止于 L4（provable_to=L4）` / `PASS 真实 T04 不得 admitted（D5）` |
| D3 cross-request stitch | `[14] FAIL 真实 T04 相邻跨请求对被抓（cross_request_edge）` + `AttributeError: … _ancestry_request_breaks` | `[14] PASS …×3`; real T04: `cross_request_edge: T04-F0-W4 fault 1 所选祖先上 8 处相邻见证 request_id 不一致（首例 event 38:resp req='307' → event 39:resp req='308'）` |
| D4 `cache_access` faking L1 | `[15] FAIL LQ 族 cache_access 冒充 L1 被拒` / `FAIL LQ 族判定为 family=lq` / `FAIL cache 族 L1 非 cache_access 被拒` / `FAIL 两个 D4 规则名登记在 GATE_VIOLATIONS` | `[15] PASS ×5` (incl. cache-family control not flagged) |
| D2 containment option (2) unreachable | `[6] FAIL 真实 T08 显式含住 → admitted=True（option 2 可达）` with `no_closed_chain_and_no_containment: T08-F0-W4 …` | `[6] PASS 真实 T08 显式含住 → admitted=True（option 2 可达）` / `PASS 真实 T08 terminal=detected_contained` / `PASS 无含住证据不得凭 option 2 准入（对照组）`; `[16] PASS ×4` |

## Rulings implemented

- **L5 = the real detection event.** `_explicit_l5()` now requires a
  *non-lifecycle* kind carrying a non-empty `detection_layer` **and** `outcome`
  **and** a chain-correlating `corr` (`seq_primary|addr_fallback|origin|
  taint_prop`). `chain_end` (always `corr=none`) is structurally excluded: it
  occupies **no** layer any more, so `ready_by_chain_end_only` is enforced by
  construction, not by a message. Layout: `_LIFECYCLE_KINDS`, `_CHAIN_CORR`,
  `_obs_layer_of()` (family observation layer, keeps prefix proofs working).
- **Cross-request stitching** is caught on the whole chosen ancestry
  (`_ancestry_request_breaks`), not only between the ≤6 layer representatives.
- **L1 identity is family-aware** (`_UNIT_FAMILY` by RunID prefix
  T/L/S/C/A/P/O): the cache family's L1 must be `cache_access`
  (`cache_l1_missing`); every other family may not take a cache-structure event
  as its L1 (`cache_access_faked_l1`). Both tokens registered in
  `GATE_VIOLATIONS`.
- **Containment (option 2)** is derived from explicit evidence only
  (`containment_from_events`): `contained=1` + `detection_layer` + `outcome`,
  descending from the unit's own L0→L_obs prefix, and refused when any witness
  exists at a deeper layer. `chain_admission` now passes `containment` +
  `oracle_outcome` into the bundle.

## Real-stream re-judge (offline, no re-run)

| stream | before | after |
|---|---|---|
| T02-F0-W4 | `full` (bogus) | `provable_to_L4_then_unknown` |
| T04-F0-W4 | `full`, `admitted=True` | `provable_to_L4_then_unknown`, `admitted=False` (+ 8 cross-request breaks) |
| T05-F0-W4 | `detected_contained` | `detected_contained` (**now admissible** — option 2) |
| T08-F0-W4 | `detected_contained` | `detected_contained`, `chain_admission admitted=True` |
| A01-F0-W3 | `detected_translation_outcome_pending` | unchanged |
| C01-F0-W6 | `provable_to_L4_then_unknown` | unchanged, no new token (family=cache) |

## Regenerated contract (honest counts)

```
[ready_contract] total=325 READY=0 PARTIAL=0 BLOCKED=325 self_consistent=True
[ready_contract] blocked_by_category={'CHAIN-UNPROVEN': 43, 'CHAIN-EVIDENCE-MISSING': 198,
  'RULING': 6, 'FS-INFRA': 24, 'MODE-UNIMPL': 3, 'UNRESOLVED': 4, 'FS-MULTICORE': 35, 'LICENSE': 12}
[ready_contract] chain_gate admitted=0 unproven=43 evidence_missing=198
  root=/home/sdc/gem5-fi-ding/.claude/worktrees/lsu-mdspec-20261019
[gate] binary_sha256=None pytest_rc=1 mem_avail=20.6G disk_free=64.4G
[verdict] NO-GO — BLOCKED=325 > 0；正式二进制缺失；pytest_rc=1 != 0（2 failed, 19 passed）；
  全套件运行器 tests_rc=1 != 0；全套件 FAIL=13（{'FAIL': 13, 'PASS': 34, 'ENV': 5, 'SKIP': 1}）；
  ENV 阻塞=5；磁盘 free 64.4G < 红线 70.6G
```

Category counts and totals are unchanged vs HEAD (no READY reappeared, none was
relaxed); the *reasons* got stronger — real rows now fail with the new tokens,
e.g. `C11-F6-W6` `cross_request_edge` (resp req=183→260), `P06-F0-W8`
`cross_request_edge` ×7, `P06-F6-W6` `cache_access_faked_l1` (pf family L1 =
`cache_access`), `C14-F5-W6` `cache_l1_missing` (L1=None). `blocked_triage.md`
needed no regeneration (its per-category census is unchanged).

## Suite

```
[lsu_test_runner] suites=53 ENV=5 FAIL=13 PASS=34 SKIP=1
```

Baseline vs now, computed by running the runner at base `2b87cd9d`
(`git worktree add /tmp/b2base 2b87cd9d`) and diffing the FAIL suite sets:

```
baseline FAIL 13 now FAIL 13
NEW FAIL: []
FIXED   : []
```

So **NEW FAIL = []**, and one pre-existing FAIL suite (`test_lsu_hook_sq.py`)
diffed **byte-identical** before/after.

## Risks / open items

1. The 13 pre-existing FAILs include the hook suites
   (`test_lsu_hook_{a07,c11,c12,c14,c15,cpf,l04,o0x,p06,s10,sq}.py`,
   `test_lsu_campaign_propagation.py`, `pytest::collect`). They were red *before*
   this work (their fixtures still expect a closed chain the emitter does not
   produce; e.g. `test_lsu_hook_sq.py` reports all edges `missing`). Several of
   them literally assert "链 L0→L4 全边 proven → full", i.e. they encode the
   pre-D1 `chain_end`-as-L5 expectation; the hook owners should re-point those
   expectations at a real detection witness. Out of this task's scope (no
   `test_lsu_hook_*.py` was touched).
2. `chain_end` now occupies no layer at all, so `edges["L4->L5"]` is `proven`
   only when a real detection witness descends from the errant commit.
3. `containment_from_events` selects the longest fault chain when several
   faults share a stream; multi-fault streams are not exercised by current
   pilots.
4. D2 admission is reachable but vacuously unexercised by the contract: no
   RunID in `pilot_evidence.json` carries containment evidence (T08/T05 pilots
   are not registered there), so `chain_gate.admitted` stays 0. Registering
   those pilots is what would move a row to READY.
