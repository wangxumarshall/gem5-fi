# R6-P F0 Gap Closure + Faithful Submodels Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the five R6-P F0 chain gaps with evidence-based minimal fixes (no admission loosening, no fabricated terminals), then implement the smallest faithful P04/P07/P09 submodels.

**Architecture:** Three independent defect classes, one commit each:
1. **Sampling**: P06-F0-W8's census used a relative `--cmd` path while the formal campaign uses an absolute path; the guest argv[0] shifts stack/cache placement, changing the eligible stream (32 vs 28). Re-census with the campaign's exact absolute command and freeze the rule.
2. **Analyzer path selection**: P01-F0-W2 has a real `errant_commit` escape on the same parent DAG as a `squash_masked` lane. `_linear_best_ordered_path` keeps the first maximal prefix (the squash lane), so the escape is reported `provable_to_L5_then_unknown`. Escape-first tie-breaking (already the documented `_terminal_rank` rule) must also apply to path selection.
3. **Missing observation link**: P06-F0-W6 and P03-F0-W8/W9 have real downstream demand accesses on the faulted line, but the demand request's first fault event is parentless. The existing `request_fork` lineage-bridge machinery is designed for exactly this; it fails because it only searches the owner request's last event, not the registered **prefetch request** (`pf_request_id`) source. Add a pf-request source arm to the bridge, and make the checker validate a `pf_request_id` source identity for family `pf`.

**Tech Stack:** gem5 v25.1.0.1 vendored C++ (`CHAOS/gem5/src/`), Python campaign/checker (`tools/`), pytest, SE O3 B0 (`configs/se/lsu_proxy.py`).

**Spec:** `docs/gem5-fi/lsu/gem5-fi-LSU单元故障注入方案-09-逐RunID传播监控.md` (P rows + 表9 chain rules), `docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md`, `docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CLOSEOUT.md`, `docs/gem5-fi/lsu/mdspec/pilot_report.md`, `tests/test_lsu_hook_p06.py` (the P06 chain contract).

## Global Constraints

- Scope this round: **P-F0/P-F5 only** (23 RunIDs). Full P matrix = 53 RunIDs across F0–F6; not claimed.
- Existing 9 certified RunIDs / 27 seeds stay PARTIAL_SUBMODEL; do not rerun or rewrite their evidence.
- F0 historical evidence stays on binary `c6cccf5b…`; F5 evidence stays on frozen `gem5.opt-8a2778d4`. Never rewrite old evidence as new-binary output.
- New runs go to new directories; old failed evidence is retained and a supersession record is added.
- No fabricated ends: no `unknown`→`contained`, no admission relaxation, no terminal without a real event.
- `git add` explicit paths only; never `git add -A`. Push to `fix/r6-p-unit-20261104` after each verified commit; never push `main`.
- Disk: ~38 GiB free; keep at most two 1.1 GiB frozen binaries per round; incremental build only.
- Commit messages end with the repo's tag line; do **not** add `Co-Authored-By: Claude`.

## Review Focus

1. A census run whose `--cmd` form differs from the campaign's absolute form — it changes the eligible stream and must never be used to set a span.
2. A bridge whose source event does not actually touch the declared shared range, or whose `old_request_id` is not the source event's identity — must be rejected loudly, never silently accepted.
3. An escape-first path tie-break that changes non-tie cases or hides a genuine containment — must only reorder equal-length maximal prefixes.
4. A prefetch bridge emitted for a `mshr_fill`/`cache_access` on a line that is not the registered faulted line (e.g. the 0x76c08 partial-overlap merges) — the shared-object check must reject it.
5. A rerun whose oracle/gzip/stats/exit identity is not re-audited — seed1 must be fully audited before seeds 2/3.

---

### Task 1: Freeze the takeover baseline

**Files:**
- Modify: `docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md` (append a version-boundary section)
- Modify: `docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CLOSEOUT.md` (append supersession policy)
- Modify: `/home/sdc/gem5-fi-ding-cleanup-20261029/R6P_UNIT_STATE.json` (version records only)

**Interfaces:**
- Consumes: current HEAD `77c6ee65`, origin `77c6ee65`, `origin/fi-ding f5055a99`.
- Produces: a written per-batch binary ledger (F0 old, F5 frozen, intermediate 587ea8c3 excluded, new F0-gap binary TBD).

- [ ] **Step 1: Record the three binary identities verbatim**

Add to `R6-P-UNIT-CENSUS.md`:

```markdown
## Binary identity ledger (2026-11-04 takeover)

| batch | binary | sha256 | source head | evidence |
|---|---|---|---|---|
| F0 certified (15 seeds) | O-worktree build | `c6cccf5b490823d216d01bd2449031aef2d892c88cec5cd291c852bbe86ca87b` | `f5055a99` | `campaign_seed1_20261104`, `campaign_seed23_20261104` |
| F5 certified (12 seeds) | `runs/lsu/r6_p_unit/binaries/gem5.opt-8a2778d4` | `8a2778d4d32644dbb02355ee90a95b3107b56af31723811f663da8940d283204` | `3f0a5589` | `campaign_f5_seed1_v2`, `campaign_f5_seed23_v2`, `campaign_f5_seed3_v2` |
| intermediate (NOT final) | `runs/lsu/r6_p_unit/binaries/gem5.opt-587ea8c3` | `587ea8c34db022edddb10828463621270d27c45944514f0234c65f30d3c5ad6d` | `3f0a5589` | none; do not cite as evidence |
```

- [ ] **Step 2: Record the supersession policy**

Append to `R6-P-UNIT-CLOSEOUT.md`: old failed F0 evidence (`campaign_seed1_20261104` for the 5 gaps) is retained; new runs go to `campaign_f0gap_20261104` (+ `_seed23`) and are linked as superseding only for the 5 gap RunIDs.

- [ ] **Step 3: Commit**

```bash
git add docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CLOSEOUT.md
git commit -m "[LSU][MDSPEC][R6-P-UNIT][DOCS] record per-batch binary ledger and F0-gap supersession policy"
git push origin fix/r6-p-unit-20261104
```

---

### Task 2: P06-F0-W8 exact-command census and frozen span rule

**Files:**
- Modify: `tools/lsu_campaign.py:1857-1859` (`PF_F0_SPAN` P06 rows)
- Modify: `tests/test_lsu_hook_p06.py:283-295` (span assertions)
- Create: `docs/gem5-fi/lsu/evidence/R6-P-F0GAP-CENSUS.md`
- Evidence: `/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/census_abs_20261104/`

**Interfaces:**
- Consumes: frozen binary `gem5.opt-8a2778d4`; campaign absolute `--cmd` form.
- Produces: `PF_F0_SPAN[("P06","cache_dirtyevict")]` and `PF_F0_SPAN[("P06","prefetch_stride")]` re-measured; the rule `warmup=1, span=N` where `N` is the exact-command no-fault eligible count.

- [ ] **Step 1: Run the no-fault census with the campaign's EXACT absolute command**

For each workload in {`cache_dirtyevict`, `prefetch_stride`}:

```bash
mkdir -p /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/census_abs_20261104
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-p-unit-20261104
CHAOS/gem5/build/ARM/gem5.opt \
  --outdir=/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/census_abs_20261104/P06_<wl> \
  configs/se/lsu_proxy.py \
  --cmd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-p-unit-20261104/workloads/directed/<wl> \
  --cpu O3 --chaos_prefetch --prefetch_mode p06_as_demand \
  --prefetch_lsu_tier F0 --prefetch_warmup_events 1 \
  --prefetch_span_events 1000000000 --prefetch_max_faults 1 \
  --prefetch_rng_seed 1 \
  --chaos_propagation --prop_run_id P06-SPAN-<wl> --prop_sample_run_id s1 \
  > /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/census_abs_20261104/P06_<wl>.out 2>&1
```

Expected: `CHAOS_LSU_TRIGGER: injector=CHAOSPrefetch tier=F0 attempted=<N> eligible=<N> injected=0` plus `SPAN_UNREACHABLE` alarm. Quote both lines verbatim in `R6-P-F0GAP-CENSUS.md`.

- [ ] **Step 2: Freeze the rule**

In `R6-P-F0GAP-CENSUS.md` state: `warmup=1; span=N; next_fire=1+lcg(seed)%N ∈ [1,N]` hits every eligible event uniformly, and the draw is guaranteed `≤ N`. The old W8 span=32 is invalid because it came from a relative-`--cmd` census (measured 32) while the formal absolute-`--cmd` stream has 28.

- [ ] **Step 3: Update `PF_F0_SPAN` and tests with the measured values**

```python
("P06", "cache_dirtyevict"): <measured W6 N>,
("P06", "prefetch_stride"): <measured W8 N>,   # expected 28; replace only with the quoted census value
```

Update `tests/test_lsu_hook_p06.py` assertions to the same values (keep the loud-refusal assertion).

- [ ] **Step 4: Verify**

```bash
python3 tests/test_lsu_hook_p06.py
python3 -m pytest tests/test_lsu_chain_check.py -q
```

Expected: ALL PASS; no new pytest failures.

- [ ] **Step 5: Commit**

```bash
git add tools/lsu_campaign.py tests/test_lsu_hook_p06.py docs/gem5-fi/lsu/evidence/R6-P-F0GAP-CENSUS.md
git commit -m "[LSU][MDSPEC][R6-P-UNIT][TOOLS] re-census P06 F0 spans with the campaign absolute command"
git push origin fix/r6-p-unit-20261104
```

---

### Task 3: Escape-first path selection (P01-F0-W2)

**Files:**
- Modify: `tools/lsu_chain_check.py:256-355` (`_walk_best_ordered_path`, `_linear_best_ordered_path`)
- Test: `tests/test_lsu_chain_check.py`

**Interfaces:**
- Consumes: `_terminal_rank` (already defined at line 1103), `_explicit_l5`, `_ancestry`, `_ordered_prefix`.
- Produces: `_path_rank(selected, by_id, family) -> int`; both path builders use `(len(sel), _path_rank(...))` so an equal-length errant-commit path beats a squash path.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_lsu_chain_check.py` a synthetic stream with two maximal L0–L5 lanes: lane A ends in `squash_masked` (earlier), lane B ends in `errant_commit` (later, on the same DAG through a root fork). Assert:

```python
v = CC.check_chain(events)
assert v["faults"]["1"]["terminal"] == "full"
assert "errant_commit" in CC._obs_layer_of  # sanity import
```

Expected before fix: FAIL (`provable_to_L5_then_unknown`, squash lane selected).

- [ ] **Step 2: Run to confirm failure**

```bash
python3 -m pytest tests/test_lsu_chain_check.py -q -k escape_first
```

- [ ] **Step 3: Implement the tie-break**

```python
def _path_rank(selected, by_id, family):
    if not selected or len(selected) != len(LAYERS):
        return 0
    last = selected[-1]
    if not _explicit_l5(last):
        return 0
    anc = _ancestry(last, by_id)
    if any(e.get("kind") in _L4_TERMINAL_KINDS for e in anc):
        return 2          # full escape (spec terminal 1)
    return 1              # explicit L5 but no L4 terminal
```

In `_walk_best_ordered_path` and `_linear_best_ordered_path`, replace `len(selected) > len(best)` / `len(sel) > len(best)` with a tuple comparison:

```python
def better(sel, best):
    if len(sel) != len(best):
        return len(sel) > len(best)
    try:
        return _path_rank(sel, by_id, family) > _path_rank(best, by_id, family)
    except NameError:
        return False
```

(`by_id` is built inside each function; pass it explicitly.)

- [ ] **Step 4: Re-run the P01 evidence through the checker**

```bash
python3 tools/lsu_chain_check.py \
  /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/campaign_seed1_20261104/P01-F0-W2/seed1/prop_evt.txt.gz \
  --run-id P01-F0-W2
```

Expected: fault 1 terminal `full`, L4→L5 witness on `errant_commit` (not `squash_masked`). The `errant_escape_outranks_containment` guard remains for any sample that still selects a squash lane.

- [ ] **Step 5: Run tests and commit**

```bash
python3 -m pytest tests/test_lsu_chain_check.py -q
git add tools/lsu_chain_check.py tests/test_lsu_chain_check.py
git commit -m "[LSU][MDSPEC][R6-P-UNIT][TOOLS] apply escape-first tie-break to chain path selection"
git push origin fix/r6-p-unit-20261104
```

---

### Task 4: Prefetch-request lineage bridge (P06-F0-W6, P03-F0-W8/W9)

**Files:**
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh:867-892`
- Modify: `CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc:394-514, 585-686`
- Modify: `CHAOS/gem5/src/mem/cache/cache.cc:180-215` (cache_access pfid)
- Modify: `CHAOS/gem5/src/mem/cache/base.cc:1860-1885` (mshr_fill pfid)
- Modify: `tools/lsu_chain_check.py:1408-1481` (pfid source identity)
- Test: `tests/test_lsu_chain_check.py`, `tests/test_lsu_hook_p06.py`

**Interfaces:**
- Consumes: `prefetchRequestId(addr,size)`, `blk_registry`, `emitLineageBridge`, `_validate_bridges`.
- Produces: bridge kind `request_fork` with `old_request_id=<pf_request_id>`, `new_request_id=<demand request_id>`, `source_event_id=<last pf event on the faulted line>`, `dest_event_id=<new request's first fault event>`, `bridge_layer=<dest obs layer>`, `shared_addr/size=<faulted block>`.

- [ ] **Step 1: Write the failing checker test**

Add a synthetic chain in `tests/test_lsu_chain_check.py`:
`inj(L0)` → `pf_train(L1, pf_request_id=4294967297, va=0x76440)` → `pf_fill(L3, pf_request_id=4294967297, cache_line=0x76440)` → `request_fork(source_event_id=pf_fill, dest_event_id=mshr_fill, old_request_id=4294967297, new_request_id=214831, bridge_layer=L2, shared_addr=76440, shared_size=40)` → `mshr_fill(L2, request_id=214831, cache_line=0x76440)` → `cache_fill(L3)` → `taint_reg(L4)` → `errant_commit(L5)`.

Assert `_validate_bridges` accepts it (the source event has `request_id=""` but `pf_request_id=4294967297`) and `check_chain` returns `full`.

- [ ] **Step 2: Run to confirm failure**

```bash
python3 -m pytest tests/test_lsu_chain_check.py -q -k pf_lineage
```

Expected: `invalid_lineage_bridge: source request_id '' != old_request_id '4294967297'`.

- [ ] **Step 3: Extend the checker**

In `_validate_bridges`, replace the source-identity clause with:

```python
src_req = str(src.get("request_id", "")).strip()
old = str(b["old_request_id"]).strip()
pf_ok = (family == "pf" and src_req == ""
         and str(src.get("pf_request_id", "")).strip() == old)
if src_req != old and not pf_ok:
    issues.append(...)
    continue
```

No other clause changes: the shared-object and parent-edge checks still apply.

- [ ] **Step 4: Add the C++ pf source record and bridge arm**

In `CHAOSPropagation.hh`, next to `ptag_branch_src`:

```cpp
// [R6-P-BRIDGE] Last event of this ptag that carries a prefetch-request
// identity (pf_train/pf_queue/pf_issue/pf_fill/pf_demand).  pf_request_id
// is the spec's request-level identity for prefetch requests and is the
// only legal source for a prefetch->demand lineage bridge (a prefetch
// request has no CPU request_id).
struct PfLineageSrc {
    uint64_t event_id = 0;
    uint64_t pfid = 0;
    LineageSrc addr;
};
std::map<uint64_t, PfLineageSrc> ptag_pf_src;   // ptag -> last pf event
```

In `emitPropEvt`, after the auto fields and before the bridge block:

```cpp
if (ptag != 0) {
    const std::string &pf = fields["pf_request_id"];
    if (!pf.empty() && pf != "0") {
        auto hex = [&](const char *k) -> uint64_t {
            const auto it = fields.find(k);
            return (it == fields.end() || it->second.empty())
                ? 0 : strtoull(it->second.c_str(), nullptr, 16);
        };
        PfLineageSrc s;
        s.event_id = event_id;
        s.pfid = strtoull(pf.c_str(), nullptr, 10);
        s.addr = LineageSrc{event_id, hex("va"), hex("pa"),
                            hex("cache_line")};
        ptag_pf_src[ptag] = s;
    }
}
```

In `emitLineageBridge`, before the owner-request lookup:

```cpp
const std::string &pf = fields.count("pf_request_id")
    ? fields.at("pf_request_id") : std::string();
if (!pf.empty() && pf != "0") {
    const auto pit = ptag_pf_src.find(ptag);
    if (pit != ptag_pf_src.end()
            && pit->second.pfid == strtoull(pf.c_str(), nullptr, 10)
            && pit->second.event_id != 0) {
        src_request = pit->second.pfid;
        src = pit->second.addr;      // use this instead of the owner source
    }
}
```

Keep the existing "no verifiable shared object → no bridge" loop and all field serialization; the bridge's `old_request_id` becomes the pfid and `new_request_id` the demand request id.

- [ ] **Step 5: Put the pfid on the two destination sites**

`cache.cc` `cache_access` (before `notePropEvt`):

```cpp
const uint64_t h4_pfid = h4->prefetchRequestId(
    pkt->getAddr(), pkt->getSize());
// in the field map:
{"pf_request_id", h4_pfid ? std::to_string(h4_pfid) : ""},
```

`base.cc` `mshr_fill` (the `h4f` block):

```cpp
const uint64_t h4f_pfid = h4f->prefetchRequestId(pkt->getAddr(), blkSize);
// in the mshr_fill field map:
{"pf_request_id", h4f_pfid ? std::to_string(h4f_pfid) : ""},
```

Do not modify the prefetch's own `mshr_fill`/`pf_fill` arm: a prefetch fill has no stamped `request_id`, so the existing `stamped0` gate skips it.

- [ ] **Step 6: Build (incremental) and run unit tests**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-p-unit-20261104/CHAOS/gem5
scons -j16 build/ARM/gem5.opt 2>&1 | tee /home/sdc/gem5-fi-ding-cleanup-20261029/r6o-logs/p_f0gap_build.log
```

Expected: zero new warnings; check the log for the P-unit files. Then:

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-p-unit-20261104
python3 -m pytest tests/test_lsu_chain_check.py tests/test_lsu_hook_p06.py -q
```

- [ ] **Step 7: Freeze the binary**

```bash
SHA=$(sha256sum CHAOS/gem5/build/ARM/gem5.opt | cut -c1-8)
cp CHAOS/gem5/build/ARM/gem5.opt /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/binaries/gem5.opt-$SHA
sha256sum /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/binaries/gem5.opt-$SHA
```

Record the full SHA, source commit (this commit), build log path, and "zero new warnings" in `R6-P-F0GAP-CENSUS.md`.

- [ ] **Step 8: Commit**

```bash
git add CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.hh CHAOS/gem5/src/cpu/o3/CHAOSPropagation/CHAOSPropagation.cc CHAOS/gem5/src/mem/cache/cache.cc CHAOS/gem5/src/mem/cache/base.cc tools/lsu_chain_check.py tests/test_lsu_chain_check.py tests/test_lsu_hook_p06.py
git commit -m "[LSU][MDSPEC][R6-P-UNIT][PROP] bridge prefetch requests to their demand consumers by pf_request_id"
git push origin fix/r6-p-unit-20261104
```

---

### Task 5: Seed-1 verification for the five RunIDs (new binary, new directory)

**Files:**
- Evidence: `/home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/campaign_f0gap_20261104/<RunID>/seed1/`
- Modify: `docs/gem5-fi/lsu/evidence/R6-P-F0GAP-CENSUS.md`

**Interfaces:**
- Consumes: frozen F0-gap binary; `PF_F0_SPAN` values from Task 2.
- Produces: seed1 terminal/oracle/admission per RunID, with quoted trigger and chain lines.

- [ ] **Step 1: Re-run the no-fault goldens with the new binary**

For W2/W6/W8/W9/W10, run the campaign golden control (same command shape as the prior goldens) and confirm: W2 `a10b9827edd8a9fb`, W6 `062e5124df3667f9`, W8 `629727c0ad9ca8ef`, W9 `030921682b3731f2`, W10 `50ab96a7fe8f6ec2`. If any hash moves, stop and treat it as a binary-change regression.

- [ ] **Step 2: Seed1 campaign**

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/r6-p-unit-20261104
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/campaign_f0gap_20261104 \
  --cells P01-F0-W2,P03-F0-W8,P03-F0-W9,P06-F0-W6,P06-F0-W8 \
  --phase trial --seed-start 1 --n-seeds 1 --max-parallel 4
```

- [ ] **Step 3: Audit every seed1**

For each RunID, verify and quote:
- `cell_results.json`: `activated=1`, oracle class, `conservation=OK`, no trigger alarm.
- `chain_summary.md` / `chain_report.json`: terminal, `provable_to`, `beyond`, `admitted`.
- `prefetch_injections.log`: exactly one effective injection with a real before→after.
- gzip EOF on `prop_evt.txt.gz` and `prop_trace.csv.gz`; `stats.txt` non-empty; `run.out` exit 0; not truncated.
- For P06/P03: the new `request_fork` bridge event exists, its source/dest ids and shared range match the real events, and the L5 ancestry contains the bridge.

- [ ] **Step 4: Decide per RunID**

- P01-W2: expected `full` (errant_commit), admitted via `full_chain`; oracle remains the real Masked.
- P06-W6: expected `full` through the pf bridge; oracle remains Masked.
- P03-W8/W9: if the bridge is present and the chain reaches a real L5, record `full`; if the bridge is absent because the source does not touch the faulted block, record an explicit local block (`cross_branch/L4-only; pf source not verifiable`) — do not borrow the L5.
- P06-W8: expected injected=1 (span=28, draw ≤28), chain per the same audit.

Any RunID not passing remains not certified; never edit the oracle or admission.

- [ ] **Step 5: Commit the seed1 evidence record**

```bash
git add docs/gem5-fi/lsu/evidence/R6-P-F0GAP-CENSUS.md docs/gem5-fi/lsu/mdspec/R6-P-UNIT-CENSUS.md
git commit -m "[LSU][MDSPEC][R6-P-UNIT][DOCS] record seed1 F0-gap reruns with the pf lineage bridge"
git push origin fix/r6-p-unit-20261104
```

---

### Task 6: Seed 2/3 and closeout

**Files:**
- Evidence: `campaign_f0gap_seed23_20261104/`
- Modify: `R6-P-UNIT-CENSUS.md`, `R6-P-UNIT-CLOSEOUT.md`, `docs/gem5-fi/lsu/EVIDENCE*`, `CATALOG*`, `INDEX*`, `STATUS*`, `R6-P-UNIT-STATUS.json`
- Modify: `/home/sdc/gem5-fi-ding-cleanup-20261029/R6P_UNIT_STATE.json`, `R6P_UNIT_PROGRESS.md`

**Interfaces:**
- Consumes: seed1 outcome per RunID; only RunIDs with a clean seed1 get seeds 2/3.
- Produces: updated certified/blocked counts, per-seed docs, audit report, regression set comparison.

- [ ] **Step 1: Seeds 2/3 for the passing RunIDs only**

```bash
python3 tools/lsu_campaign.py \
  --matrix artifacts/lsu-trial/07-expanded-matrix-backfilled.csv \
  --outdir /home/sdc/gem5-fi-ding/runs/lsu/r6_p_unit/campaign_f0gap_seed23_20261104 \
  --cells <passing RunIDs> \
  --phase trial --seed-start 2 --n-seeds 2 --max-parallel 4
```

- [ ] **Step 2: Audit seeds 2/3 identically to Task 5 and write per-seed docs**

Path: `runs/lsu/R6_COMPLETE_PROPAGATION_PATHS/<RunID>/<RunID>-seedN.md`.

- [ ] **Step 3: Update the propagation document, EVIDENCE, CATALOG, INDEX, STATUS, STATE/PROGRESS**

Counts must distinguish: complete seeds, complete RunIDs, submodel coverage. A full chain ≠ full fault model. P01/P02/P03/P05/P06/P08 remain PARTIAL_SUBMODEL at their documented boundaries; P03-b is still absent.

- [ ] **Step 4: Correct the audit report's anomalous generation time**

Inspect audit artifacts for a future/clock-skew timestamp; keep a correction note (what was wrong, what it is now, evidence). Do not silently delete the old value.

- [ ] **Step 5: Independent evidence audit + regression**

```bash
python3 -m pytest -q
```

Compare the failure **set**, not just the count, against the recorded baseline (309 passed / 10 failed). Any new failure is a hard stop. Run the realroot/hook regressions the prior round used.

- [ ] **Step 6: Commit and push**

```bash
git add <explicit doc/index/state paths>
git commit -m "[LSU][MDSPEC][R6-P-UNIT][DOCS] close F0 gaps with per-seed evidence and audited totals"
git push origin fix/r6-p-unit-20261104
```

---

### Task 7: Faithful P04 queue valid/pointer/select submodel

**Files:**
- Create: `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetchP04.hh` (or extend the existing injector with a `P04QueueState` mode gated by `--prefetch_mode p04_queue_state`)
- Modify: `CHAOSPrefetch.cc`, `CHAOSPrefetch.hh`, `CHAOSPrefetch.py`
- Modify: `tools/lsu_campaign.py` (`MODEL_FLAGS["P04"]`)
- Test: `tests/test_lsu_hook_p04.py`

**Interfaces:**
- Consumes: the prefetch queue (`prefetch::Queued`) entry state, `pf_request_id`, the trigger.
- Produces: P04-a queue **valid** clear, P04-b queue **pointer** corruption (head/tail), P04-c queue **select** wrong-entry substitution — each a real state mutation with an event (`field=queue_valid|queue_pointer|queue_select`, before/after), not the P05 drop/dup approximation.

- [ ] **Step 1: Write behavior tests first** (trigger eligibility, real state mutation, no P05 reuse, event fields).
- [ ] **Step 2: Implement one submodel at a time (a → b → c), each its own commit**, with a no-fault gate and seed1 pilot before seed2/3.
- [ ] **Step 3: Keep P04 in PARTIAL_SUBMODEL until all three are implemented and certified.**

---

### Task 8: Faithful P07 fill way/tag and P09 prefetch-dirty writeback

Same shape as Task 7, one submodel per commit:
- P07: hook the prefetch response fill site; corrupt the **fill way** (`way`) or **tag** (`tag`) and emit the real fill event fields; do not reuse `l1d_target_field=tag`.
- P09: hook the prefetch-caused dirty eviction/writeback site; models `writeback_loss` / `writeback_done_early` / `writeback_clear`; do not reuse `l1d_target_field=dirty`.
- P09-W13 stays BLOCKED_ASSET (PARSEC absent); do not substitute another probe.

---

### Task 9: P04-c behavioral verification (takeover round)

**Files:**
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/queued.hh`, `queued.cc`
- Modify: `CHAOS/gem5/src/mem/cache/prefetch/CHAOSPrefetch/CHAOSPrefetch.hh`, `.cc`
- Modify: `tests/test_lsu_hook_p04.py`
- Modify: `docs/gem5-fi/lsu/evidence/R6-P-P04-EVIDENCE.md`,
  `R6-P-UNIT-CENSUS.md`, `R6-P-UNIT-CLOSEOUT.md`

- [x] Add observation-only selection/issue shadows (`chaosSelectedWrong`,
  `chaosDisplacedHead`) and a dedicated `p04c_queue_behavior.log`; no issue
  decision changes when the mode is unmounted.
- [x] Record selection identities (head/second) and real issue roles
  (`wrong_selected` / `head_issued_late`).
- [x] Build and freeze `gem5.opt-a0d0e8af`
  (`a0d0e8af9d2242dd6250c24f48bdecf396e4bcc6c220dbbc6e331b65f49cd687`).
- [x] Run W2/W8 fault pilots + no-fault controls; verify the issue order is
  exactly reversed and both entries issue once.
- [x] Add behavior-log assertions to `tests/test_lsu_hook_p04.py`.
- [x] Full pytest: 309 passed / 10 failed, identical historical failure
  set (r6a4, results_layout, 8 s_prop_docs) => NEW FAIL=0.

### Task 10: P04-b pointer submodel (next unit)

- [ ] Implement a real tail-pointer -1 insertion fault (no drop/dup), with
  L0/L1/L2 events and a behavior check; build/freeze a new binary.
- [ ] Run the exact-command no-fault census for the F0 W2/W8 stream, freeze
  the span, and run seed1 before seeds 2/3.

## Self-Review

- **Spec coverage:** P01 (stride), P03 (same-page subst), P06 (fill-class), P04 (queue), P07 (fill way/tag), P09 (dirty writeback) each have a task or a documented block; P03-b cross-page remains explicitly absent; P09-W13 remains asset-blocked.
- **Placeholder scan:** no `TBD` except the two census values that must be filled from the quoted real census output in Task 2; the plan requires the quoted line to replace them.
- **Type consistency:** `pf_request_id` is the prefetch request identity; `old_request_id` in a bridge is the pfid for prefetch sources; `request_id` stays the CPU request id; the checker accepts the pfid source only for family `pf` and only when the source event has no CPU request id.
- **Review focus tests:** absolute-command census (Task 2), bridge shared-object rejection (Task 4 test), escape-first only on equal-length ties (Task 3 test), bridge destination on the registered line only (Task 4), full seed1 audit before seeds 2/3 (Tasks 5–6).
