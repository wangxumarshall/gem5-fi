# OOO FIX-B Re-admission: Real E2E (gem5 beb5d6b7) + eng3 n=2 + Handoff Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-admit the L0–L5 observation chain on the new frozen gem5 (`beb5d6b7…a39e6a4`): fix the four real integration bugs the 12:27 baseline E2E exposed, run the real E2E to PASS in a new independent directory, run eng3 n=2 engineering admission for the four backfill RunIDs, and produce `admission_handoff_eng3.json` — then stop at "waiting for central merge".

**Architecture:** All fixes are Python-only (tools/); the frozen binary is NOT rebuilt or re-frozen. The L3 builder (`tools/ooo_l3.py`) gains (a) dict-form `first_divergent_commit` normalization, (b) a rename/RAT map-entry join seeded from the L0 event's `(class, arch, new_phys)` tags — empirically validated on the retained 12:27 SDC sample. `do_l3` in `tools/ooo_sample_runner.py` gains the `rat` component alias and an honest `not_observed_before_crash` status for zero-byte crash traces. `tools/ooo_observation.py` emits a gate-recognized `l0.limited_reason` when `eligible_count` has no source (documented n/a, never a silent null). The E2E contract (`tools/tests/e2e/ooo_l0l5_e2e.py`) is updated from the pre-FIX-B "L3 unsupported" expectation to the real `source_read` chain, and gains an `OOO_E2E_ROOT` env override so the re-admission E2E writes to a new directory without touching old experiments.

**Tech Stack:** Python 3 stdlib only (argparse/json/gzip/re/os). No scons, no C++. Tests are plain scripts with process exit codes.

**Spec:** User task brief "0201 OOO 完整观测链 — 从真实E2E和重新准入继续" (2026-10-13, 11 numbered steps, quoted inline where pinned) + patrol-log §[09:45] re-admission plan ("E2E 四类 → eng3 4×n=2 → 全量完整性审计（含 activated>0 且 chain_complete=true ≥1 的硬要求）→ admission verdict=PASS").

## Ground Truth (measured 2026-10-13, this session, all commands real)

- Worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/ooo-l0l5`, branch `ooo/l0l5-chain`, HEAD `8cd46c1`. Sole uncommitted change: `tools/tests/e2e/ooo_l0l5_e2e.py` (FROZEN_GEM5_SHA → `beb5d6b7…`, `trace["ctrace_v2"]=True`) — verified by `git diff`, nothing else.
- `sha256sum` both `build/ARM/gem5.opt` (repo root and worktree) = `beb5d6b7a254049c5388734abd5889f362d72caf93e24cfe2ccfae7a2a39e6a4`.
- Baseline E2E 12:27–12:32 (this exact tree state) at `runs/ooo-l0l5/e2e/e2e_result.json`: normal **PASS**; masked **FAIL** (`decode l3.status must be unsupported ('error')` + audit `l0_funnel_missing`); crash **FAIL** (`l3_unsupported_with_activation` + `l0_funnel_missing`); sdc **FAIL** (same two violations). Root causes, each reproduced from retained evidence:
  1. **fdc dict**: `tools/ooo_l3.py:270` `rec.seq > fdc` — `do_l3` passes `l2_blk["first_divergent_commit"]` = `{"seq": 103, …}` (dict); builder expects int. Direct call with dict → `TypeError: '>' not supported between instances of 'int' and 'dict'`; without kwargs → real chain built.
  2. **rat wiring**: E2E sdc class injector is `rat` (manifest `target.component`); `do_l3` checks `component in ("decode","rename")` → falls to unsupported. Rename `map_bitflip2_adj` log line carries **no sn** — only `class=vec, arch=V1, old_phys=1, new_phys=13`. Empirical join on the retained SDC ctrace: after injection tick 9933770 there are **885** committed reads with src triple `(2,1,13)` and **0** with `(2,1,1)`; first consumer = seq 5269 `cmeq`; first L2 divergence seq 5798 `fmla` whose run line itself carries src `(2,1,13)`. `RegClassType`: IntRegClass=0, FloatRegClass=1, VecRegClass=2 (src/cpu/reg_class.hh:61-64). CHAOSRenameMap targets Vec (prefix "V", tag ", class=vec") or Int (prefix "X", no tag) pools only.
  3. **crash zero-byte**: crash sample `evidence/ctrace.csv.gz` is 0 bytes → head-read yields "" → `is_v2=False` → "retained trace is v1" (false reason). l1/l2 already use honest `no_snapshots_before_crash` / `not_observed_before_crash`.
  4. **eligible_count**: semantic gate `l0_funnel_missing` fires when `l0.attempted` or `l0.eligible_count` is null without a limited reason (`l0.status=no_log` or non-empty `l0.funnel_limited_reason`/`l0.limited_reason`). Producer writes the scope note under key `limited` (gate doesn't read it) and `eligible_count=None` for decode/rat (only CHAOSLSQFwd/CHAOSExec ever write `CHAOS_ELIGIBLE_COUNT=`, at teardown). Real values ARE present: `attempted=1, eligible=1`.
- E2E masked-sample chain geometry (real): L0 event sn=159; source row commits at seq 103 which **is** the first divergence (`fdc.seq=103`); first downstream consumer seq 107 (seqenc 186). With fdc honored, masked → `hops=[]` is the honest result (window ends at the source row itself); the join proof is `source_row.seqencNum == sn`. SDC (rat): first hop seq 5269 < fdc 5798 → hops ≥ 1.
- eng2 previous round (same base_seed 52001000, old binary): D01-c r0000 Hang + r0001 Masked; D02-b/c and D04-d both Masked (7 Masked + 1 Hang, all injector=decode — D02 is decode `field=mixed bitflip2_nonadj`, NOT rat). RNG stream is byte-identical on the new binary (FIX-B verified "RNG stream untouched"), so eng3 with the same seeds reproduces the same geometries plus v2 traces.
- Candidate RunIDs for eng3 (patrol-log §[09:45] "eng3 4×n=2"): `D01-F0-W6-c`, `D02-F0-W6-b`, `D02-F0-W6-c`, `D04-F0-W4-d`. D01-a/b formal state (registered-not-backfilled, Excel frozen F-013) is a **central** concern — recorded in the handoff as a separate note, never silently decided here.

## Global Constraints

- **No C++ changes**: binary stays `beb5d6b7…a39e6a4`; no scons; no re-freeze. Python-only edits under `tools/`.
- **Gates never relaxed**: `ooo_chain_audit.semantic_gate_violations` is NOT modified. `l0.limited_reason` uses the gate's own documented escape clause. Original evidence under `runs/` is never rewritten; all new outputs go to NEW paths.
- **No formal 385 launches, no Excel writes, no merge to fi-ding/main, no new RunIDs beyond eng3 n=2 engineering samples.**
- **Hard cap 4 concurrent gem5 processes** (host OOM discipline).
- **One patch per unit**: commit prefix `[OOO][FIX-RB]`, each commit self-verified with real commands; NO `Co-Authored-By` line (project CLAUDE.md rule overrides the default attribution).
- **Auto-push** branch `ooo/l0l5-chain` to remote after each verified commit (never main). Work only in the worktree `/home/sdc/gem5-fi-ding/.claude/worktrees/ooo-l0l5`.
- **Honesty**: `n/a` never silent zeros; `unsupported` only when truly no join exists; `execution_complete` is never passed off as `chain_complete`.
- Machine is idle (guard log 13:01–14:00: gem5=0); ~24.9 GiB MemAvail.

## Review Focus (input classes the brief implies but old tests never exercised)

1. **fdc as dict** — the exact integration shape (`l2.first_divergent_commit` record). Pinned by Task 5 tests (dict == int behavior, echo, unusable-dict caveat).
2. **RAT event without sn** (map_bitflip family) — must join via (class, arch, new_phys); no tags at all → honest unsupported. Pinned by Task 7 tests (join/kill/squash/zero-reader/no-tags).
3. **Phys-reuse false extension** — a later *legitimate* re-mapping of the same arch to the same phys must not extend the chain; the map seed dies at the next same-(class,arch) dest. Pinned by Task 7 kill test.
4. **Zero-byte ctrace on early Crash** — must read `not_observed_before_crash`, must NOT fire `l3_unsupported_with_activation`, chain gap L3 recorded. Pinned by Task 6 tests.
5. **eligible_count n/a must not mask a missing log** — with-log samples get `limited_reason` (documented n/a); no-log samples keep `status=no_log` (gate already covers). Pinned by Task 8 tests (both directions). Plus: **masked fixture where fdc == source seq** (zero hops, still chain_complete=true) — pinned by Task 9 fixtures.

---

### Task 1: This plan document

**Files:**
- Create: `docs/superpowers/plans/2026-10-13-ooo-fixB-readmission-e2e-eng3.md` (this file)

- [x] **Step 1: Write the plan** (done — this file)
- [x] **Step 2: Commit**

```bash
git add docs/superpowers/plans/2026-10-13-ooo-fixB-readmission-e2e-eng3.md
git commit -m "[OOO][FIX-RB] plan: FIX-B re-admission — real E2E on beb5d6b7, eng3 n=2, handoff (4 integration fixes scoped from the 12:27 baseline)"
git push origin ooo/l0l5-chain
```

### Task 2: Test battery + commit the pending E2E modification

**Files:**
- Commit (no edit): `tools/tests/e2e/ooo_l0l5_e2e.py` (the existing uncommitted SHA+ctrace_v2 change)

**Interfaces:** none (verification + a commit of an already-written change).

- [ ] **Step 1: Run the full offline battery** (13 suites, no gem5 for most; sample_runner/golden_key use the real frozen binary). From the worktree root:

```bash
for t in test_ooo_guard test_ooo_guard_race test_ooo_scheduler_dry test_ooo_observation test_ooo_sample_runner test_ooo_golden_key test_runner_msnap_flag test_commit_diff_seqrange test_ooo_chain_audit test_ooo_handoff test_faults_log_contract test_ooo_l3; do
  echo "=== $t"; python3 tools/tests/$t.py >/tmp/rb_$t.log 2>&1; echo "rc=$?"; tail -2 /tmp/rb_$t.log
done
echo "=== e2e self-test"; python3 tools/tests/e2e/ooo_l0l5_e2e.py --self-test; echo "rc=$?"
echo "=== admission self-test"; python3 tools/tests/e2e/ooo_l0l5_admission.py --self-test; echo "rc=$?"
```

Expected: every rc=0 (all suites green on the pre-fix tree — the fixtures encode the current contracts; Tasks 5–9 update them alongside the fixes).

- [ ] **Step 2: Commit the pending E2E modification** (user step 3; the diff is exactly SHA + ctrace_v2, verified in Task-2 ground truth):

```bash
git add tools/tests/e2e/ooo_l0l5_e2e.py
git commit -m "[OOO][FIX-RB] e2e: re-freeze gem5 sha beb5d6b7 + enable ctrace_v2 in E2E campaigns (L3 source->consumer input)"
git push origin ooo/l0l5-chain
git status --porcelain   # must be empty
```

### Task 3: OOO_E2E_ROOT env override (new independent E2E directory)

**Files:**
- Modify: `tools/tests/e2e/ooo_l0l5_e2e.py:59` (E2E_ROOT definition)

**Interfaces:**
- Produces: env var `OOO_E2E_ROOT` — when set, the E2E writes campaigns/samples/goldens/e2e_result.json under it; unset → the current default `/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e` (byte-identical behavior). Mirrors the existing `OOO_E2E_SELFTEST_ROOT` pattern at line 60-62.

- [ ] **Step 1: Edit E2E_ROOT**

```python
E2E_ROOT = os.environ.get(
    "OOO_E2E_ROOT",
    "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e")
```

- [ ] **Step 2: Verify override + default**

```bash
OOO_E2E_ROOT=/tmp/rb-e2e-override-check python3 - <<'EOF'
import os, sys
os.environ["OOO_E2E_ROOT"] = "/tmp/rb-e2e-override-check"
sys.argv = ["e2e", "--self-test"]
import importlib.util
spec = importlib.util.spec_from_file_location("e2e", "tools/tests/e2e/ooo_l0l5_e2e.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.E2E_ROOT == "/tmp/rb-e2e-override-check", m.E2E_ROOT
print("override ok:", m.E2E_ROOT)
EOF
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('e2e','tools/tests/e2e/ooo_l0l5_e2e.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.E2E_ROOT == '/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e', m.E2E_ROOT
print('default ok:', m.E2E_ROOT)"
python3 tools/tests/e2e/ooo_l0l5_e2e.py --self-test; echo "rc=$?"
```

Expected: `override ok`, `default ok`, self-test rc=0.

- [ ] **Step 3: Commit**

```bash
git add tools/tests/e2e/ooo_l0l5_e2e.py
git commit -m "[OOO][FIX-RB] e2e: OOO_E2E_ROOT env override — re-admission runs into a new independent dir, old experiments untouched"
git push origin ooo/l0l5-chain
```

### Task 4: Baseline E2E run (pre-fix, expected FAIL — honest record)

**Files:** none (evidence only, under `runs/`).

- [ ] **Step 1: Run the real E2E into the new baseline dir** (user step 4; ~7 min: smoke goldens ~8 s + dcv golden ~91 s + 4 samples):

```bash
OOO_E2E_ROOT=/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e.v4a-fixB-pre \
  python3 tools/tests/e2e/ooo_l0l5_e2e.py 2>&1 | tee /tmp/rb_e2e_pre.log; echo "rc=$?"
```

Expected: **OVERALL: FAIL** reproducing the 12:27 taxonomy — normal PASS; masked FAIL (assert `decode l3.status must be unsupported ('error')` + `l0_funnel_missing`); crash FAIL (`l3_unsupported_with_activation` + `l0_funnel_missing`); sdc FAIL (same). This is the before/after evidence pair for the handoff; do NOT fix by editing this dir.

- [ ] **Step 2: Record the result paths** (no commit; runs/ is untracked):

```bash
python3 -c "
import json
r = json.load(open('/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e.v4a-fixB-pre/e2e_result.json'))
print(r['overall'], {k: r[k]['status'] for k in ('normal','masked','crash','sdc')})"
```

### Task 5: Fix A — build_l3 accepts dict-form first_divergent_commit

**Files:**
- Modify: `tools/ooo_l3.py` (build_l3: normalize fdc; lines ~177-230, ~270, ~371-373)
- Test: `tools/tests/test_ooo_l3.py` (new checks in the fdc section, ~line 350)

**Interfaces:**
- Consumes: `first_divergent_commit` as int (CLI/tests) **or** dict with int `"seq"` (sample_runner `l2_blk["first_divergent_commit"]`, `commit_diff.first_divergence`).
- Produces: unchanged result schema; `first_divergent_commit` field echoes the ORIGINAL argument; window bound uses the normalized int; unusable form → no bound + explicit caveat (never a crash, never a silent bound).

- [ ] **Step 1: Write the failing tests** (append to test_ooo_l3.py next to the existing `[7] build_l3 first_divergent_commit window` section; reuse its fixture builder — read the file first and follow its local style):

```python
    print("[7b] fdc dict form (integration contract: l2 record)")
    # reuse the same fixture trace as check [7]; fdc_dict must behave
    # exactly like fdc_int, and the result echoes the dict verbatim.
    res_int = ooo_l3.build_l3("decode", events, path, first_divergent_commit=11)
    res_dict = ooo_l3.build_l3("decode", events, path,
                               first_divergent_commit={"seq": 11,
                                                       "class": "data_corruption"})
    check("fdc-dict-same-window",
          res_dict["hops"] == res_int["hops"] and
          res_dict["status"] == res_int["status"] == "ok",
          "int hops=%r dict hops=%r" % (res_int["hops"], res_dict["hops"]))
    check("fdc-dict-echoed",
          res_dict["first_divergent_commit"] == {"seq": 11,
                                                 "class": "data_corruption"},
          repr(res_dict["first_divergent_commit"]))
    res_bad = ooo_l3.build_l3("decode", events, path,
                              first_divergent_commit={"no_seq": True})
    check("fdc-unusable-no-bound-no-crash",
          res_bad["status"] == "ok" and
          "unusable" in res_bad["caveat"], res_bad["caveat"])
```

- [ ] **Step 2: Run to verify it fails**

```bash
python3 tools/tests/test_ooo_l3.py 2>&1 | tail -6; echo "rc=$?"
```

Expected: FAIL — `fdc-dict-same-window` fails with `TypeError: '>' not supported between instances of 'int' and 'dict'` caught... if the harness check() doesn't catch exceptions, wrap the calls in try/except and check the exception type; simplest: the test file's check() pattern already prints FAIL on mismatch — adapt so a raised TypeError counts as a failed check (the file's existing style for expected-unsupported cases shows how; follow it).

- [ ] **Step 3: Implement** — in `build_l3`, right after the component check:

```python
    # Integration contract (sample_runner do_l3 / commit_diff):
    # first_divergent_commit arrives either as a bare commit-seq int
    # (CLI, unit tests) or as the l2 first-divergent RECORD (a dict
    # carrying "seq"). Normalize once; the result echoes the original.
    fdc_in = first_divergent_commit
    if isinstance(fdc_in, bool):
        fdc_seq = None
    elif isinstance(fdc_in, int):
        fdc_seq = fdc_in
    elif isinstance(fdc_in, dict):
        s = fdc_in.get("seq")
        fdc_seq = s if isinstance(s, int) and not isinstance(s, bool) else None
    else:
        fdc_seq = None
```

Then: line ~224 `fdc = first_divergent_commit` → `fdc = fdc_seq`; line ~371 caveat block becomes:

```python
    if fdc is None:
        if fdc_in is None:
            caveats.append("no first_divergent_commit given: the chain was "
                           "followed to the end of the trace window")
        else:
            caveats.append("first_divergent_commit given in a form without "
                           "a usable integer seq (%r): no window bound "
                           "applied" % (fdc_in,))
```

And the two result dicts (`"first_divergent_commit": fdc` at lines ~358/~397) → `"first_divergent_commit": fdc_in`. The `_unsupported`/`_error` helper calls already receive the original `first_divergent_commit` — leave them.

- [ ] **Step 4: Verify tests pass + regression**

```bash
python3 tools/tests/test_ooo_l3.py; echo "rc=$?"
python3 tools/tests/test_commit_diff_seqrange.py; echo "rc=$?"
```

Expected: all checks PASS, rc=0 (existing check `[7]` still passes: int 11 in → echo 11).

- [ ] **Step 5: Commit**

```bash
git add tools/ooo_l3.py tools/tests/test_ooo_l3.py
git commit -m "[OOO][FIX-RB] ooo_l3: accept dict-form first_divergent_commit (l2 record with seq) — fixes the TypeError that made every activated decode sample's L3 status=error"
git push origin ooo/l0l5-chain
```

### Task 6: Fix B — do_l3 honest zero-byte crash L3 (not_observed_before_crash)

**Files:**
- Modify: `tools/ooo_sample_runner.py` (do_l3, lines ~556-585)
- Test: `tools/tests/test_ooo_sample_runner.py` (new offline checks; follow the file's existing structure — read it first)

**Interfaces:**
- Produces: for a retained trace of 0 bytes (or missing) under decode/rename/rat: `l3 = {"status": "not_observed_before_crash", "method": None, "fanout": None, "caveat": None, "reason": <zero-byte explanation>}`. `chain_completeness` records gap L3 (status != ok) — honest; `semantic_gate_violations` does NOT fire (status != "unsupported").

- [ ] **Step 1: Write the failing tests** (offline; a zero-byte gz + a l0 block with one event):

```python
    print("[rb] do_l3 zero-byte crash trace -> not_observed_before_crash")
    import ooo_sample_runner as osr
    zbuf = os.path.join(tmp, "zero.csv.gz")
    open(zbuf, "wb").close()
    l0 = {"events": [{"tick": 1, "sn": 5, "faults_injected": 1}]}
    r = osr.do_l3("decode", l0, zbuf)
    check("zero-byte-status", r["status"] == "not_observed_before_crash",
          repr(r.get("status")))
    check("zero-byte-no-false-v1-reason",
          "v1" not in (r.get("reason") or ""), repr(r.get("reason")))
    import ooo_chain_audit as oca
    obs = {"l0": {"activated": 1, "attempted": 1, "eligible_count": None,
                  "limited_reason": "x", "status": "ok"},
           "l1": {"status": "no_snapshots_before_crash"},
           "l2": {"status": "not_observed_before_crash"},
           "l3": r}
    check("zero-byte-no-semantic-violation",
          "l3_unsupported_with_activation" not in
          oca.semantic_gate_violations(obs),
          repr(oca.semantic_gate_violations(obs)))
```

- [ ] **Step 2: Run to verify it fails**

```bash
python3 tools/tests/test_ooo_sample_runner.py 2>&1 | tail -8; echo "rc=$?"
```

Expected: `zero-byte-status` FAIL (current status is `unsupported` with the false v1 reason).

- [ ] **Step 3: Implement** — in `do_l3`, first thing inside `if component in ("decode", "rename"):` (the tuple grows to include "rat" in Task 7 — keep that task's edit separate):

```python
        # Crash-truncation honesty (fix-A semantics, applied to L3): a
        # zero-byte retained trace means the run died before the first
        # gz flush -- there is nothing to join, and claiming "v1 (no
        # source triples)" would be a false reason. l1/l2 already carry
        # no_snapshots_before_crash / not_observed_before_crash; L3
        # matches that vocabulary. Chain gap L3 is still recorded by
        # chain_completeness (status != ok) -- honest, not a violation.
        try:
            _empty = os.path.getsize(retained_trace) == 0
        except OSError:
            _empty = True
        if _empty:
            return dict(status="not_observed_before_crash", method=None,
                        fanout=None, caveat=None,
                        reason="retained commit trace is zero bytes: the "
                               "run crashed before the first trace flush; "
                               "no L3 join is possible (honest n/a)")
```

- [ ] **Step 4: Also verify the truncated-nonempty behavior** (crash mid-flush): confirm `commit_diff.open_text`/`iter_ctrace_events` either rescues the readable prefix or raises a caught error → `do_l3` returns `status="error"` with the honest reason (never a crash, never fabricated hops). Test with a chopped gz (6 bytes off the tail) containing a v2 header + rows; assert status in ("ok","error") and no exception escapes. If iter_ctrace_events raises EOFError uncaught, wrap the build_l3 call site's except clause to also catch EOFError with reason "truncated v2 trace: readable prefix exhausted".

- [ ] **Step 5: Verify + regression**

```bash
python3 tools/tests/test_ooo_sample_runner.py; echo "rc=$?"
python3 tools/tests/test_ooo_l3.py; echo "rc=$?"
```

- [ ] **Step 6: Commit**

```bash
git add tools/ooo_sample_runner.py tools/tests/test_ooo_sample_runner.py
git commit -m "[OOO][FIX-RB] do_l3: zero-byte crash ctrace -> not_observed_before_crash (was: false 'retained trace is v1' unsupported)"
git push origin ooo/l0l5-chain
```

### Task 7: Fix C — rat component wiring + rename map-entry join

**Files:**
- Modify: `tools/ooo_sample_runner.py` (do_l3 tuple → `("decode", "rename", "rat")`)
- Modify: `tools/ooo_l3.py` (SUPPORTED_COMPONENTS, map-seed helper, build_l3 rename path)
- Test: `tools/tests/test_ooo_l3.py` (new `[8] rename/rat map-entry join` section)

**Interfaces:**
- Consumes: L0 rename events as parsed by `ooo_observation.parse_injection_log` from `rename_injections.log`: `{"tick": int, "site": "rename_setEntry", "mode": "map_bitflip2_adj", "class": "vec", "arch": "V1", "old_phys": 1, "new_phys": 13, "bits": "(2,3)", "dist": 1, "faults_injected": 1, "raw": …}` (int-class/arch fields also accepted).
- Produces: `build_l3("rat"|"rename", events, trace, …)`:
  - event with int `sn` → existing sn join (unchanged);
  - event without sn but with `(class, arch, new_phys, tick)` → **map-entry join**: seed = `(class_id, arch_idx, new_phys)`; consumer = first committed row with tick ≥ event tick whose src triple equals the seed; the seed dies at the first later row with dest `(class_id, arch_idx, *)` (map entry re-pointed — kills the phys-reuse false extension); downstream hops/squash/kill/fdc/budget logic shared with the sn path;
  - neither → `unsupported` with reason naming both missing keys.
  - Result adds `"source_map_entry": {"class","arch","old_phys","new_phys","tick"}` and `injected` carries tick/field/class/arch/old_phys/new_phys (no fabricated seqencNum/pc); `source_row=None`; zero hops with an explicit caveat ("no committed reader of the corrupted mapping before it was re-pointed: no architectural propagation via this mapping") — status stays ok (the observation completed; the propagation set is empty).
- Class mapping (RegClassType, src/cpu/reg_class.hh): `"vec"→2`, `"int"→0`; arch `"V<n>"/"X<n>"→n`.

- [ ] **Step 1: Write the failing tests** (hand-built v2 fixtures; follow test_ooo_l3.py's fixture style — it already builds v2 traces inline):

```python
    print("[8] rename/rat map-entry join (no sn)")
    ev = {"tick": 100, "site": "rename_setEntry", "mode": "map_bitflip2_adj",
          "class": "vec", "arch": "V1", "old_phys": 1, "new_phys": 13,
          "faults_injected": 1, "raw": "Tick: 100, ..."}
    # trace: pre-injection reader of (2,1,1); post-injection reader of
    # (2,1,13) [hop1]; a downstream consumer of hop1's dest; then a
    # re-definition of V1 (dest 2,1,*) followed by a LATER (2,1,13)
    # reader that must NOT join (phys reuse after re-point).
    rows8 = [
        "0,1,0,50,401000,mov,1,2,1,1,0000000000000001,1,2,1,1",      # pre-inj reader of true phys 1
        "1,2,0,150,401004,cmeq,1,2,2,20,0000000000000000,1,2,1,13",  # hop1: reads corrupted (2,1,13)
        "2,3,0,200,401008,fmla,1,2,3,21,0000000000000000,1,2,2,20",  # hop2: reads hop1 dest (2,2,20)
        "3,4,0,250,40100c,mov,1,2,1,30,0000000000000000,0",          # V1 re-defined -> seed/map window ends
        "4,5,0,300,401010,cmeq,1,2,4,40,0000000000000000,1,2,1,13",  # later (2,1,13) reader: phys reuse, NOT a consumer
    ]
    p8 = _write_trace(tmp, "rat8", rows8)          # existing fixture helper w/ v2 header
    r8 = ooo_l3.build_l3("rat", [ev], p8, first_divergent_commit=None)
    check("rat-join-status", r8["status"] == "ok" and
          r8["method"] == "source_read", repr(r8.get("status")))
    check("rat-join-hops", [h["seq"] for h in r8["hops"]] == [1, 2],
          repr(r8["hops"]))
    check("rat-via-src", r8["hops"][0]["via_src"] ==
          {"class": 2, "arch": 1, "phys": 13}, repr(r8["hops"][0]["via_src"]))
    check("rat-source-map-entry", r8["source_map_entry"] ==
          {"class": 2, "arch": 1, "old_phys": 1, "new_phys": 13,
           "tick": 100}, repr(r8.get("source_map_entry")))
    # kill: only the FIRST (2,1,13) reader joins; the post-re-point one (seq 4) must not
    # zero-reader case
    rows8b = [r for r in rows8 if r.split(",")[0] != "1"]
    p8b = _write_trace(tmp, "rat8b", rows8b)
    r8b = ooo_l3.build_l3("rat", [ev], p8b)
    check("rat-zero-reader-honest",
          r8b["status"] == "ok" and r8b["hops"] == [] and
          "no committed reader" in r8b["caveat"], repr(r8b["caveat"]))
    # no tags, no sn -> unsupported
    r8c = ooo_l3.build_l3("rat", [{"tick": 100, "mode": "map_bitflip"}], p8)
    check("rat-no-join-keys-unsupported",
          r8c["status"] == "unsupported" and "sn" in r8c["reason"] and
          "new_phys" in r8c["reason"], repr(r8c.get("reason")))
    # sn still wins when present (rename dest_reg_sub family)
    r8d = ooo_l3.build_l3("rat", [dict(ev, sn=2)], p8)
    check("rat-sn-priority", r8d["source_row"] is not None and
          r8d["source_row"]["seqencNum"] == 2, repr(r8d.get("source_row")))
```

(Adapt helper/fixture names to what test_ooo_l3.py actually provides — read it first; the semantic assertions above are the contract.)

- [ ] **Step 2: Run to verify it fails**

```bash
python3 tools/tests/test_ooo_l3.py 2>&1 | tail -10; echo "rc=$?"
```

Expected: `[8]` checks FAIL (rat currently unsupported at the component gate).

- [ ] **Step 3: Implement — ooo_l3.py**:

```python
SUPPORTED_COMPONENTS = ("decode", "rename", "rat")
```

New helpers near `_pick_source_event`:

```python
_REG_CLASS_TAG = {"vec": 2, "int": 0}   # RegClassType (reg_class.hh)
_RE_ARCH_NAME = re.compile(r"^[VX](\d+)$")


def _map_seed_from(event):
    """RAT map-corruption seed triple for a rename_setEntry
    map_bitflip-family event: the arch reg's mapping was corrupted
    old_phys -> new_phys, so the first reader renamed after the fault
    carries src == (class, arch, new_phys). Returns
    (class, arch, phys, tick, old_phys) or None when the tags are
    absent/non-int."""
    cls = event.get("class")
    if isinstance(cls, str):
        cls = _REG_CLASS_TAG.get(cls.strip().lower())
    elif isinstance(cls, bool):
        cls = None
    arch = event.get("arch")
    if isinstance(arch, str):
        m = _RE_ARCH_NAME.match(arch.strip())
        arch = int(m.group(1)) if m else None
    phys = event.get("new_phys")
    tick = event.get("tick")
    old = event.get("old_phys")
    if not all(isinstance(x, int) and not isinstance(x, bool)
               for x in (cls, arch, phys, tick)):
        return None
    return cls, arch, phys, tick, (old if isinstance(old, int) else None)
```

In `build_l3`: after `_pick_source_event` — if `n_with_sn == 0` and component in `("rename", "rat")`, take the first event with `_map_seed_from(...) != None` as the seed event (report others in counts); if none → `_unsupported(..., "rename/rat L0 events carry neither an sn join key nor (class, arch, new_phys) map tags: no honest join exists")`. In the scan loop: for map mode, skip the `source_row is None` gating and instead (a) only consider rows with `rec.tick >= seed_tick`, (b) consumer test = any src triple equal to the seed triple, (c) after appending hop 1, seed the shared `live` set with hop 1's dest triples and continue with the normal downstream logic, (d) kill the seed at the first row with a dest triple `(cls, arch, *)`; squash events whose srcs contain the seed triple before the first consumer → `squashed_consumers` (committed=false). `injected`/`source_map_entry`/zero-hop caveat per the Interfaces block. Budget counter `rows_scanned_after_source` counts rows with tick ≥ seed_tick.

- [ ] **Step 4: Implement — ooo_sample_runner.py do_l3**: `if component in ("decode", "rename", "rat"):` (comment: manifest `target.component` for the RAT injector is `rat`; `rename` kept as the library's family name).

- [ ] **Step 5: Verify against the RETAINED real sample** (the strongest test — the 12:27 SDC evidence):

```bash
SDIR=/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e/e2e_sdc_fr02_replica/samples/e2e_sdc_fr02_replica-c0000-r0000
python3 - "$SDIR" <<'EOF'
import json, sys
sys.path.insert(0, "tools")
import ooo_l3
obs = json.load(open(sys.argv[1] + "/observation.json"))
ev = obs["l0"]["events"][0]
fdc = obs["l2"].get("first_divergent_commit")
r = ooo_l3.build_l3("rat", obs["l0"]["events"],
                    sys.argv[1] + "/evidence/ctrace_window.csv.gz",
                    first_divergent_commit=fdc)
print("status:", r["status"], "| method:", r["method"])
print("hops:", len(r["hops"]), "first hop:", r["hops"][0] if r["hops"] else None)
assert r["status"] == "ok" and r["hops"], r
assert r["hops"][0]["seq"] == 5269 and r["hops"][0]["via_src"]["phys"] == 13
assert r["hops"][0]["via_src"] == {"class": 2, "arch": 1, "phys": 13}
print("REAL-DATA JOIN PROVEN: first hop seq 5269 reads the corrupted (2,1,13)")
EOF
```

Expected: status ok, hops ≥ 1, first hop seq **5269** via_src `(2,1,13)` — the exact values measured in Ground Truth.

- [ ] **Step 6: Full test files green**

```bash
python3 tools/tests/test_ooo_l3.py; echo "rc=$?"
python3 tools/tests/test_ooo_sample_runner.py; echo "rc=$?"
```

- [ ] **Step 7: Commit**

```bash
git add tools/ooo_l3.py tools/ooo_sample_runner.py tools/tests/test_ooo_l3.py
git commit -m "[OOO][FIX-RB] ooo_l3+do_l3: rat component + rename map-entry join (class/arch/new_phys seed, re-point kill, squash consumers) — real-data proven: SDC first hop seq 5269 via (2,1,13)"
git push origin ooo/l0l5-chain
```

### Task 8: Fix D — l0.limited_reason for source-less eligible_count

**Files:**
- Modify: `tools/ooo_observation.py` (l0_block_from, lines ~640-667)
- Test: `tools/tests/test_ooo_observation.py` (new checks; read the file's fixture style first)

**Interfaces:**
- Produces: `l0.limited_reason` = non-empty documentation string iff the log exists AND `eligible_count is None`; `None` otherwise. Key name matches the gate's documented escape (`ooo_chain_audit.py:162` reads `funnel_limited_reason`/`limited_reason`). The gate itself is NOT touched. `l0.limited` (existing scope note) is kept unchanged.

- [ ] **Step 1: Write the failing tests**:

```python
    print("[rb] l0 limited_reason for source-less eligible_count")
    # decode-style log: marker lines, NO CHAOS_ELIGIBLE_COUNT ->
    # limited_reason present; gate silent.
    d = os.path.join(tmp, "lrd"); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "decode_injections.log"), "w") as f:
        f.write("Tick: 416955, Site: fetch_decode, mode=imm_bitflip, "
                "pc=0x4090a0, sn=159, faults_injected: 1\n")
    blk = ooo_observation.l0_block_from(d, "decode")
    check("limited-reason-present",
          isinstance(blk.get("limited_reason"), str) and
          "CHAOS_ELIGIBLE_COUNT" in blk["limited_reason"] and
          "eligible_count" in blk["limited_reason"],
          repr(blk.get("limited_reason")))
    check("real-funnel-intact",
          blk["attempted"] == 1 and blk["eligible"] == 1 and
          blk["eligible_count"] is None,
          "attempted=%r eligible=%r ec=%r" % (blk["attempted"],
                                              blk["eligible"],
                                              blk["eligible_count"]))
    obs = {"l0": blk, "l1": {}, "l2": {}, "l3": {}}
    check("gate-silent-with-reason",
          "l0_funnel_missing" not in
          oca.semantic_gate_violations(obs),
          repr(oca.semantic_gate_violations(obs)))
    # lsq-style log WITH the self-report -> no limited_reason, no violation
    d2 = os.path.join(tmp, "lrd2"); os.makedirs(d2, exist_ok=True)
    with open(os.path.join(d2, "lsq_fwd_injections.log"), "w") as f:
        f.write("CHAOS_ELIGIBLE_COUNT= 3\n"
                "Tick: 100, Site: fwd, faults_injected: 1\n")
    blk2 = ooo_observation.l0_block_from(d2, "lsq_fwd")
    check("no-reason-when-self-reported",
          blk2.get("limited_reason") is None and
          blk2["eligible_count"] == 3,
          "ec=%r lr=%r" % (blk2["eligible_count"],
                           blk2.get("limited_reason")))
    # no-log case stays covered by status=no_log (gate's own clause)
    d3 = os.path.join(tmp, "lrd3"); os.makedirs(d3, exist_ok=True)
    blk3 = ooo_observation.l0_block_from(d3, "decode")
    check("no-log-status-unchanged", blk3["status"] == "no_log",
          repr(blk3["status"]))
```

- [ ] **Step 2: Run to verify it fails**

```bash
python3 tools/tests/test_ooo_observation.py 2>&1 | tail -6; echo "rc=$?"
```

Expected: `limited-reason-present` FAIL (key absent today).

- [ ] **Step 3: Implement** — in `l0_block_from`, inside the `if funnel["log_exists"]:` branch (after `limited = (...)`):

```python
        # Admission-gate vocabulary (ooo_chain_audit
        # .semantic_gate_violations reads funnel_limited_reason /
        # limited_reason): eligible_count is n/a whenever this log
        # carries no CHAOS_ELIGIBLE_COUNT= self-report -- decode/rat
        # injectors never write one (only CHAOSLSQFwd/CHAOSExec do, at
        # teardown; a crash before teardown also loses it). Documented
        # n/a -- attempted/eligible above stay the real per-line counts,
        # and this can never mask a null attempted (log exists =>
        # attempted is an int).
        if funnel["eligible_count"] is None:
            limited_reason = (
                "eligible_count n/a: no CHAOS_ELIGIBLE_COUNT= self-report "
                "in this injector log (only CHAOSLSQFwd/CHAOSExec write "
                "one, at teardown; decode/rat injectors never do, and a "
                "crash before teardown loses it). attempted=%d / "
                "eligible=%d are the real per-line logged counts "
                "(injection events + honest skips / injection events)."
                % (funnel["attempted"], funnel["eligible"]))
        else:
            limited_reason = None
```

and add `limited_reason=limited_reason,` to the returned dict. The `else` (no_log) branch returns `limited_reason=None` implicitly (add the key explicitly for schema stability).

- [ ] **Step 4: Verify + regression**

```bash
python3 tools/tests/test_ooo_observation.py; echo "rc=$?"
python3 tools/tests/test_ooo_chain_audit.py; echo "rc=$?"
python3 tools/tests/test_faults_log_contract.py; echo "rc=$?"
```

- [ ] **Step 5: Commit**

```bash
git add tools/ooo_observation.py tools/tests/test_ooo_observation.py
git commit -m "[OOO][FIX-RB] l0: emit gate-recognized limited_reason when eligible_count has no source (decode/rat logs never carry CHAOS_ELIGIBLE_COUNT) — documented n/a, gate untouched"
git push origin ooo/l0l5-chain
```

### Task 9: Fix E — E2E contract: real L3 chain expectations

**Files:**
- Modify: `tools/tests/e2e/ooo_l0l5_e2e.py` (assert_masked ~line 236-259; assert_sdc ~line 276-296; self-test fixtures `_obs_min` + masked/sdc sections)

**Interfaces:**
- Produces (assert_masked, post-FIX-B decode contract): `l3.status=="ok"`, `l3.method=="source_read"`, `l3.source_row is not None` with `source_row.seqencNum == l0.events[0].sn` (the join proof), `chain_complete is True`, `chain_gaps == []`. Hops may be `[]` when `first_divergent_commit.seq == source_row.seq` (window honestly ends at the source row — the masked fixture is exactly this: sn=159 commits at seq 103 = fdc).
- Produces (assert_sdc, rat contract — added to the existing checks): `l3.status=="ok"`, `method=="source_read"`, `len(l3.hops) >= 1`, `l3.hops[0].via_src == {"class": l0ev.class_id, "arch": l0ev.arch_id, "phys": l0ev.new_phys}` — read the L0 event fields from the observation (not hardcoded), mapping `"vec"->2`/`"int"->0` and `"V<n>"/"X<n>"->n` locally; `chain_complete is True`; `chain_gaps == []`.

- [ ] **Step 1: Update assert_masked** — replace the unsupported-expectation block:

```python
    l3 = obs.get("l3", {})
    if l3.get("status") != "ok" or l3.get("method") != "source_read":
        f.append("decode l3 must be the REAL source_read chain "
                 "(status=%r method=%r)" % (l3.get("status"),
                                            l3.get("method")))
    src_row = l3.get("source_row")
    sn0 = (l0.get("events") or [{}])[0].get("sn")
    if not (isinstance(src_row, dict) and
            src_row.get("seqencNum") == sn0):
        f.append("masked l3.source_row must join the L0 sn "
                 "(source_row=%r sn=%r)" % (src_row, sn0))
    if obs.get("chain_complete") is not True:
        f.append("chain_complete must be true (real chain; "
                 "hops may be empty when fdc==source seq)")
    if obs.get("chain_gaps") != []:
        f.append("chain_gaps must be [] (%r)" % obs.get("chain_gaps"))
```

- [ ] **Step 2: Extend assert_sdc** (keep all existing checks; add):

```python
    l3 = obs.get("l3", {})
    if l3.get("status") != "ok" or l3.get("method") != "source_read":
        f.append("rat l3 must be the REAL source_read chain "
                 "(status=%r method=%r)" % (l3.get("status"),
                                            l3.get("method")))
    elif not l3.get("hops"):
        f.append("sdc rat sample must carry >=1 real L3 hop "
                 "(first corrupted read observed in trace)")
    else:
        ev0 = (l0.get("events") or [{}])[0]
        cls = {"vec": 2, "int": 0}.get(str(ev0.get("class", "")).lower())
        am = re.match(r"^[VX](\d+)$", str(ev0.get("arch", "")))
        via = l3["hops"][0].get("via_src") or {}
        if not (cls is not None and am and
                via.get("class") == cls and via.get("arch") == int(am.group(1))
                and via.get("phys") == ev0.get("new_phys")):
            f.append("sdc first hop via_src must equal the corrupted "
                     "L0 mapping (via=%r class=%r arch=%r new_phys=%r)"
                     % (via, ev0.get("class"), ev0.get("arch"),
                        ev0.get("new_phys")))
    if obs.get("chain_complete") is not True:
        f.append("sdc chain_complete must be true (real chain)")
    if obs.get("chain_gaps") != []:
        f.append("sdc chain_gaps must be [] (%r)" % obs.get("chain_gaps"))
```

(`import re` is already at the top of the file — verify; add if not.)

- [ ] **Step 3: Update self-test fixtures** — `_obs_min` default `l3` stays `{"status": "unsupported"}` (used by negative tests); update the positive fixtures:
  - `masked-pass`: `l3={"status": "ok", "method": "source_read", "source_row": {"seqencNum": 159, "seq": 103}, "hops": []}`, `chain_complete=True`, `chain_gaps=[]`, and `l0` must include `events: [{"tick": 1, "sn": 159}]` (the default `_obs_min` l0 events `[{"tick": 1}]` need `sn`).
  - `masked-negative-l3` becomes: `l3={"status": "unsupported"}` (pre-FIX-B shape) must FAIL.
  - sdc positive fixture: add the ok/source_read l3 with one hop `via_src {"class":2,"arch":1,"phys":13}` + l0 event `{"tick": 9933770, "class": "vec", "arch": "V1", "old_phys": 1, "new_phys": 13, "faults_injected": 1}` + `chain_complete=True, chain_gaps=[]`; negative: wrong phys in via_src must FAIL.

- [ ] **Step 4: Run the self-test to green**

```bash
python3 tools/tests/e2e/ooo_l0l5_e2e.py --self-test; echo "rc=$?"
```

Expected: all checks PASS (the count grows from 29; every old check that encoded the stale contract is updated, none deleted silently — the negative variants keep the old shapes as FAIL cases).

- [ ] **Step 5: Commit**

```bash
git add tools/tests/e2e/ooo_l0l5_e2e.py
git commit -m "[OOO][FIX-RB] e2e contract: masked asserts the real decode chain (sn join, source_row, chain_complete), sdc asserts the rat map-join (>=1 hop, via_src==corrupted L0 mapping)"
git push origin ooo/l0l5-chain
```

### Task 10: Full battery re-run (all suites green post-fix)

- [ ] **Step 1: Run everything from Task 2 Step 1 again.** Expected: every rc=0. If any suite fails, fix within the owning task's scope and re-run — do NOT relax assertions.

### Task 11: Real E2E run → PASS + step-5 sample validation

**Files:** evidence only under `runs/ooo-l0l5/e2e.v4-fixB-readmission/`.

- [ ] **Step 1: Run the E2E** (fresh dir; ~7 min):

```bash
OOO_E2E_ROOT=/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e.v4-fixB-readmission \
  python3 tools/tests/e2e/ooo_l0l5_e2e.py 2>&1 | tee /tmp/rb_e2e_final.log; echo "rc=$?"
```

Expected: `OVERALL: PASS` — normal Inactive chain_complete=true; masked REAL chain (sn join, fdc==source seq → hops possibly [], chain_complete=true); crash honest (l3 not_observed_before_crash, zero-byte trace, no fake seq=0 divergence); sdc rat chain (hop seq 5269-class, via (2,1,13), fdc 5798 window); 4/4 replay determinism match.

- [ ] **Step 2: Scripted step-5 checklist** (user step 5, quote real values):

```bash
python3 - <<'EOF'
import json, glob
root = "/home/sdc/gem5-fi-ding/runs/ooo-l0l5/e2e.v4-fixB-readmission"
res = json.load(open(root + "/e2e_result.json"))
print("OVERALL:", res["overall"])
for cls in ("normal", "masked", "crash", "sdc"):
    sd = res[cls]["sample_dir"]
    obs = json.load(open(sd + "/observation.json"))
    l0, l2, l3 = obs["l0"], obs["l2"], obs["l3"]
    print("[%s] %s" % (cls, res[cls]["status"]))
    print("  L0 attempted=%r eligible=%r eligible_count=%r activated=%r"
          % (l0.get("attempted"), l0.get("eligible"),
             l0.get("eligible_count"), l0.get("activated")))
    print("  L0 limited_reason: %s" % bool(l0.get("limited_reason")))
    print("  L1=%r L2=%r L4=%r L5=%r" % (obs["l1"].get("status"),
          l2.get("status"), obs["l4"].get("status"),
          obs["l5"].get("classification")))
    print("  L3 status=%r method=%r hops=%d" % (l3.get("status"),
          l3.get("method"), len(l3.get("hops") or [])))
    fd = (l2.get("commit_diff") or {}).get("first_divergence")
    print("  first_divergence seq=%r run_instructions=%r"
          % (fd and fd.get("seq"),
             (l2.get("commit_diff") or {}).get("run_instructions")))
    print("  chain_complete=%r gaps=%r" % (obs.get("chain_complete"),
                                           obs.get("chain_gaps")))
    assert not (fd and fd.get("seq") == 0), "fake seq=0 divergence!"
act = [c for c in ("masked", "sdc")
       if json.load(open(res[c]["sample_dir"] + "/observation.json"))
       ["chain_complete"] is True]
print("activated+chain_complete=true classes:", act)
assert act, "need >=1 real activated chain_complete=true sample"
print("STEP-5 CHECKLIST: PASS")
EOF
```

Expected (the honest contract): masked/crash/sdc L0 attempted=1 eligible=1 (eligible_count=None + limited_reason=True); crash L1=no_snapshots_before_crash L2/L3=not_observed_before_crash; masked/sdc L3 ok/source_read; no `first_divergence.seq==0`; ≥1 activated chain_complete=true (masked AND sdc expected).

### Task 12: eng3 specs + n=2 engineering runs (4 RunIDs)

**Files:**
- Create (runs/, untracked): `runs/ooo-l0l5/specs/eng3_{D01-F0-W6-c,D02-F0-W6-b,D02-F0-W6-c,D04-F0-W4-d}.yaml`

**Interfaces:**
- Consumes: `runs/ooo-l0l5/specs/eng2_<same>.yaml` as templates; `tools/ooo_sample_runner.py` CLI `run --campaign-yaml Y --rep N --runs-root R` then `replay --sample-dir D`.
- Produces: `runs/eng3_<RunID>/{results.jsonl, samples/eng3_<RunID>-c0000-r000{0,1}/}` — 8 samples + 8 replays.

- [ ] **Step 1: Generate eng3 specs** (from eng2 specs: campaign_id/runid_row prefix eng3_, add `trace.ctrace_v2: true`, substitute `__FREEZE_COMMIT__` with the Task-10-final commit SHA `$CS` where `$CS=$(git rev-parse HEAD)`; base_seed 52001000 unchanged — same geometries as eng2, now with v2 traces):

```bash
CS=$(git rev-parse HEAD) && echo "freeze commit: $CS"
for r in D01-F0-W6-c D02-F0-W6-b D02-F0-W6-c D04-F0-W4-d; do
  python3 - "$r" "$CS" <<'EOF'
import re, sys
r, cs = sys.argv[1], sys.argv[2]
src = open("/home/sdc/gem5-fi-ding/runs/ooo-l0l5/specs/eng2_%s.yaml" % r)
txt = src.read().replace("eng2_", "eng3_")
txt = txt.replace("__FREEZE_COMMIT__", cs)
txt = txt.replace("msnap_every: 1000", "msnap_every: 1000\n  ctrace_v2: true")
open("/home/sdc/gem5-fi-ding/runs/ooo-l0l5/specs/eng3_%s.yaml" % r, "w").write(txt)
print("wrote eng3_%s.yaml (chaos_commit=%s, ctrace_v2=true)" % (r, cs))
EOF
done
grep -c "ctrace_v2: true" /home/sdc/gem5-fi-ding/runs/ooo-l0l5/specs/eng3_*.yaml   # 4 files, 1 each
```

- [ ] **Step 2: Run 4 campaigns × n=2 (+100% replay), ≤4 concurrent gem5** (reuses the frozen goldens keyed by the new binary sha; first use builds them — smoke/coremark/depchain goldens already exist under runs/ooo-l0l5/goldens from the E2E/eng2 era only if sha-keyed — verify the runner finds or builds them):

```bash
cd /home/sdc/gem5-fi-ding/.claude/worktrees/ooo-l0l5
for r in D01-F0-W6-c D02-F0-W6-b D02-F0-W6-c D04-F0-W4-d; do
  for rep in 0 1; do
    python3 tools/ooo_sample_runner.py run \
      --campaign-yaml /home/sdc/gem5-fi-ding/runs/ooo-l0l5/specs/eng3_$r.yaml \
      --rep $rep --runs-root /home/sdc/gem5-fi-ding/runs \
      >>/tmp/rb_eng3_$r.log 2>&1
  done &
done; wait
tail -3 /tmp/rb_eng3_*.log
```

Expected: 8 × `COMPLETE` lines; classifications match the eng2 geometries (7 Masked + 1 Hang expected — D01-c r0000 Hang, r0001 Masked; others Masked; ANY deviation is recorded honestly and investigated before admission, never massaged).

- [ ] **Step 3: Replays** — the runner's replay_pct=100 runs them automatically (verify each sample dir has `evidence/replay/` and observation `replay.determinism == "match"`); if the runner does not auto-replay, run `python3 tools/ooo_sample_runner.py replay --sample-dir <dir>` per sample.

### Task 13: Admission gate over the eng3 samples

- [ ] **Step 1: Run the 7-item admission** (identity/conservation/traces/no-overwrite/replay/observation/chain):

```bash
python3 tools/tests/e2e/ooo_l0l5_admission.py \
  --eng2-dirs /home/sdc/gem5-fi-ding/runs/eng3_D01-F0-W6-c \
              /home/sdc/gem5-fi-ding/runs/eng3_D02-F0-W6-b \
              /home/sdc/gem5-fi-ding/runs/eng3_D02-F0-W6-c \
              /home/sdc/gem5-fi-ding/runs/eng3_D04-F0-W4-d \
  --goldens-dir /home/sdc/gem5-fi-ding/runs/ooo-l0l5/goldens \
  --frozen-gem5-sha beb5d6b7a254049c5388734abd5889f362d72caf93e24cfe2ccfae7a2a39e6a4 \
  --frozen-chaos-commit $(git rev-parse HEAD) \
  --out /home/sdc/gem5-fi-ding/runs/ooo-l0l5/admission/admission_checks_eng3.json \
  --expect-samples 8; echo "rc=$?"
```

Expected: rc=0, `OVERALL: PASS`, 8/8 samples × 7 items. (Check the `--goldens-dir` value against what Task 12 actually used — follow the runner's golden path; `--guard-dir` default if required by the script — read its `--help` first.)

- [ ] **Step 2: If any item FAILs** — user step 11: locate, fix (new task in this plan's style, own commit), re-run Task 10→13. Never lower a gate; never substitute execution_complete for chain_complete.

### Task 14: admission_handoff_eng3.json + tallies

**Files:**
- Create (runs/, untracked): `/home/sdc/gem5-fi-ding/runs/ooo-l0l5/admission/admission_handoff_eng3.json`
- Create (runs/, untracked): `/home/sdc/gem5-fi-ding/runs/ooo-l0l5/admission/eng3_tallies.json` (machine-generated counts the handoff quotes)

- [ ] **Step 1: Generate the tallies** (all 8 eng3 samples + the 4 E2E final samples):

```bash
python3 - <<'EOF'
import json, glob, collections
tally = collections.Counter()
rows = []
for sd in sorted(glob.glob("/home/sdc/gem5-fi-ding/runs/eng3_*/samples/*")):
    obs = json.load(open(sd + "/observation.json"))
    l3 = obs.get("l3") or {}
    rows.append(dict(sample=sd.split("/")[-1],
                     classification=obs["l5"]["classification"],
                     activated=obs["l0"]["activated"],
                     attempted=obs["l0"]["attempted"],
                     eligible=obs["l0"]["eligible"],
                     chain_complete=obs["chain_complete"],
                     l3_status=l3.get("status"),
                     l3_method=l3.get("method"),
                     n_hops=len(l3.get("hops") or []),
                     replay=(obs.get("l2", {}).get("replay") or
                             obs.get("replay") or {}).get("determinism")))
    tally["l3_method:" + str(l3.get("method"))] += 1
    tally["l3_status:" + str(l3.get("status"))] += 1
    tally["chain_complete:" + str(obs["chain_complete"])] += 1
out = dict(rows=rows, tallies=dict(tally),
           n_activated=sum(r["activated"] or 0 for r in rows),
           n_chain_complete=sum(1 for r in rows if r["chain_complete"]))
json.dump(out, open("/home/sdc/gem5-fi-ding/runs/ooo-l0l5/admission/"
                    "eng3_tallies.json", "w"), indent=1)
print(json.dumps(out["tallies"], indent=1))
print("activated total:", out["n_activated"],
      "| chain_complete:", out["n_chain_complete"])
EOF
```

- [ ] **Step 2: Assemble the handoff** (schema `ooo-admission-handoff/v1`, following `runs/ooo-l0l5/admission/admission_handoff.json` structure; REQUIRED fields per user step 7):

```json
{
  "schema_version": "ooo-admission-handoff/v1",
  "generated_at": "<now>",
  "phase": "FIX-B-READMISSION -> WAITING-CENTRAL-MERGE",
  "fails": [],
  "pending": [],
  "central_ruling_pending": ["D01-F0-W6-a/b formal-385 registered-not-backfilled + Excel frozen (F-013) — central decision, outside this admission's scope"],
  "counts": {"n_samples": 8, "activated_total": "<from tallies>", "chain_complete_total": "<from tallies>"},
  "l3_method_distribution": "<from tallies>",
  "n2_per_runid": {"eng3_D01-F0-W6-c": ["<cls r0>", "<cls r1>"], "...": "..."},
  "frozen": {"branch": "ooo/l0l5-chain", "merge_ready_commit": "<git rev-parse HEAD>",
             "gem5_opt_sha256": "beb5d6b7a254049c5388734abd5889f362d72caf93e24cfe2ccfae7a2a39e6a4",
             "base": "8cd46c1 (FIX-INT lead integration)"},
  "barriers": {"A_unit_tests": {"status": "<PASS>", "evidence": "<suite list + rc>"},
               "B_e2e_four_class": {"status": "<PASS>", "evidence": "runs/ooo-l0l5/e2e.v4-fixB-readmission/e2e_result.json OVERALL=PASS (pre-fix FAIL baseline: e2e.v4a-fixB-pre)"},
               "C_eng3_n2": {"status": "<PASS>", "evidence": "runs/ooo-l0l5/admission/admission_checks_eng3.json (7 items x 8 samples)"},
               "D_real_chain_hard_req": {"status": "<PASS>", "evidence": "activated>0 AND chain_complete=true samples: <n> (masked decode sn-join + sdc rat map-join)"},
               "E_no_fake_divergence": {"status": "<PASS>", "evidence": "zero seq=0 first_divergence; crash = not_observed_before_crash/truncated_empty"},
               "F_l0_real_funnel": {"status": "<PASS>", "evidence": "attempted/eligible real per-line counts; eligible_count n/a documented via limited_reason"}},
  "evidence_paths": ["runs/ooo-l0l5/e2e.v4-fixB-readmission/", "runs/ooo-l0l5/e2e.v4a-fixB-pre/", "runs/eng3_D01-F0-W6-c/", "runs/eng3_D02-F0-W6-b/", "runs/eng3_D02-F0-W6-c/", "runs/eng3_D04-F0-W4-d/", "runs/ooo-l0l5/admission/admission_checks_eng3.json", "runs/ooo-l0l5/admission/eng3_tallies.json"]
}
```

Every value filled from REAL command output — no placeholders survive into the written file.

- [ ] **Step 3: Verdict rule** (user step 8): PASS iff `fails == []` and `pending == []` and admission checks PASS and ≥1 activated chain_complete=true sample. Otherwise the verdict is FAIL and Task 13 Step 2 applies.

### Task 15: Push, report, stop at waiting-for-central-merge

- [ ] **Step 1: Confirm clean tree + push**

```bash
git status --porcelain        # empty
git log --oneline 8cd46c1..HEAD
git push origin ooo/l0l5-chain
```

- [ ] **Step 2: Write the brief report** (chat, not Excel): merge-ready commit SHA, gem5 SHA, fails/pending counts, activated/chain_complete counts, L3 method distribution, per-RunID n=2 outcomes, evidence paths, the D01-a/b central-ruling note, and the explicit statement that formal-385 scheduling (6→8 slots) resumes ONLY after central merge + fi-ding binary freeze. Then STOP — no merge, no Excel, no formal launches.

## Self-Review

- Spec coverage: user steps 1-2 → Task 2; step 3 → Task 2 Step 2; step 4 → Tasks 3-4, 11; step 5 → Task 11 Step 2 (+ Tasks 5-9 owning each requirement); step 6 → Tasks 12-13; step 7 → Task 14; step 8 → Task 14 Step 3; step 9 → Task 15 constraints (no formal/Excel/merge — Global Constraints); step 10 → Task 15; step 11 → Task 13 Step 2. Patrol-log plan (E2E 四类 → eng3 4×n=2 → hard req) → Tasks 11-14. ✓
- Placeholder scan: code blocks carry real implementations; command tasks quote expected outputs measured in Ground Truth. The `<...>` markers in Task 14's JSON skeleton are fill-from-output instructions, explicitly closed by Step 2's rule. ✓
- Type consistency: `limited_reason` key matches gate reader (ooo_chain_audit.py:162); `source_map_entry` fields match Task 7 test; `via_src` dict shape `{"class","arch","phys"}` consistent between builder and asserts; `not_observed_before_crash` consistent with l1/l2 vocabulary. ✓
- Review Focus: all five classes pinned by named tests in Tasks 5-9. ✓
